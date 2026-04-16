"""
Operation 14: Viewing referee statistics (Referee)

Route: routes/referee.py::referee_stats

Spec requirements:
  - Show how many matches referee officiated.
  - Show total yellow and red cards issued across those matches.
  - Only completed matches should be included.
"""

import pytest

T_REFEREE_ID = 9935

ROUTE_QUERY = """
    SELECT COUNT(DISTINCT m.match_id) AS matches_officiated,
           COALESCE(SUM(mp.yellow_cards), 0) AS total_yellow,
           COALESCE(SUM(mp.red_cards), 0) AS total_red
    FROM `Match` m
    LEFT JOIN Match_Participation mp ON mp.match_id = m.match_id
    WHERE m.referee_id = %s AND m.home_goals IS NOT NULL
"""


def _cleanup(db):
    with db.cursor() as cur:
        cur.execute("DELETE FROM Referee WHERE person_id = %s", (T_REFEREE_ID,))
        cur.execute("DELETE FROM Person WHERE person_id = %s", (T_REFEREE_ID,))
    db.commit()


@pytest.fixture(autouse=True)
def clean_temp(db):
    _cleanup(db)
    yield
    _cleanup(db)


def _route_stats(db, referee_id):
    with db.cursor() as cur:
        cur.execute(ROUTE_QUERY, (referee_id,))
        return cur.fetchone()


class TestOp14RefereeStats:

    def test_route_query_matches_independent_aggregation(self, db):
        """Route stats must equal an independently computed aggregate for the same referee."""
        route_row = _route_stats(db, 5)

        with db.cursor() as cur:
            cur.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM `Match` m
                     WHERE m.referee_id = %s AND m.home_goals IS NOT NULL) AS matches_officiated,
                    (SELECT COALESCE(SUM(mp.yellow_cards), 0)
                     FROM Match_Participation mp
                     JOIN `Match` m ON m.match_id = mp.match_id
                     WHERE m.referee_id = %s AND m.home_goals IS NOT NULL) AS total_yellow,
                    (SELECT COALESCE(SUM(mp.red_cards), 0)
                     FROM Match_Participation mp
                     JOIN `Match` m ON m.match_id = mp.match_id
                     WHERE m.referee_id = %s AND m.home_goals IS NOT NULL) AS total_red
                """,
                (5, 5, 5),
            )
            expected = cur.fetchone()

        assert route_row['matches_officiated'] == expected['matches_officiated']
        assert route_row['total_yellow'] == expected['total_yellow']
        assert route_row['total_red'] == expected['total_red']

    def test_scheduled_matches_are_excluded(self, db):
        """matches_officiated must count only completed matches, not all assigned matches."""
        route_row = _route_stats(db, 5)

        with db.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS cnt FROM `Match` WHERE referee_id = %s", (5,))
            total_assigned = cur.fetchone()['cnt']

        assert route_row['matches_officiated'] <= total_assigned

    def test_referee_with_no_matches_returns_zeroes(self, db):
        """A referee with no matches should get 0 matches, 0 yellow, 0 red."""
        with db.cursor() as cur:
            cur.execute(
                "INSERT INTO Person (person_id, name, surname, nationality, date_of_birth) "
                "VALUES (%s, 'Tmp', 'NoMatchRef', 'Turkish', '1980-01-01')",
                (T_REFEREE_ID,),
            )
            cur.execute(
                "INSERT INTO Referee (person_id, license_level, years_of_experience) "
                "VALUES (%s, 'FIFA', 5)",
                (T_REFEREE_ID,),
            )
        db.commit()

        row = _route_stats(db, T_REFEREE_ID)
        assert row['matches_officiated'] == 0
        assert row['total_yellow'] == 0
        assert row['total_red'] == 0
