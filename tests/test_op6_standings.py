"""
Operation 6: League standings (Manager)

Spec requirements:
  - Only League-type competitions in which the manager's club has participated.
  - Ranked by Total Points DESC, then Goal Difference DESC.
  - Columns: Club Name, MP, W, D, L, GS, GC, GD, Pts.
  - Points: Win=3, Draw=1, Loss=0.
  - Only completed matches (home_goals IS NOT NULL) count.

These tests run the exact SQL query used by routes/manager.py::manager_standings()
directly against the database.

Seed data used:
  Competition 1 : Premier League 2025/2026  (League)  — matches 1-4 completed
  Competition 2 : Champions League 2025/2026 (Cup)    — matches 5-6 completed
  Competition 3 : Premier League 2024/2025  (League)  — no matches

  Completed match results for Competition 1:
    Match 1 : Royal Madrid  (1) 2-1 Manchester Blues (2)  → RM win
    Match 2 : Liverpool Reds(3) 3-0 Atletico Madrid  (4)  → LR win
    Match 3 : Manchester Blues(2) 1-1 Liverpool Reds (3)  → Draw
    Match 4 : Atletico Madrid (4) 0-3 Royal Madrid   (1)  → RM win (away)

  Expected standings for Competition 1:
    1. Royal Madrid      2MP  2W 0D 0L  GS=5 GC=1 GD=+4 Pts=6
    2. Liverpool Reds    2MP  1W 1D 0L  GS=4 GC=1 GD=+3 Pts=4
    3. Manchester Blues  2MP  0W 1D 1L  GS=2 GC=3 GD=-1 Pts=1
    4. Atletico Madrid   2MP  0W 0D 2L  GS=0 GC=6 GD=-6 Pts=0

  Future matches 7, 8, 10 also belong to Competition 1 but have no goals —
  they must NOT affect the standings.
"""

import pytest

# ── The exact query used by routes/manager.py::manager_standings ──────────────
STANDINGS_QUERY = """
    SELECT cl.club_id, cl.club_name,
           COUNT(*) AS played,
           SUM(CASE WHEN (m.home_club_id = cl.club_id AND m.home_goals > m.away_goals)
                      OR (m.away_club_id = cl.club_id AND m.away_goals > m.home_goals)
                    THEN 1 ELSE 0 END) AS wins,
           SUM(CASE WHEN m.home_goals = m.away_goals THEN 1 ELSE 0 END) AS draws,
           SUM(CASE WHEN (m.home_club_id = cl.club_id AND m.home_goals < m.away_goals)
                      OR (m.away_club_id = cl.club_id AND m.away_goals < m.home_goals)
                    THEN 1 ELSE 0 END) AS losses,
           SUM(CASE WHEN m.home_club_id = cl.club_id THEN m.home_goals
                    ELSE m.away_goals END) AS goals_scored,
           SUM(CASE WHEN m.home_club_id = cl.club_id THEN m.away_goals
                    ELSE m.home_goals END) AS goals_conceded,
           SUM(CASE WHEN m.home_club_id = cl.club_id THEN m.home_goals - m.away_goals
                    ELSE m.away_goals - m.home_goals END) AS goal_diff,
           SUM(CASE WHEN (m.home_club_id = cl.club_id AND m.home_goals > m.away_goals)
                      OR (m.away_club_id = cl.club_id AND m.away_goals > m.home_goals)
                    THEN 3
                    WHEN m.home_goals = m.away_goals THEN 1
                    ELSE 0 END) AS points
    FROM Club cl
    JOIN `Match` m ON (m.home_club_id = cl.club_id OR m.away_club_id = cl.club_id)
    WHERE m.competition_id = %s AND m.home_goals IS NOT NULL
    GROUP BY cl.club_id, cl.club_name
    ORDER BY points DESC, goal_diff DESC, goals_scored DESC
"""

LEAGUE_COMPETITIONS_QUERY = """
    SELECT DISTINCT comp.competition_id, comp.name, comp.season
    FROM Competition comp
    JOIN `Match` m ON m.competition_id = comp.competition_id
    WHERE comp.competition_type = 'League'
      AND (m.home_club_id = %s OR m.away_club_id = %s)
    ORDER BY comp.season DESC, comp.name
"""


# ── Helper ─────────────────────────────────────────────────────────────────────

def _standings(db, competition_id):
    with db.cursor() as cur:
        cur.execute(STANDINGS_QUERY, (competition_id,))
        return cur.fetchall()


def _row(standings, club_id):
    return next((r for r in standings if r['club_id'] == club_id), None)


# ── Tests ──────────────────────────────────────────────────────────────────────

