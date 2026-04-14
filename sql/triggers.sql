-- Run AFTER schema.sql (or schema_updates.sql for existing DBs)
-- mysql -u root -p DB < sql/triggers.sql
--
-- MySQL allows only ONE trigger per (timing, event, table) combination.
-- All checks for the same combination are merged into a single trigger.

USE DB;

-- ================================================================
-- Drop all triggers so this file is idempotent
-- ================================================================
DROP TRIGGER IF EXISTS trg_match_before_insert;
DROP TRIGGER IF EXISTS trg_match_before_update;
DROP TRIGGER IF EXISTS trg_participation_before_insert;
DROP TRIGGER IF EXISTS trg_participation_before_update;
DROP TRIGGER IF EXISTS trg_contract_before_insert;
DROP TRIGGER IF EXISTS trg_permanent_contract_before_insert;
DROP TRIGGER IF EXISTS trg_loan_contract_before_insert;
DROP TRIGGER IF EXISTS trg_competition_before_insert;
DROP TRIGGER IF EXISTS trg_player_before_insert;
DROP TRIGGER IF EXISTS trg_manager_before_insert;
DROP TRIGGER IF EXISTS trg_referee_before_insert;
DROP TRIGGER IF EXISTS trg_transfer_before_insert;
DROP TRIGGER IF EXISTS trg_transfer_after_insert;

-- also drop old individual trigger names (cleanup)
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
DROP TRIGGER IF EXISTS trg_check_loan_requires_permanent;
DROP TRIGGER IF EXISTS trg_check_competition_unique;
DROP TRIGGER IF EXISTS trg_check_player_disjoint;
DROP TRIGGER IF EXISTS trg_check_manager_disjoint;
DROP TRIGGER IF EXISTS trg_check_referee_disjoint;
DROP TRIGGER IF EXISTS trg_check_contract_disjoint_perm;
DROP TRIGGER IF EXISTS trg_check_contract_disjoint_loan;
DROP TRIGGER IF EXISTS trg_check_yellow_red_card;
DROP TRIGGER IF EXISTS trg_check_yellow_red_card_update;
DROP TRIGGER IF EXISTS trg_check_result_after_match;
DROP TRIGGER IF EXISTS trg_check_participation_club_in_match;
DROP TRIGGER IF EXISTS trg_check_transfer_from_club;
DROP TRIGGER IF EXISTS trg_check_no_participation_completed_match;
DROP TRIGGER IF EXISTS trg_check_market_value_on_purchase;

DELIMITER //

-- ================================================================
-- MATCH — BEFORE INSERT
--   1. No 120-minute overlap for stadium / referee / clubs
--   2. Match must be scheduled in the future
-- ================================================================
CREATE TRIGGER trg_match_before_insert
BEFORE INSERT ON `Match`
FOR EACH ROW
BEGIN
    DECLARE conflict_count INT DEFAULT 0;

    -- 1. 120-minute overlap check
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

    -- 2. Must be in the future
    IF NEW.match_datetime <= NOW() THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Match must be scheduled for a future date and time.';
    END IF;
END//

