"""
Operation 5: Squad submission (Manager)

Spec requirements:
  - Only players with an active contract (Permanent or Loan) with the club can be selected.
  - Maximum 11 players can be marked as is_starter.
  - Total squad must be between 11 and 23 players.
  - A player on loan cannot participate for their parent club.

Constraints are split across two layers:
  • DB trigger  (trg_participation_before_insert): starters > 11, squad > 23,
    no active contract, loan rule, match already completed, wrong club.
  • App layer   (routes/manager.py:142): squad < 11 (minimum not enforced by trigger).

Seed data used:
  Match 7 : Royal Madrid (1, home)     vs Liverpool Reds (3, away) — future, no goals
  Match 8 : Atletico Madrid (4, home)  vs Man Blues (2, away)      — future, no goals
  Match 1 : Royal Madrid (1, home)     vs Man Blues (2, away)      — completed (goals set)
  Club 1 players with active contracts: 8–19  (12 players)
  Club 3 players with active contracts: 32–43 (12 players)
  Player 31 (Julian Alvarez): permanent contract with club 2, active LOAN to club 4

Temporary test data uses IDs 9901–9915 and is cleaned up after every test.
"""

import pytest
import pymysql

# ── Temporary IDs ─────────────────────────────────────────────────────────────
# 9901 – player with an EXPIRED contract (for contract-validity tests)
# 9902 – player with a FUTURE-START contract
# 9903 – player with NO contract at all
# 9904–9914 – 11 players with valid contracts (squad-size boundary tests)
# 9915 – 1 extra player (24th player test)
T_PERSON_IDS   = list(range(9901, 9916))   # 9901..9915
T_CONTRACT_IDS = list(range(9901, 9916))   # same IDs for simplicity (skip 9903)

# Matches used (must not clean participation from match 1 — it is already completed)
T_MATCHES_TO_CLEAN = (7, 8)

INSERT_PARTICIPATION = """
    INSERT INTO Match_Participation
        (match_id, player_id, club_id, is_starter, minutes_played,
         position_in_match, goals, assists, yellow_cards, red_cards, rating)
    VALUES (%s, %s, %s, %s, 0, 'Forward', 0, 0, 0, 0, 5.0)
"""


# ── Cleanup helpers ────────────────────────────────────────────────────────────

def _cleanup(db):
    ph = ', '.join(['%s'] * len(T_MATCHES_TO_CLEAN))
    with db.cursor() as cur:
        cur.execute(f"DELETE FROM Match_Participation WHERE match_id IN ({ph})", T_MATCHES_TO_CLEAN)

        ids_ph = ', '.join(['%s'] * len(T_PERSON_IDS))
        # Remove temp contracts (loan first due to FK, then permanent, then base)
        cur.execute(f"DELETE FROM Loan_Contract      WHERE contract_id IN ({ids_ph})", T_PERSON_IDS)
        cur.execute(f"DELETE FROM Permanent_Contract WHERE contract_id IN ({ids_ph})", T_PERSON_IDS)
        cur.execute(f"DELETE FROM Contract           WHERE contract_id IN ({ids_ph})", T_PERSON_IDS)
        cur.execute(f"DELETE FROM Player             WHERE person_id   IN ({ids_ph})", T_PERSON_IDS)
        cur.execute(f"DELETE FROM Person             WHERE person_id   IN ({ids_ph})", T_PERSON_IDS)
    db.commit()


@pytest.fixture(autouse=True)
def clean_test_data(db):
    _cleanup(db)
    yield
    _cleanup(db)


# ── Low-level helpers ─────────────────────────────────────────────────────────

def _add(db, match_id, player_id, club_id, is_starter=False):
    """Insert one participation row and commit. Raises on trigger violation."""
    with db.cursor() as cur:
        cur.execute(INSERT_PARTICIPATION, (match_id, player_id, club_id, is_starter))
    db.commit()


def _add_many(db, match_id, player_ids, club_id, starters=0):
    """Insert multiple rows; first `starters` are marked is_starter=True."""
    with db.cursor() as cur:
        for i, pid in enumerate(player_ids):
            cur.execute(INSERT_PARTICIPATION, (match_id, pid, club_id, i < starters))
    db.commit()


