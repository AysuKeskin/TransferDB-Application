-- Run AFTER schema.sql (or schema_updates.sql for existing DBs)
-- mysql -u root -p DB < sql/triggers.sql

USE DB;

-- ================================================================
-- Drop existing triggers/procedures so this file is idempotent
-- ================================================================
DROP TRIGGER IF EXISTS trg_check_match_conflict;
DROP TRIGGER IF EXISTS trg_check_match_future;
DROP TRIGGER IF EXISTS trg_check_match_result_attendance;
DROP TRIGGER IF EXISTS trg_check_starter_limit;
DROP TRIGGER IF EXISTS trg_check_squad_max;
DROP TRIGGER IF EXISTS trg_check_player_active_contract;
DROP TRIGGER IF EXISTS trg_check_loan_restriction;
DROP TRIGGER IF EXISTS trg_check_contract_max_active;
DROP TRIGGER IF EXISTS trg_check_no_duplicate_perm;
DROP TRIGGER IF EXISTS trg_check_no_duplicate_loan;
DROP TRIGGER IF EXISTS trg_auto_terminate_old_perm;
DROP TRIGGER IF EXISTS trg_check_loan_requires_permanent;
DROP TRIGGER IF EXISTS trg_check_competition_unique;
DROP TRIGGER IF EXISTS trg_check_player_disjoint;
DROP TRIGGER IF EXISTS trg_check_manager_disjoint;
DROP TRIGGER IF EXISTS trg_check_referee_disjoint;
DROP TRIGGER IF EXISTS trg_check_contract_disjoint_perm;
DROP TRIGGER IF EXISTS trg_check_contract_disjoint_loan;
DROP TRIGGER IF EXISTS trg_check_yellow_red_card;
DROP TRIGGER IF EXISTS trg_check_yellow_red_card_update;

DELIMITER //

-- ================================================================
-- 1. Match scheduling: no 120-minute overlap for stadium/referee/clubs
-- ================================================================
CREATE TRIGGER trg_check_match_conflict
BEFORE INSERT ON `Match`
FOR EACH ROW
BEGIN
    DECLARE conflict_count INT DEFAULT 0;

    SELECT COUNT(*) INTO conflict_count
    FROM `Match`
    WHERE ABS(TIMESTAMPDIFF(MINUTE, match_datetime, NEW.match_datetime)) < 120
      AND (
            stadium_id    = NEW.stadium_id
         OR referee_id    = NEW.referee_id
         OR home_club_id  IN (NEW.home_club_id, NEW.away_club_id)
         OR away_club_id  IN (NEW.home_club_id, NEW.away_club_id)
      );

    IF conflict_count > 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Match conflicts with an existing match within 120 minutes (stadium, referee, or club overlap).';
    END IF;
END//

-- ================================================================
-- 1b. Match scheduling: must be in the future
-- ================================================================
CREATE TRIGGER trg_check_match_future
BEFORE INSERT ON `Match`
FOR EACH ROW
BEGIN
    IF NEW.match_datetime <= NOW() THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Match must be scheduled for a future date and time.';
    END IF;
END//

-- ================================================================
-- 2. Match result: attendance must not exceed stadium capacity
-- ================================================================
CREATE TRIGGER trg_check_match_result_attendance
BEFORE UPDATE ON `Match`
FOR EACH ROW
BEGIN
    DECLARE cap INT DEFAULT 0;

    IF NEW.attendance IS NOT NULL THEN
        SELECT capacity INTO cap
        FROM Stadium
        WHERE stadium_id = NEW.stadium_id;

        IF NEW.attendance > cap THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Attendance exceeds stadium capacity.';
        END IF;
    END IF;
END//

-- ================================================================
-- 3. Match Participation: max 11 starters per club per match
-- ================================================================
CREATE TRIGGER trg_check_starter_limit
BEFORE INSERT ON Match_Participation
FOR EACH ROW
BEGIN
    DECLARE starter_count INT DEFAULT 0;

    IF NEW.is_starter = TRUE THEN
        SELECT COUNT(*) INTO starter_count
        FROM Match_Participation
        WHERE match_id = NEW.match_id
          AND club_id  = NEW.club_id
          AND is_starter = TRUE;

        IF starter_count >= 11 THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Cannot have more than 11 starters per club per match.';
        END IF;
    END IF;
END//

-- ================================================================
-- 4. Match Participation: max 23 squad members per club per match
-- ================================================================
CREATE TRIGGER trg_check_squad_max
BEFORE INSERT ON Match_Participation
FOR EACH ROW
BEGIN
    DECLARE squad_count INT DEFAULT 0;

    SELECT COUNT(*) INTO squad_count
    FROM Match_Participation
    WHERE match_id = NEW.match_id
      AND club_id  = NEW.club_id;

    IF squad_count >= 23 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Squad cannot exceed 23 players per club per match.';
    END IF;
END//