-- ================================================================
-- MATCH — BEFORE UPDATE
--   1. Attendance must not exceed stadium capacity
--   2. Results only after match time has passed
--   3. Each club must have >= 11 players in squad
-- ================================================================
CREATE TRIGGER trg_match_before_update
BEFORE UPDATE ON `Match`
FOR EACH ROW
BEGIN
    DECLARE cap INT DEFAULT 0;
    DECLARE home_squad INT DEFAULT 0;
    DECLARE away_squad INT DEFAULT 0;

    -- 0. Only the assigned referee can submit results
    IF (NEW.home_goals IS NOT NULL OR NEW.away_goals IS NOT NULL OR NEW.attendance IS NOT NULL)
       AND (OLD.home_goals IS NULL AND OLD.away_goals IS NULL AND OLD.attendance IS NULL) THEN
        IF @app_person_id IS NOT NULL AND OLD.referee_id != @app_person_id THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Only the assigned referee can submit match results.';
        END IF;
    END IF;

    -- 1. Attendance <= stadium capacity
    IF NEW.attendance IS NOT NULL THEN
        SELECT capacity INTO cap
        FROM Stadium
        WHERE stadium_id = NEW.stadium_id;

        IF NEW.attendance > cap THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Attendance exceeds stadium capacity.';
        END IF;
    END IF;

    -- The rest only fires when results are being submitted for the first time
    IF (NEW.home_goals IS NOT NULL OR NEW.away_goals IS NOT NULL OR NEW.attendance IS NOT NULL)
       AND (OLD.home_goals IS NULL AND OLD.away_goals IS NULL AND OLD.attendance IS NULL) THEN

        -- 2. Match must be in the past
        IF NEW.match_datetime > NOW() THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Cannot submit match results before the match has been played.';
        END IF;

        -- 3a. Home club >= 11 players
        SELECT COUNT(*) INTO home_squad
        FROM Match_Participation
        WHERE match_id = NEW.match_id AND club_id = NEW.home_club_id;

        IF home_squad < 11 THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Home club must have at least 11 players in the squad before submitting results.';
        END IF;

        -- 3b. Away club >= 11 players
        SELECT COUNT(*) INTO away_squad
        FROM Match_Participation
        WHERE match_id = NEW.match_id AND club_id = NEW.away_club_id;

        IF away_squad < 11 THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Away club must have at least 11 players in the squad before submitting results.';
        END IF;
    END IF;
END//

-- ================================================================
-- MATCH_PARTICIPATION — BEFORE INSERT
--   1. Cannot add players to a completed match
--   2. Club must be home or away in the match
--   3. Max 11 starters per club per match
--   4. Max 23 squad members per club per match
--   5. Player must have active contract with the club
--   6. Player on loan cannot play for parent club
--   7. Two yellow cards => automatic red card
--   8. Red card in previous club match => suspended
--   9. 5 accumulated yellow cards in competition/season => suspended
-- ================================================================
CREATE TRIGGER trg_participation_before_insert
BEFORE INSERT ON Match_Participation
FOR EACH ROW
BEGIN
    DECLARE match_completed INT DEFAULT 0;
    DECLARE valid_club INT DEFAULT 0;
    DECLARE starter_count INT DEFAULT 0;
    DECLARE squad_count INT DEFAULT 0;
    DECLARE contract_count INT DEFAULT 0;
    DECLARE match_date DATE;
    DECLARE loan_count INT DEFAULT 0;
    DECLARE perm_count INT DEFAULT 0;
    DECLARE comp_id INT DEFAULT 0;
    DECLARE prev_match_id INT DEFAULT NULL;
    DECLARE prev_red INT DEFAULT 0;
    DECLARE yellow_total INT DEFAULT 0;

    -- 1. Cannot add players to a completed match
    SELECT COUNT(*) INTO match_completed
    FROM `Match`
    WHERE match_id = NEW.match_id
      AND home_goals IS NOT NULL;

    IF match_completed > 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Cannot modify squad for a match that already has results.';
    END IF;

    -- 2. Club must be home or away in the match
    SELECT COUNT(*) INTO valid_club
    FROM `Match`
    WHERE match_id = NEW.match_id
      AND (home_club_id = NEW.club_id OR away_club_id = NEW.club_id);

    IF valid_club = 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Club is not participating in this match.';
    END IF;

    -- 3. Max 11 starters per club per match
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

    -- 4. Max 23 squad members per club per match
    SELECT COUNT(*) INTO squad_count
    FROM Match_Participation
    WHERE match_id = NEW.match_id
      AND club_id  = NEW.club_id;

    IF squad_count >= 23 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Squad cannot exceed 23 players per club per match.';
    END IF;

    -- 5. Player must have active contract with the club on match date
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

    -- 6. Player on loan cannot play for parent club
    SELECT COUNT(*) INTO loan_count
    FROM Contract c
    JOIN Loan_Contract lc ON lc.contract_id = c.contract_id
    WHERE c.player_id  = NEW.player_id
      AND c.club_id   != NEW.club_id
      AND c.start_date <= match_date
      AND c.end_date   >= match_date;

    IF loan_count > 0 THEN
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

    -- 7. Two yellow cards => automatic red card
    IF NEW.yellow_cards >= 2 AND NEW.red_cards = 0 THEN
        SET NEW.red_cards = 1;
    END IF;

    -- Fetch competition_id once for checks 8 and 9
    SELECT competition_id INTO comp_id
    FROM `Match` WHERE match_id = NEW.match_id;

    -- 8. Red card suspension: player got a red card in club's previous match in this competition
    SELECT m.match_id INTO prev_match_id
    FROM `Match` m
    WHERE m.competition_id = comp_id
      AND (m.home_club_id = NEW.club_id OR m.away_club_id = NEW.club_id)
      AND m.match_datetime < (SELECT match_datetime FROM `Match` WHERE match_id = NEW.match_id)
      AND m.home_goals IS NOT NULL
    ORDER BY m.match_datetime DESC
    LIMIT 1;

    IF prev_match_id IS NOT NULL THEN
        SELECT COUNT(*) INTO prev_red
        FROM Match_Participation
        WHERE match_id  = prev_match_id
          AND player_id = NEW.player_id
          AND red_cards > 0;

        IF prev_red > 0 THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Player is suspended: received a red card in the previous match of this competition.';
        END IF;
    END IF;

    -- 9. Yellow card accumulation: 5 yellows in same competition/season => suspended for next match
    SELECT COALESCE(SUM(mp.yellow_cards), 0) INTO yellow_total
    FROM Match_Participation mp
    JOIN `Match` m ON m.match_id = mp.match_id
    WHERE mp.player_id    = NEW.player_id
      AND m.competition_id = comp_id
      AND m.match_datetime < (SELECT match_datetime FROM `Match` WHERE match_id = NEW.match_id)
      AND m.home_goals IS NOT NULL;

    IF yellow_total >= 5 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Player is suspended: accumulated 5 yellow cards in this competition and season.';
    END IF;