def _create_temp_players(db, ids, club_id,
                         contract_start='2025-07-01', contract_end='2027-06-30'):
    """Create Person + Player + Contract + Permanent_Contract rows for `ids`."""
    with db.cursor() as cur:
        for i, pid in enumerate(ids):
            cur.execute(
                "INSERT INTO Person (person_id, name, surname, nationality, date_of_birth) "
                "VALUES (%s, %s, %s, 'Turkish', '2000-01-01')",
                (pid, f'TmpP{i}', f'TmpS{i}')
            )
            cur.execute(
                "INSERT INTO Player (person_id, market_value, main_position, strong_foot, height) "
                "VALUES (%s, 1000000, 'Forward', 'Right', 180)",
                (pid,)
            )
            cur.execute(
                "INSERT INTO Contract (contract_id, player_id, club_id, start_date, end_date, weekly_wage) "
                "VALUES (%s, %s, %s, %s, %s, 50000)",
                (pid, pid, club_id, contract_start, contract_end)
            )
            cur.execute(
                "INSERT INTO Permanent_Contract (contract_id) VALUES (%s)", (pid,)
            )
    db.commit()


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestOp5SquadSubmission:

    # ── Squad size ────────────────────────────────────────────────────────────

    def test_exactly_11_players_accepted(self, db):
        """
        Inserting exactly 11 valid players for a club must succeed at the DB level.
        (11 is also the app-enforced minimum.)
        """
        _add_many(db, match_id=7, player_ids=range(8, 19), club_id=1)
        with db.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS cnt FROM Match_Participation WHERE match_id=7 AND club_id=1"
            )
            assert cur.fetchone()['cnt'] == 11

    def test_exactly_23_players_accepted(self, db):
        """
        Inserting exactly 23 valid players (the maximum allowed) must succeed.
        Uses 12 seed players (8–19) + 11 temp players (9904–9914).
        """
        _create_temp_players(db, range(9904, 9915), club_id=1)
        all_players = list(range(8, 20)) + list(range(9904, 9915))  # 12 + 11 = 23
        _add_many(db, match_id=7, player_ids=all_players, club_id=1)

        with db.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS cnt FROM Match_Participation WHERE match_id=7 AND club_id=1"
            )
            assert cur.fetchone()['cnt'] == 23

    def test_24th_player_rejected(self, db):
        """
        After 23 players, the trigger must reject a 24th insertion.
        """
        _create_temp_players(db, range(9904, 9916), club_id=1)  # 9904–9915 = 12 temp
        all_23 = list(range(8, 20)) + list(range(9904, 9915))   # 12 + 11 = 23
        _add_many(db, match_id=7, player_ids=all_23, club_id=1)

        with pytest.raises(pymysql.Error) as exc_info:
            _add(db, match_id=7, player_id=9915, club_id=1)
        db.rollback()
        assert '23' in str(exc_info.value) or '45000' in str(exc_info.value)

    def test_below_min_squad_allowed_at_db_level(self, db):
        """
        The DB trigger does NOT enforce the minimum squad size — that check lives
        in the app layer (routes/manager.py:142).  10 inserts must succeed at DB level.
        """
        _add_many(db, match_id=7, player_ids=range(8, 18), club_id=1)  # 10 players
        with db.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS cnt FROM Match_Participation WHERE match_id=7 AND club_id=1"
            )
            assert cur.fetchone()['cnt'] == 10

    # ── Starter count ─────────────────────────────────────────────────────────

    def test_ten_starters_accepted(self, db):
        """
        A squad may have fewer than 11 starters — 10 starters must be accepted.
        """
        _add_many(db, match_id=7, player_ids=range(8, 19), club_id=1, starters=10)
        with db.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS cnt FROM Match_Participation "
                "WHERE match_id=7 AND club_id=1 AND is_starter=1"
            )
            assert cur.fetchone()['cnt'] == 10

    def test_eleven_starters_accepted(self, db):
        """
        Exactly 11 starters is the allowed maximum — must be accepted.
        """
        _add_many(db, match_id=7, player_ids=range(8, 19), club_id=1, starters=11)
        with db.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS cnt FROM Match_Participation "
                "WHERE match_id=7 AND club_id=1 AND is_starter=1"
            )
            assert cur.fetchone()['cnt'] == 11

    def test_twelfth_starter_rejected(self, db):
        """
        After 11 starters the trigger must reject a 12th is_starter=True insertion.
        """
        _add_many(db, match_id=7, player_ids=range(8, 19), club_id=1, starters=11)

        with pytest.raises(pymysql.Error) as exc_info:
            _add(db, match_id=7, player_id=19, club_id=1, is_starter=True)
        db.rollback()
        assert '11' in str(exc_info.value) or '45000' in str(exc_info.value)

    # ── Contract validity ─────────────────────────────────────────────────────

    def test_player_no_contract_with_club_rejected(self, db):
        """
        Player 8 has a contract with club 1, not club 3.
        Inserting them into club 3's squad for match 7 must be rejected.
        """
        with pytest.raises(pymysql.Error) as exc_info:
            _add(db, match_id=7, player_id=8, club_id=3)
        db.rollback()
        assert 'contract' in str(exc_info.value).lower() or '45000' in str(exc_info.value)

    def test_expired_contract_rejected(self, db):
        """
        Player 9901 has only a contract that ended before match 7 (2026-05-10).
        Insertion must be rejected by the trigger.
        """
        _create_temp_players(db, [9901], club_id=1,
                             contract_start='2020-01-01', contract_end='2026-04-30')

        with pytest.raises(pymysql.Error) as exc_info:
            _add(db, match_id=7, player_id=9901, club_id=1)
        db.rollback()
        assert 'contract' in str(exc_info.value).lower() or '45000' in str(exc_info.value)

    def test_future_contract_start_rejected(self, db):
        """
        Player 9902 has a contract whose start_date is after match 7 (2026-05-10).
        Insertion must be rejected by the trigger.

        The contract INSERT trigger forces start_date = CURDATE(), so we INSERT
        first (satisfying the trigger) then UPDATE start_date to a future value —
        UPDATE does not re-fire the INSERT trigger.
        """
        _create_temp_players(db, [9902], club_id=1, contract_end='2028-06-30')
        with db.cursor() as cur:
            cur.execute(
                "UPDATE Contract SET start_date = '2026-06-01' WHERE contract_id = 9902"
            )
        db.commit()

        with pytest.raises(pymysql.Error) as exc_info:
            _add(db, match_id=7, player_id=9902, club_id=1)
        db.rollback()
        assert 'contract' in str(exc_info.value).lower() or '45000' in str(exc_info.value)

    def test_player_with_no_contract_at_all_rejected(self, db):
        """
        Player 9903 exists as a Person/Player record but has zero contracts.
        The trigger must reject their insertion into any squad.
        """
        with db.cursor() as cur:
            cur.execute(
                "INSERT INTO Person (person_id, name, surname, nationality, date_of_birth) "
                "VALUES (9903, 'No', 'Contract', 'Turkish', '2000-01-01')"
            )
            cur.execute(
                "INSERT INTO Player (person_id, market_value, main_position, strong_foot, height) "
                "VALUES (9903, 1000000, 'Forward', 'Right', 180)"
            )
        db.commit()

        with pytest.raises(pymysql.Error) as exc_info:
            _add(db, match_id=7, player_id=9903, club_id=1)
        db.rollback()
        assert 'contract' in str(exc_info.value).lower() or '45000' in str(exc_info.value)

    # ── Loan rule ─────────────────────────────────────────────────────────────

    def test_loan_player_rejected_from_parent_club(self, db):
        """
        Player 31 (Julian Alvarez) has a permanent contract with club 2 but is
        currently on loan to club 4.  Club 2 (parent) must not be allowed to
        select him for match 8 (club 4 vs club 2).
        """
        with pytest.raises(pymysql.Error) as exc_info:
            _add(db, match_id=8, player_id=31, club_id=2)
        db.rollback()
        assert 'loan' in str(exc_info.value).lower() or '45000' in str(exc_info.value)

    def test_loan_player_accepted_at_loan_club(self, db):
        """
        The same player 31 on loan to club 4 must be accepted into club 4's
        squad for match 8.
        """
        _add(db, match_id=8, player_id=31, club_id=4)
        with db.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS cnt FROM Match_Participation "
                "WHERE match_id=8 AND player_id=31 AND club_id=4"
            )
            assert cur.fetchone()['cnt'] == 1

    # ── Match state ───────────────────────────────────────────────────────────

    def test_completed_match_rejected(self, db):
        """
        Match 1 already has goals set.  Any squad insertion must be rejected
        ('Cannot modify squad for a match that already has results.').
        """
        with pytest.raises(pymysql.Error) as exc_info:
            _add(db, match_id=1, player_id=8, club_id=1)
        db.rollback()
        assert 'result' in str(exc_info.value).lower() or '45000' in str(exc_info.value)

    # ── Club validity ─────────────────────────────────────────────────────────

    def test_wrong_club_rejected(self, db):
        """
        Match 7 involves only clubs 1 and 3.  Trying to submit a squad entry
        for club 2 must be rejected ('Club is not participating in this match.').
        """
        with pytest.raises(pymysql.Error) as exc_info:
            _add(db, match_id=7, player_id=20, club_id=2)
        db.rollback()
        assert 'participating' in str(exc_info.value).lower() or '45000' in str(exc_info.value)