class TestOp6Standings:

    def test_ranking_order_points_desc(self, db):
        """
        Competition 1 standings must be ordered:
        Royal Madrid (6 pts) → Liverpool Reds (4) → Manchester Blues (1) → Atletico Madrid (0).
        """
        rows = _standings(db, competition_id=1)
        assert len(rows) == 4
        assert rows[0]['club_id'] == 1, f"Expected Royal Madrid 1st, got club {rows[0]['club_id']}"
        assert rows[1]['club_id'] == 3, f"Expected Liverpool Reds 2nd, got club {rows[1]['club_id']}"
        assert rows[2]['club_id'] == 2, f"Expected Manchester Blues 3rd, got club {rows[2]['club_id']}"
        assert rows[3]['club_id'] == 4, f"Expected Atletico Madrid 4th, got club {rows[3]['club_id']}"

    def test_points_win_equals_3(self, db):
        """Royal Madrid won both matches → 2×3 = 6 points."""
        rm = _row(_standings(db, 1), club_id=1)
        assert rm['points'] == 6

    def test_points_draw_equals_1(self, db):
        """Manchester Blues drew once and lost once → 1×1 + 1×0 = 1 point."""
        mb = _row(_standings(db, 1), club_id=2)
        assert mb['points'] == 1

    def test_points_loss_equals_0(self, db):
        """Atletico Madrid lost both matches → 0 points."""
        am = _row(_standings(db, 1), club_id=4)
        assert am['points'] == 0

    def test_wins_draws_losses_counts(self, db):
        """Verify W/D/L for all four clubs."""
        rows = _standings(db, 1)
        rm = _row(rows, 1)
        lr = _row(rows, 3)
        mb = _row(rows, 2)
        am = _row(rows, 4)

        assert (rm['wins'], rm['draws'], rm['losses']) == (2, 0, 0)
        assert (lr['wins'], lr['draws'], lr['losses']) == (1, 1, 0)
        assert (mb['wins'], mb['draws'], mb['losses']) == (0, 1, 1)
        assert (am['wins'], am['draws'], am['losses']) == (0, 0, 2)

    def test_matches_played_count(self, db):
        """Every club has played exactly 2 completed matches in competition 1."""
        for row in _standings(db, 1):
            assert row['played'] == 2, f"Club {row['club_id']} expected 2 played, got {row['played']}"

    def test_goals_scored_home_and_away(self, db):
        """
        Royal Madrid scored 2 at home (match 1) + 3 away (match 4) = 5 total.
        Goals scored must aggregate both home and away goals correctly.
        """
        rm = _row(_standings(db, 1), club_id=1)
        assert rm['goals_scored'] == 5

    def test_goals_conceded_home_and_away(self, db):
        """
        Royal Madrid conceded 1 at home (match 1) + 0 away (match 4) = 1 total.
        """
        rm = _row(_standings(db, 1), club_id=1)
        assert rm['goals_conceded'] == 1

    def test_goal_difference_all_clubs(self, db):
        """GD = GS − GC for every club."""
        rows = _standings(db, 1)
        for row in rows:
            expected_gd = row['goals_scored'] - row['goals_conceded']
            assert row['goal_diff'] == expected_gd, (
                f"Club {row['club_id']}: GD={row['goal_diff']} but GS-GC={expected_gd}"
            )

    def test_future_matches_not_counted(self, db):
        """
        Matches 7, 8, 10 belong to competition 1 but have no goals yet.
        They must not appear in the standings (played count stays at 2, not 3+).
        """
        for row in _standings(db, 1):
            assert row['played'] == 2, (
                f"Club {row['club_id']} shows {row['played']} played — future matches are leaking in"
            )

    def test_empty_standings_for_competition_with_no_matches(self, db):
        """
        Competition 3 (Premier League 2024/2025) has no matches at all.
        The standings query must return zero rows.
        """
        rows = _standings(db, competition_id=3)
        assert rows == [] or len(rows) == 0

    def test_cup_competition_excluded_from_league_dropdown(self, db):
        """
        Competition 2 is type='Cup'.  The league competitions query (which
        populates the manager's dropdown) must NOT return it, even though
        it has completed matches.  Royal Madrid (club 1) participated in it.
        """
        with db.cursor() as cur:
            cur.execute(LEAGUE_COMPETITIONS_QUERY, (1, 1))
            comps = cur.fetchall()
        comp_ids = [c['competition_id'] for c in comps]
        assert 2 not in comp_ids, "Cup competition (id=2) must not appear in the league dropdown"

    def test_atletico_away_goals_conceded_correctly(self, db):
        """
        Atletico Madrid conceded 3 goals away (match 4, lost 0-3) +
        3 goals at home (match 2, lost 0-3 to Liverpool) = 6 total conceded.
        """
        am = _row(_standings(db, 1), club_id=4)
        assert am['goals_conceded'] == 6

    def test_draw_goals_counted_for_both_clubs(self, db):
        """
        Match 3: Manchester Blues 1-1 Liverpool Reds.
        Both clubs must count 1 goal scored and 1 goal conceded from this match.
        Liverpool Reds: match 2 (3 scored, 0 conceded) + match 3 (1 scored, 1 conceded) = 4 GS, 1 GC.
        """
        lr = _row(_standings(db, 1), club_id=3)
        assert lr['goals_scored'] == 4
        assert lr['goals_conceded'] == 1