END//

-- ================================================================
-- MATCH_PARTICIPATION — BEFORE UPDATE
--   1. Two yellow cards => automatic red card
-- ================================================================
CREATE TRIGGER trg_participation_before_update
BEFORE UPDATE ON Match_Participation
FOR EACH ROW
BEGIN
    IF NEW.yellow_cards >= 2 AND NEW.red_cards = 0 THEN
        SET NEW.red_cards = 1;
    END IF;
END//

-- ================================================================
-- CONTRACT — BEFORE INSERT
--   1. Force start_date = CURDATE()
--   2. Max 2 active contracts per player (1 permanent + 1 loan)
-- ================================================================
CREATE TRIGGER trg_contract_before_insert
BEFORE INSERT ON Contract
FOR EACH ROW
BEGIN
    DECLARE active_count INT DEFAULT 0;

    -- 1. Contract start date must always be the current system date
    SET NEW.start_date = CURDATE();

    -- 2. Max 2 active contracts
    SELECT COUNT(*) INTO active_count
    FROM Contract
    WHERE player_id = NEW.player_id
      AND start_date <= NEW.start_date
      AND end_date   > NEW.start_date;

    IF active_count >= 2 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Player already has the maximum number of active contracts (2).';
    END IF;
END//

-- ================================================================
-- PERMANENT_CONTRACT — BEFORE INSERT
--   1. Contract cannot also be a Loan Contract (ISA disjointness)
--   2. No two simultaneous permanent contracts
-- ================================================================
CREATE TRIGGER trg_permanent_contract_before_insert
BEFORE INSERT ON Permanent_Contract
FOR EACH ROW
BEGIN
    DECLARE cnt INT DEFAULT 0;
    DECLARE perm_count INT DEFAULT 0;
    DECLARE new_player INT;
    DECLARE new_start  DATE;

    -- 1. ISA disjointness
    SELECT COUNT(*) INTO cnt
    FROM Loan_Contract WHERE contract_id = NEW.contract_id;
    IF cnt > 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'This contract is already a Loan Contract and cannot also be a Permanent Contract.';
    END IF;

    -- 2. No duplicate active permanent
    SELECT player_id, start_date INTO new_player, new_start
    FROM Contract WHERE contract_id = NEW.contract_id;

    SELECT COUNT(*) INTO perm_count
    FROM Contract c
    JOIN Permanent_Contract pc ON pc.contract_id = c.contract_id
    WHERE c.player_id = new_player
      AND c.start_date <= new_start
      AND c.end_date   > new_start;

    IF perm_count > 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Player already has an active permanent contract. Terminate it before creating a new one.';
    END IF;