-- ================================================================
-- 5. Match Participation: player must have active contract with club
-- ================================================================
CREATE TRIGGER trg_check_player_active_contract
BEFORE INSERT ON Match_Participation
FOR EACH ROW
BEGIN
    DECLARE contract_count INT DEFAULT 0;
    DECLARE match_date     DATE;

    SELECT DATE(match_datetime) INTO match_date
    FROM `Match`
    WHERE match_id = NEW.match_id;

    SELECT COUNT(*) INTO contract_count
    FROM Contract
    WHERE player_id  = NEW.player_id
      AND club_id    = NEW.club_id
      AND start_date <= match_date
      AND end_date   >= match_date;

    IF contract_count = 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Player does not have an active contract with this club on the match date.';
    END IF;
END//

-- ================================================================
-- 6. Match Participation: player on loan cannot play for parent club
-- ================================================================
CREATE TRIGGER trg_check_loan_restriction
BEFORE INSERT ON Match_Participation
FOR EACH ROW
BEGIN
    DECLARE loan_count INT DEFAULT 0;
    DECLARE perm_count INT DEFAULT 0;
    DECLARE match_date DATE;

    SELECT DATE(match_datetime) INTO match_date
    FROM `Match`
    WHERE match_id = NEW.match_id;

    -- Does the player have an active loan with a DIFFERENT club?
    SELECT COUNT(*) INTO loan_count
    FROM Contract c
    JOIN Loan_Contract lc ON lc.contract_id = c.contract_id
    WHERE c.player_id  = NEW.player_id
      AND c.club_id   != NEW.club_id
      AND c.start_date <= match_date
      AND c.end_date   >= match_date;

    IF loan_count > 0 THEN
        -- Is the club they're trying to play for their permanent club?
        SELECT COUNT(*) INTO perm_count
        FROM Contract c
        JOIN Permanent_Contract pc ON pc.contract_id = c.contract_id
        WHERE c.player_id  = NEW.player_id
          AND c.club_id    = NEW.club_id
          AND c.start_date <= match_date
          AND c.end_date   >= match_date;

        IF perm_count > 0 THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Player currently on loan cannot participate for their parent club.';
        END IF;
    END IF;
END//

-- ================================================================
-- 7. Contract: max 2 active contracts (1 permanent + 1 loan)
-- ================================================================
CREATE TRIGGER trg_check_contract_max_active
BEFORE INSERT ON Contract
FOR EACH ROW
BEGIN
    DECLARE active_count INT DEFAULT 0;

    SELECT COUNT(*) INTO active_count
    FROM Contract
    WHERE player_id = NEW.player_id
      AND start_date <= NEW.start_date
      AND end_date   >= NEW.start_date;

    IF active_count >= 2 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Player already has the maximum number of active contracts (2).';
    END IF;
END//

-- ================================================================
-- 7b. Permanent Contract: prevent two simultaneous permanent contracts
-- ================================================================
CREATE TRIGGER trg_check_no_duplicate_perm
BEFORE INSERT ON Permanent_Contract
FOR EACH ROW
BEGIN
    DECLARE perm_count INT DEFAULT 0;
    DECLARE new_player INT;
    DECLARE new_start  DATE;

    SELECT player_id, start_date INTO new_player, new_start
    FROM Contract WHERE contract_id = NEW.contract_id;

    SELECT COUNT(*) INTO perm_count
    FROM Contract c
    JOIN Permanent_Contract pc ON pc.contract_id = c.contract_id
    WHERE c.player_id = new_player
      AND c.start_date <= new_start
      AND c.end_date   >= new_start;

    IF perm_count > 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Player already has an active permanent contract. Terminate it before creating a new one.';
    END IF;
END//

-- ================================================================
-- 7c. Loan Contract: prevent two simultaneous loan contracts
-- ================================================================
CREATE TRIGGER trg_check_no_duplicate_loan
BEFORE INSERT ON Loan_Contract
FOR EACH ROW
BEGIN
    DECLARE loan_count INT DEFAULT 0;
    DECLARE new_player INT;
    DECLARE new_start  DATE;

    SELECT player_id, start_date INTO new_player, new_start
    FROM Contract WHERE contract_id = NEW.contract_id;

    SELECT COUNT(*) INTO loan_count
    FROM Contract c
    JOIN Loan_Contract lc ON lc.contract_id = c.contract_id
    WHERE c.player_id = new_player
      AND c.start_date <= new_start
      AND c.end_date   >= new_start;

    IF loan_count > 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Player already has an active loan contract.';
    END IF;
END//

-- ================================================================
-- 8. Loan contract: player must have active permanent contract elsewhere
-- ================================================================
CREATE TRIGGER trg_check_loan_requires_permanent
BEFORE INSERT ON Loan_Contract
FOR EACH ROW
BEGIN
    DECLARE perm_count INT DEFAULT 0;
    DECLARE contract_start DATE;
    DECLARE contract_club INT;

    -- Get contract details
    SELECT start_date, club_id INTO contract_start, contract_club
    FROM Contract
    WHERE contract_id = NEW.contract_id;

    -- Check for active permanent contract with a DIFFERENT club
    SELECT COUNT(*) INTO perm_count
    FROM Contract c
    JOIN Permanent_Contract pc ON pc.contract_id = c.contract_id
    WHERE c.player_id = (SELECT player_id FROM Contract WHERE contract_id = NEW.contract_id)
      AND c.club_id != contract_club
      AND c.start_date <= contract_start
      AND c.end_date   >= contract_start;

    IF perm_count = 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Cannot create a loan contract without an active permanent contract at another club.';
    END IF;
