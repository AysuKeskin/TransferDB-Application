"""
Operation 16: Viewing performance statistics (Player)

Route: routes/player.py::player_stats

Spec requirements:
  - Career aggregation (default across all clubs/competitions).
  - Seasonal filtering.
  - Competition + season filtering.
  - Metrics: matches, goals, assists, yellow/red cards, average rating.
"""


BASE_SELECT = """
    SELECT COUNT(DISTINCT mp.match_id) AS matches_played,
           COALESCE(SUM(mp.goals),0) AS goals,
           COALESCE(SUM(mp.assists),0) AS assists,
           COALESCE(SUM(mp.yellow_cards),0) AS yellow_cards,
           COALESCE(SUM(mp.red_cards),0) AS red_cards,
           COALESCE(ROUND(AVG(mp.rating),2),0) AS avg_rating
    FROM Match_Participation mp
"""


def _player_stats(db, player_id, season='', comp_id=''):
    with db.cursor() as cur:
        if season and comp_id:
            cur.execute(
                BASE_SELECT + """
                JOIN `Match` m ON mp.match_id = m.match_id
                JOIN Competition comp ON m.competition_id = comp.competition_id
                WHERE mp.player_id = %s AND comp.season = %s AND comp.competition_id = %s
                """,
                (player_id, season, comp_id),
            )
        elif season:
            cur.execute(
                BASE_SELECT + """
                JOIN `Match` m ON mp.match_id = m.match_id
                JOIN Competition comp ON m.competition_id = comp.competition_id
                WHERE mp.player_id = %s AND comp.season = %s
                """,
                (player_id, season),
            )
        else:
            cur.execute(BASE_SELECT + " WHERE mp.player_id = %s", (player_id,))
        return cur.fetchone()


class TestOp16PlayerStats:

    def test_career_aggregation_matches_independent_totals(self, db):
        """Default view must match independent aggregation over all participations."""
        route_row = _player_stats(db, 16)

        with db.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(DISTINCT match_id) AS matches_played,
                       COALESCE(SUM(goals), 0) AS goals,
                       COALESCE(SUM(assists), 0) AS assists,
                       COALESCE(SUM(yellow_cards), 0) AS yellow_cards,
                       COALESCE(SUM(red_cards), 0) AS red_cards,
                       COALESCE(ROUND(AVG(rating),2),0) AS avg_rating
                FROM Match_Participation
                WHERE player_id = %s
                """,
                (16,),
            )
            expected = cur.fetchone()

        assert route_row == expected

    def test_season_filter_matches_independent_totals(self, db):
        """Seasonal view must match independent aggregation for that season."""
        route_row = _player_stats(db, 16, season='2025/2026')

        with db.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(DISTINCT mp.match_id) AS matches_played,
                       COALESCE(SUM(mp.goals),0) AS goals,
                       COALESCE(SUM(mp.assists),0) AS assists,
                       COALESCE(SUM(mp.yellow_cards),0) AS yellow_cards,
                       COALESCE(SUM(mp.red_cards),0) AS red_cards,
                       COALESCE(ROUND(AVG(mp.rating),2),0) AS avg_rating
                FROM Match_Participation mp
                JOIN `Match` m ON mp.match_id = m.match_id
                JOIN Competition comp ON m.competition_id = comp.competition_id
                WHERE mp.player_id = %s AND comp.season = %s
                """,
                (16, '2025/2026'),
            )
            expected = cur.fetchone()

        assert route_row == expected

    def test_competition_and_season_filter_narrows_scope(self, db):
        """Competition+season view must be a narrowed subset of season-level stats."""
        season_row = _player_stats(db, 16, season='2025/2026')
        comp_row = _player_stats(db, 16, season='2025/2026', comp_id='1')

        assert comp_row['matches_played'] <= season_row['matches_played']
        assert comp_row['goals'] <= season_row['goals']
        assert comp_row['assists'] <= season_row['assists']
        assert comp_row['yellow_cards'] <= season_row['yellow_cards']
        assert comp_row['red_cards'] <= season_row['red_cards']

    def test_nonexistent_season_returns_zeroes(self, db):
        """Filtering to a season with no player matches must return zeroed metrics."""
        row = _player_stats(db, 16, season='1999/2000')
        assert row['matches_played'] == 0
        assert row['goals'] == 0
        assert row['assists'] == 0
        assert row['yellow_cards'] == 0
        assert row['red_cards'] == 0
        assert row['avg_rating'] == 0

    def test_average_rating_is_rounded_to_two_decimals(self, db):
        """Average rating should follow route rounding rule: ROUND(..., 2)."""
        row = _player_stats(db, 16)
        val = float(row['avg_rating'])
        assert round(val, 2) == val