END//

-- ================================================================
-- LOAN_CONTRACT — BEFORE INSERT
--   1. Contract cannot also be a Permanent Contract (ISA disjointness)
--   2. No two simultaneous loan contracts
--   3. Player must have active permanent contract at another club
-- ================================================================
CREATE TRIGGER trg_loan_contract_before_insert
BEFORE INSERT ON Loan_Contract
FOR EACH ROW
BEGIN
    DECLARE cnt INT DEFAULT 0;
    DECLARE loan_count INT DEFAULT 0;
    DECLARE perm_count INT DEFAULT 0;
    DECLARE new_player INT;
    DECLARE new_start  DATE;
    DECLARE contract_club INT;

    -- 1. ISA disjointness
    SELECT COUNT(*) INTO cnt
    FROM Permanent_Contract WHERE contract_id = NEW.contract_id;
    IF cnt > 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'This contract is already a Permanent Contract and cannot also be a Loan Contract.';
    END IF;

    -- Get contract details
    SELECT player_id, start_date, club_id INTO new_player, new_start, contract_club
    FROM Contract WHERE contract_id = NEW.contract_id;

    -- 2. No duplicate active loan
    SELECT COUNT(*) INTO loan_count
    FROM Contract c
    JOIN Loan_Contract lc ON lc.contract_id = c.contract_id
    WHERE c.player_id = new_player
      AND c.start_date <= new_start
      AND c.end_date   > new_start;

    IF loan_count > 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Player already has an active loan contract.';
    END IF;

    -- 3. Must have active permanent contract at a DIFFERENT club
    SELECT COUNT(*) INTO perm_count
    FROM Contract c
    JOIN Permanent_Contract pc ON pc.contract_id = c.contract_id
    WHERE c.player_id = new_player
      AND c.club_id != contract_club
      AND c.start_date <= new_start
      AND c.end_date   > new_start;

    IF perm_count = 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Cannot create a loan contract without an active permanent contract at another club.';
    END IF;
END//

-- ================================================================
-- COMPETITION — BEFORE INSERT
--   1. Unique (name, season) — backup trigger for UNIQUE constraint
-- ================================================================
CREATE TRIGGER trg_competition_before_insert
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
-- PLAYER — BEFORE INSERT
--   1. ISA Disjointness: cannot also be Manager or Referee
-- ================================================================
CREATE TRIGGER trg_player_before_insert
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
-- MANAGER — BEFORE INSERT
--   1. ISA Disjointness: cannot also be Player or Referee
-- ================================================================
CREATE TRIGGER trg_manager_before_insert
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
-- REFEREE — BEFORE INSERT
--   1. ISA Disjointness: cannot also be Player or Manager
-- ================================================================
CREATE TRIGGER trg_referee_before_insert
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
-- TRANSFER_RECORD — BEFORE INSERT
--   1. Force transfer_date = CURDATE()
--   2. Player must have active contract with the source club
-- ================================================================
CREATE TRIGGER trg_transfer_before_insert
BEFORE INSERT ON Transfer_Record
FOR EACH ROW
BEGIN
    DECLARE contract_count INT DEFAULT 0;

    -- 1. Transfer date must always be the current system date
    SET NEW.transfer_date = CURDATE();

    -- 2. Player must have active contract with source club
    SELECT COUNT(*) INTO contract_count
    FROM Contract
    WHERE player_id  = NEW.player_id
      AND club_id    = NEW.from_club_id
      AND start_date <= NEW.transfer_date
      AND end_date   >= NEW.transfer_date;

    IF contract_count = 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Player does not have an active contract with the source club.';
    END IF;
END//

-- ================================================================
-- TRANSFER_RECORD — AFTER INSERT
--   1. Purchase transfer: auto-update player market value to fee
-- ================================================================
CREATE TRIGGER trg_transfer_after_insert
AFTER INSERT ON Transfer_Record
FOR EACH ROW
BEGIN
    IF NEW.transfer_type = 'Purchase' THEN
        UPDATE Player
        SET market_value = NEW.transfer_fee
        WHERE person_id = NEW.player_id;
    END IF;
END//

DELIMITER ;
