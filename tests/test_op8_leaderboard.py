"""
Operation 8: Competition leaderboard (Manager)

Spec requirements:
  - Top 10 players per competition+season for three categories:
      'goals'      → SUM(goals), no match minimum
      'assists'    → SUM(assists), no match minimum
      'avg_rating' → ROUND(AVG(rating),2), minimum 3 matches played
  - Columns: name, surname, club_name, matches_played, metric
  - Ordered by metric DESC, limited to 10 rows
  - Only completed matches (home_goals IS NOT NULL) count

Seed data — Competition 1 (Premier League 2025/2026), completed matches 1–4:
  Top goal scorers:
    Player 16 (Vinicius Junior,  club 1): match1=1g + match4=2g = 3 goals
    Player 40 (Mohamed Salah,    club 3): match2=2g + match3=1g = 3 goals
  Top assist providers:
    Player 17 (Rodrygo Goes,     club 1): match1=1a + match4=1a = 2 assists
    Player 41 (Sadio Mane,       club 3): match2=1a + match3=1a = 2 assists
  Avg rating:
    Every player in comp 1 played exactly 2 matches → HAVING matches_played >= 3
    filters ALL players → result is empty.

Future matches 7, 8, 10 also belong to comp 1 but have no goals (home_goals IS NULL)
and no Match_Participation rows — they must not inflate any metric.
"""

import pytest

# ── Queries (exact copies of the route logic) ─────────────────────────────────
_BASE = """
    SELECT p.name, p.surname, cl.club_name,
           COUNT(DISTINCT mp.match_id) AS matches_played,
"""

_FROM = """
    FROM Match_Participation mp
    JOIN Person p  ON mp.player_id = p.person_id
    JOIN Club cl   ON mp.club_id   = cl.club_id
    JOIN `Match` m ON mp.match_id  = m.match_id
    WHERE m.competition_id = %s AND m.home_goals IS NOT NULL
    GROUP BY mp.player_id, p.name, p.surname, cl.club_name
"""

GOALS_QUERY      = _BASE + "SUM(mp.goals)            AS metric" + _FROM + "ORDER BY metric DESC LIMIT 10"
ASSISTS_QUERY    = _BASE + "SUM(mp.assists)           AS metric" + _FROM + "ORDER BY metric DESC LIMIT 10"
AVG_RATING_QUERY = _BASE + "ROUND(AVG(mp.rating),2)  AS metric" + _FROM + "HAVING matches_played >= 3 ORDER BY metric DESC LIMIT 10"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _leaderboard(db, query, comp_id):
    with db.cursor() as cur:
        cur.execute(query, (comp_id,))
        return cur.fetchall()

