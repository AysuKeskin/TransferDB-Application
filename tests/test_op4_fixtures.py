"""
Operation 4: Viewing fixtures and results (Manager)

Spec requirements:
  - Manager can see all matches their club is involved in
  - Past matches (home_goals IS NOT NULL) show score and Win/Loss/Draw result
  - Future matches (home_goals IS NULL) show as 'Scheduled'
  - Win/Loss/Draw is computed from the perspective of the manager's own club

The result column is computed entirely at the SQL level via a CASE expression
(see routes/manager.py::manager_fixtures).  These tests run that same SQL
directly against the DB so they verify correctness independent of Flask.

Seed data used (IDs guaranteed present after seed_data.sql):
  Match 1 : Royal Madrid (1, home)     vs Manchester Blues (2, away)  → 2-1  (RM wins)
  Match 3 : Manchester Blues (2, home) vs Liverpool Reds   (3, away)  → 1-1  (Draw)
  Match 4 : Atletico Madrid  (4, home) vs Royal Madrid     (1, away)  → 0-3  (RM wins away)
  Match 7 : Royal Madrid (1, home)     vs Liverpool Reds   (3, away)  → no goals (Scheduled)
"""

import pytest

# ── The exact query used by routes/manager.py::manager_fixtures ───────────────
FIXTURES_QUERY = """
    SELECT m.match_id,
           CASE WHEN m.home_goals IS NOT NULL THEN 'Completed' ELSE 'Scheduled' END AS status,
           m.home_goals, m.away_goals,
           CASE WHEN m.home_goals IS NULL THEN 'Scheduled'
                WHEN (m.home_club_id = %s AND m.home_goals > m.away_goals)
                  OR (m.away_club_id = %s AND m.away_goals > m.home_goals) THEN 'Win'
                WHEN m.home_goals = m.away_goals THEN 'Draw'
                ELSE 'Loss' END AS result
    FROM `Match` m
    WHERE m.match_id = %s
"""


# ── Helper ────────────────────────────────────────────────────────────────────

def _get_result(db, club_id, match_id):
    with db.cursor() as cur:
        cur.execute(FIXTURES_QUERY, (club_id, club_id, match_id))
        return cur.fetchone()


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestOp4FixturesResults:

    def test_future_match_shows_scheduled(self, db):
        """
        Match 7: Royal Madrid vs Liverpool Reds — future date, no goals.
        Must appear as status='Scheduled' and result='Scheduled'.
        """
        row = _get_result(db, club_id=1, match_id=7)

        assert row is not None
        assert row['status'] == 'Scheduled'
        assert row['result'] == 'Scheduled'
        assert row['home_goals'] is None
        assert row['away_goals'] is None

    def test_home_win_shows_win_for_home_club(self, db):
        """
        Match 1: Royal Madrid (home) 2-1 Manchester Blues (away).
        From club 1's perspective → 'Win'.
        From club 2's perspective → 'Loss'.
        """
        home_row = _get_result(db, club_id=1, match_id=1)
        away_row = _get_result(db, club_id=2, match_id=1)

        assert home_row['result'] == 'Win',  f"Expected Win for home club, got: {home_row['result']}"
        assert away_row['result'] == 'Loss', f"Expected Loss for away club, got: {away_row['result']}"
        assert home_row['status'] == 'Completed'

    def test_away_win_shows_win_for_away_club(self, db):
        """
        Match 4: Atletico Madrid (home) 0-3 Royal Madrid (away).
        From club 1's (RM) perspective → 'Win'.
        From club 4's (Atletico) perspective → 'Loss'.
        """
        away_winner = _get_result(db, club_id=1, match_id=4)
        home_loser  = _get_result(db, club_id=4, match_id=4)

        assert away_winner['result'] == 'Win',  f"Expected Win for away club, got: {away_winner['result']}"
        assert home_loser['result']  == 'Loss', f"Expected Loss for home club, got: {home_loser['result']}"

    def test_draw_shows_draw_for_both_clubs(self, db):
        """
        Match 3: Manchester Blues (home) 1-1 Liverpool Reds (away).
        Both clubs must see 'Draw'.
        """
        home_row = _get_result(db, club_id=2, match_id=3)
        away_row = _get_result(db, club_id=3, match_id=3)

        assert home_row['result'] == 'Draw', f"Expected Draw for home club, got: {home_row['result']}"
        assert away_row['result'] == 'Draw', f"Expected Draw for away club, got: {away_row['result']}"

    def test_completed_match_shows_correct_score(self, db):
        """
        Match 1: score must be returned as home_goals=2, away_goals=1.
        """
        row = _get_result(db, club_id=1, match_id=1)

        assert row['home_goals'] == 2
        assert row['away_goals'] == 1
        assert row['status'] == 'Completed'