END//

-- ================================================================
-- 9. Competition: unique (name, season) — backup trigger
--    (also enforced by UNIQUE constraint in schema)
-- ================================================================
CREATE TRIGGER trg_check_competition_unique
BEFORE INSERT ON Competition
FOR EACH ROW
BEGIN
    DECLARE dup_count INT DEFAULT 0;

    SELECT COUNT(*) INTO dup_count
    FROM Competition
    WHERE name = NEW.name AND season = NEW.season;

    IF dup_count > 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'A competition with this name and season already exists.';
    END IF;
END//

-- ================================================================
-- 10. ISA Disjointness: Player cannot also be Manager or Referee
-- ================================================================
CREATE TRIGGER trg_check_player_disjoint
BEFORE INSERT ON Player
FOR EACH ROW
BEGIN
    DECLARE cnt INT DEFAULT 0;

    SELECT COUNT(*) INTO cnt
    FROM Manager WHERE person_id = NEW.person_id;
    IF cnt > 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'This person is already registered as a Manager and cannot also be a Player.';
    END IF;

    SELECT COUNT(*) INTO cnt
    FROM Referee WHERE person_id = NEW.person_id;
    IF cnt > 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'This person is already registered as a Referee and cannot also be a Player.';
    END IF;
END//

-- ================================================================
-- 10b. ISA Disjointness: Manager cannot also be Player or Referee
-- ================================================================
CREATE TRIGGER trg_check_manager_disjoint
BEFORE INSERT ON Manager
FOR EACH ROW
BEGIN
    DECLARE cnt INT DEFAULT 0;

    SELECT COUNT(*) INTO cnt
    FROM Player WHERE person_id = NEW.person_id;
    IF cnt > 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'This person is already registered as a Player and cannot also be a Manager.';
    END IF;

    SELECT COUNT(*) INTO cnt
    FROM Referee WHERE person_id = NEW.person_id;
    IF cnt > 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'This person is already registered as a Referee and cannot also be a Manager.';
    END IF;
END//

-- ================================================================
-- 10c. ISA Disjointness: Referee cannot also be Player or Manager
-- ================================================================
CREATE TRIGGER trg_check_referee_disjoint
BEFORE INSERT ON Referee
FOR EACH ROW
BEGIN
    DECLARE cnt INT DEFAULT 0;

    SELECT COUNT(*) INTO cnt
    FROM Player WHERE person_id = NEW.person_id;
    IF cnt > 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'This person is already registered as a Player and cannot also be a Referee.';
    END IF;

    SELECT COUNT(*) INTO cnt
    FROM Manager WHERE person_id = NEW.person_id;
    IF cnt > 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'This person is already registered as a Manager and cannot also be a Referee.';
    END IF;
END//

-- ================================================================
-- 11. ISA Disjointness: Contract cannot be both Permanent and Loan
-- ================================================================
CREATE TRIGGER trg_check_contract_disjoint_perm
BEFORE INSERT ON Permanent_Contract
FOR EACH ROW
BEGIN
    DECLARE cnt INT DEFAULT 0;

    SELECT COUNT(*) INTO cnt
    FROM Loan_Contract WHERE contract_id = NEW.contract_id;
    IF cnt > 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'This contract is already a Loan Contract and cannot also be a Permanent Contract.';
    END IF;
END//

CREATE TRIGGER trg_check_contract_disjoint_loan
BEFORE INSERT ON Loan_Contract
FOR EACH ROW
BEGIN
    DECLARE cnt INT DEFAULT 0;

    SELECT COUNT(*) INTO cnt
    FROM Permanent_Contract WHERE contract_id = NEW.contract_id;
    IF cnt > 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'This contract is already a Permanent Contract and cannot also be a Loan Contract.';
    END IF;
END//

-- ================================================================
-- 12. Two yellow cards automatically imply a red card
-- ================================================================
CREATE TRIGGER trg_check_yellow_red_card
BEFORE INSERT ON Match_Participation
FOR EACH ROW
BEGIN
    IF NEW.yellow_cards >= 2 AND NEW.red_cards = 0 THEN
        SET NEW.red_cards = 1;
    END IF;
END//

CREATE TRIGGER trg_check_yellow_red_card_update
BEFORE UPDATE ON Match_Participation
FOR EACH ROW
BEGIN
    IF NEW.yellow_cards >= 2 AND NEW.red_cards = 0 THEN
        SET NEW.red_cards = 1;
    END IF;
END//

DELIMITER ;
