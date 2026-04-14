"""
Operation 3: Scheduling a match (Database Manager)

Spec requirements (relevant to these tests):
  - No stadium, club, or referee can be involved in two matches whose
    start times are within 120 minutes of each other.

The constraint is enforced by trg_match_before_insert (triggers.sql).
These tests insert directly via SQL to verify the DB-level enforcement.

Seed data used (IDs guaranteed present after seed_data.sql):
  Stadiums  : 1 (Santiago Bernabeu), 2 (Etihad Stadium)
  Clubs     : 1 (Royal Madrid), 2 (Manchester Blues),
              3 (Liverpool Reds), 4 (Atletico Madrid)
  Referees  : 5 (Michael Oliver), 6 (Felix Brych)
  Competition: 1 (Premier League 2025/2026)

Test match IDs 9901–9902 are used and cleaned up after every test.
"""

import pytest
import pymysql

# ── Constants ─────────────────────────────────────────────────────────────────
T_MATCH1_ID = 9901
T_MATCH2_ID = 9902

# Both in the future (2027) so the "must be future" trigger check passes.
TIME_1 = '2027-06-01 15:00:00'   # base time
TIME_OVERLAP = '2027-06-01 15:59:00'   # 59 min later  → within 120 min → conflict
TIME_OK      = '2027-06-01 17:01:00'   # 121 min later → outside 120 min → no conflict

INSERT_MATCH = """
    INSERT INTO `Match`
        (match_id, competition_id, home_club_id, away_club_id,
         stadium_id, match_datetime, referee_id)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _cleanup(db):
    with db.cursor() as cur:
        cur.execute("DELETE FROM `Match` WHERE match_id IN (%s, %s)", (T_MATCH1_ID, T_MATCH2_ID))
    db.commit()


# ── Fixture ───────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clean_test_matches(db):
    _cleanup(db)
    yield
    _cleanup(db)


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestOp3MatchScheduling:

    def test_stadium_overlap_rejected(self, db):
        """
        Two matches at the same stadium within 120 minutes must be rejected
        by the DB trigger, regardless of clubs and referee.

        Match 1: stadium=1, clubs 1 vs 2, referee=5, 15:00
        Match 2: stadium=1, clubs 3 vs 4, referee=6, 15:59  ← 59 min gap → conflict
        """
        # Insert the first match — must succeed
        with db.cursor() as cur:
            cur.execute(INSERT_MATCH, (T_MATCH1_ID, 1, 1, 2, 1, TIME_1, 5))
        db.commit()

        # Insert the second match at the same stadium 59 min later — must be rejected
        with pytest.raises(pymysql.Error) as exc_info:
            with db.cursor() as cur:
                cur.execute(INSERT_MATCH, (T_MATCH2_ID, 1, 3, 4, 1, TIME_OVERLAP, 6))
            db.commit()

        db.rollback()
        assert 'conflicts' in str(exc_info.value).lower() or '45000' in str(exc_info.value)

    def test_referee_overlap_rejected(self, db):
        """
        Assigning the same referee to two matches within 120 minutes must be
        rejected by the DB trigger, even if the stadium and clubs are different.

        Match 1: stadium=1, clubs 1 vs 2, referee=5, 15:00
        Match 2: stadium=2, clubs 3 vs 4, referee=5, 15:59  ← same referee → conflict
        """
        # Insert the first match — must succeed
        with db.cursor() as cur:
            cur.execute(INSERT_MATCH, (T_MATCH1_ID, 1, 1, 2, 1, TIME_1, 5))
        db.commit()

        # Insert the second match with the same referee 59 min later — must be rejected
        with pytest.raises(pymysql.Error) as exc_info:
            with db.cursor() as cur:
                cur.execute(INSERT_MATCH, (T_MATCH2_ID, 1, 3, 4, 2, TIME_OVERLAP, 5))
            db.commit()

        db.rollback()
        assert 'conflicts' in str(exc_info.value).lower() or '45000' in str(exc_info.value)

    def test_club_overlap_rejected(self, db):
        """
        A club already scheduled in one match cannot appear in another match
        within 120 minutes, even at a different stadium with a different referee.

        Match 1: stadium=1, home=1 (Royal Madrid) vs away=2, referee=5, 15:00
        Match 2: stadium=2, home=1 (Royal Madrid) vs away=3, referee=6, 15:59
                 ← Royal Madrid already busy → conflict
        """
        with db.cursor() as cur:
            cur.execute(INSERT_MATCH, (T_MATCH1_ID, 1, 1, 2, 1, TIME_1, 5))
        db.commit()

        with pytest.raises(pymysql.Error) as exc_info:
            with db.cursor() as cur:
                cur.execute(INSERT_MATCH, (T_MATCH2_ID, 1, 1, 3, 2, TIME_OVERLAP, 6))
            db.commit()

        db.rollback()
        assert 'conflicts' in str(exc_info.value).lower() or '45000' in str(exc_info.value)