def _find(rows, surname):
    return next((r for r in rows if r['surname'] == surname), None)


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestOp8Leaderboard:

    # ── Goals category ────────────────────────────────────────────────────────

    def test_goals_top_scorer_metric(self, db):
        """Top goal scorer in comp 1 must have metric = 3 (Vinicius or Salah)."""
        rows = _leaderboard(db, GOALS_QUERY, comp_id=1)
        assert rows, "Goals leaderboard must not be empty"
        assert int(rows[0]['metric']) == 3

    def test_goals_both_top_scorers_in_top3(self, db):
        """Vinicius (club 1) and Salah (club 3) both scored 3 goals — both must appear."""
        rows = _leaderboard(db, GOALS_QUERY, comp_id=1)
        surnames = {r['surname'] for r in rows}
        assert 'Junior' in surnames, "Vinicius Junior missing from goals leaderboard"
        assert 'Salah'  in surnames, "Mohamed Salah missing from goals leaderboard"

    def test_goals_ordered_descending(self, db):
        """Each row's metric must be >= the next row's metric (DESC order)."""
        rows = _leaderboard(db, GOALS_QUERY, comp_id=1)
        for i in range(len(rows) - 1):
            assert int(rows[i]['metric']) >= int(rows[i + 1]['metric']), (
                f"Row {i} metric {rows[i]['metric']} < row {i+1} metric {rows[i+1]['metric']}"
            )

    def test_goals_limit_10(self, db):
        """Comp 1 has 44 participants — result must be capped at 10 rows."""
        rows = _leaderboard(db, GOALS_QUERY, comp_id=1)
        assert len(rows) <= 10

    def test_goals_matches_played_correct(self, db):
        """
        Player 16 (Vinicius) participated in matches 1 and 4 in comp 1 → matches_played = 2.
        Future match 7 (comp 1, no goals) must not be counted.
        """
        rows = _leaderboard(db, GOALS_QUERY, comp_id=1)
        vinicius = _find(rows, 'Junior')
        assert vinicius is not None
        assert vinicius['matches_played'] == 2

    def test_goals_required_columns_present(self, db):
        """Every row must contain name, surname, club_name, matches_played, metric."""
        rows = _leaderboard(db, GOALS_QUERY, comp_id=1)
        assert rows
        for col in ('name', 'surname', 'club_name', 'matches_played', 'metric'):
            assert col in rows[0], f"Column '{col}' missing from leaderboard row"

    # ── Assists category ──────────────────────────────────────────────────────

    def test_assists_top_provider_metric(self, db):
        """Top assist provider in comp 1 must have metric = 2 (Rodrygo or Mane)."""
        rows = _leaderboard(db, ASSISTS_QUERY, comp_id=1)
        assert rows, "Assists leaderboard must not be empty"
        assert int(rows[0]['metric']) == 2

    def test_assists_both_top_providers_present(self, db):
        """Rodrygo (club 1) and Mane (club 3) each have 2 assists — both must appear."""
        rows = _leaderboard(db, ASSISTS_QUERY, comp_id=1)
        surnames = {r['surname'] for r in rows}
        assert 'Goes'  in surnames, "Rodrygo Goes missing from assists leaderboard"
        assert 'Mane'  in surnames, "Sadio Mane missing from assists leaderboard"

    def test_assists_ordered_descending(self, db):
        """Assists must be ranked DESC."""
        rows = _leaderboard(db, ASSISTS_QUERY, comp_id=1)
        for i in range(len(rows) - 1):
            assert int(rows[i]['metric']) >= int(rows[i + 1]['metric'])

    # ── Avg rating category ───────────────────────────────────────────────────

    def test_avg_rating_min_3_matches_filters_everyone_in_comp1(self, db):
        """
        In comp 1 every player played exactly 2 matches.
        The HAVING matches_played >= 3 clause must exclude all of them → empty result.
        This directly verifies the '3 match minimum' spec requirement.
        """
        rows = _leaderboard(db, AVG_RATING_QUERY, comp_id=1)
        assert len(rows) == 0, (
            f"Expected empty avg_rating leaderboard (all players have <3 matches), "
            f"got {len(rows)} rows"
        )

    def test_goals_has_no_minimum_match_filter(self, db):
        """
        Unlike avg_rating, goals has no minimum match requirement.
        The goals leaderboard for comp 1 must NOT be empty.
        """
        rows = _leaderboard(db, GOALS_QUERY, comp_id=1)
        assert len(rows) > 0

    # ── Category isolation ────────────────────────────────────────────────────

    def test_goals_and_assists_return_different_metrics(self, db):
        """
        The same player (Vinicius) has goals=3, assists=0 in comp 1.
        Goals leaderboard shows him at the top; assists leaderboard must not
        show him at the top (his assists metric = 0).
        """
        goal_rows    = _leaderboard(db, GOALS_QUERY,   comp_id=1)
        assists_rows = _leaderboard(db, ASSISTS_QUERY, comp_id=1)

        # Vinicius tops goals
        assert _find(goal_rows, 'Junior') is not None
        assert int(goal_rows[0]['metric']) == 3

        # Vinicius has 0 assists — should not be at the top of assists
        top_assists_metric = int(assists_rows[0]['metric'])
        assert top_assists_metric == 2, f"Top assists should be 2, got {top_assists_metric}"

    # ── No competition selected ───────────────────────────────────────────────

    def test_no_comp_returns_empty_leaderboard(self, db):
        """
        The route only runs the leaderboard query when comp_id is provided.
        Without comp_id (empty string), leaderboard stays [].
        Simulate by querying with a non-existent comp_id.
        """
        rows = _leaderboard(db, GOALS_QUERY, comp_id=9999)
        assert len(rows) == 0

    # ── Completed matches only ────────────────────────────────────────────────

    def test_only_completed_matches_in_leaderboard(self, db):
        """
        Comp 1 has future matches 7, 8, 10 with home_goals IS NULL.
        Player 16 (Vinicius) should have matches_played = 2 (matches 1 and 4),
        not 3 — confirming the WHERE home_goals IS NOT NULL filter works.
        """
        rows = _leaderboard(db, GOALS_QUERY, comp_id=1)
        vinicius = _find(rows, 'Junior')
        assert vinicius is not None
        assert vinicius['matches_played'] == 2, (
            f"Expected 2 completed matches for Vinicius, got {vinicius['matches_played']}"
        )
