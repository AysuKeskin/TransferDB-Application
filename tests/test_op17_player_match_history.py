"""
Operation 17: Viewing player's match history (Player)

Route: routes/player.py::player_matches

Spec requirements:
  - Chronological history of participated matches.
  - Includes competition, stadium, opposing club, final result.
  - Includes per-match player stats.
  - Scheduled matches must be labeled appropriately.
"""

import pytest

PLAYER_ID = 16

ROUTE_QUERY = """
    SELECT m.match_id, m.match_datetime, m.home_goals, m.away_goals,
           CASE WHEN m.home_goals IS NOT NULL THEN 'Completed' ELSE 'Scheduled' END AS status,
           comp.name AS competition, comp.season,
           s.stadium_name,
           hc.club_name AS home_club, ac.club_name AS away_club,
           mp.club_id, mp.minutes_played, mp.position_in_match,
           mp.goals, mp.assists, mp.yellow_cards, mp.red_cards, mp.rating,
           mp.is_starter,
           CASE WHEN mp.club_id = m.home_club_id THEN ac.club_name
                ELSE hc.club_name END AS opposing_club,
           CASE WHEN m.home_goals IS NULL THEN 'Scheduled'
                WHEN (mp.club_id = m.home_club_id AND m.home_goals > m.away_goals)
                  OR (mp.club_id = m.away_club_id AND m.away_goals > m.home_goals) THEN 'Win'
                WHEN m.home_goals = m.away_goals THEN 'Draw'
                ELSE 'Loss' END AS result
    FROM Match_Participation mp
    JOIN `Match` m ON mp.match_id = m.match_id
    JOIN Competition comp ON m.competition_id = comp.competition_id
    JOIN Stadium s ON m.stadium_id = s.stadium_id
    JOIN Club hc ON m.home_club_id = hc.club_id
    JOIN Club ac ON m.away_club_id = ac.club_id
    WHERE mp.player_id = %s
    ORDER BY m.match_datetime DESC
"""


def _cleanup(db):
    with db.cursor() as cur:
        cur.execute(
            "DELETE FROM Match_Participation WHERE match_id = 7 AND player_id = %s AND club_id = 1",
            (PLAYER_ID,),
        )
    db.commit()


@pytest.fixture(autouse=True)
def clean_temp(db):
    _cleanup(db)
    yield
    _cleanup(db)


def _history(db, player_id):
    with db.cursor() as cur:
        cur.execute(ROUTE_QUERY, (player_id,))
        return cur.fetchall()


class TestOp17PlayerMatchHistory:

    def test_history_contains_all_participated_matches(self, db):
        """History row count must match participation row count for the player."""
        rows = _history(db, PLAYER_ID)
        with db.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS cnt FROM Match_Participation WHERE player_id = %s", (PLAYER_ID,))
            expected = cur.fetchone()['cnt']
        assert len(rows) == expected

    def test_history_is_ordered_descending_by_datetime(self, db):
        """Rows must be sorted by match_datetime DESC."""
        rows = _history(db, PLAYER_ID)
        for i in range(len(rows) - 1):
            assert rows[i]['match_datetime'] >= rows[i + 1]['match_datetime']

    def test_opposing_club_is_derived_correctly(self, db):
        """Opposing club must be away club when player is home, else home club."""
        rows = _history(db, PLAYER_ID)
        with db.cursor() as cur:
            for row in rows:
                cur.execute(
                    "SELECT home_club_id, away_club_id FROM `Match` WHERE match_id = %s",
                    (row['match_id'],),
                )
                ids = cur.fetchone()
                if row['club_id'] == ids['home_club_id']:
                    assert row['opposing_club'] == row['away_club']
                else:
                    assert row['opposing_club'] == row['home_club']

    def test_result_label_for_completed_matches_is_correct(self, db):
        """For completed matches, result must match win/draw/loss logic."""
        rows = _history(db, PLAYER_ID)
        with db.cursor() as cur:
            for row in rows:
                if row['status'] == 'Scheduled':
                    continue
                cur.execute(
                    "SELECT home_club_id, away_club_id FROM `Match` WHERE match_id = %s",
                    (row['match_id'],),
                )
                ids = cur.fetchone()

                if row['home_goals'] == row['away_goals']:
                    expected = 'Draw'
                elif (
                    row['club_id'] == ids['home_club_id'] and row['home_goals'] > row['away_goals']
                ) or (
                    row['club_id'] == ids['away_club_id'] and row['away_goals'] > row['home_goals']
                ):
                    expected = 'Win'
                else:
                    expected = 'Loss'
                assert row['result'] == expected

    def test_scheduled_match_row_is_labeled_scheduled(self, db):
        """If player is added to a scheduled match, status/result must be 'Scheduled'."""
        with db.cursor() as cur:
            cur.execute(
                """INSERT INTO Match_Participation
                   (match_id, player_id, club_id, is_starter, minutes_played,
                    position_in_match, goals, assists, yellow_cards, red_cards, rating)
                   VALUES (7, %s, 1, 1, 0, 'Forward', 0, 0, 0, 0, 5.0)""",
                (PLAYER_ID,),
            )
        db.commit()

        rows = _history(db, PLAYER_ID)
        row7 = next((r for r in rows if r['match_id'] == 7), None)
        assert row7 is not None
        assert row7['status'] == 'Scheduled'
        assert row7['result'] == 'Scheduled'
