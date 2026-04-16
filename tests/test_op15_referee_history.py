"""
Operation 15: Viewing referee match history (Referee)

Route: routes/referee.py::referee_history

Spec requirements:
  - Show chronological match record (latest first).
  - Include date/time, competition, stadium, attendance.
  - Include final result and total yellow/red cards issued.
  - Show "Scheduled" status for matches not yet played.
"""


ROUTE_QUERY = """
    SELECT m.match_id, m.match_datetime,
           m.home_goals, m.away_goals, m.attendance,
           CASE WHEN m.home_goals IS NOT NULL THEN 'Completed' ELSE 'Scheduled' END AS status,
           hc.club_name AS home_club, ac.club_name AS away_club,
           s.stadium_name, comp.name AS competition, comp.season,
           COALESCE((SELECT SUM(mp2.yellow_cards) FROM Match_Participation mp2
                     WHERE mp2.match_id = m.match_id), 0) AS total_yellow,
           COALESCE((SELECT SUM(mp2.red_cards) FROM Match_Participation mp2
                     WHERE mp2.match_id = m.match_id), 0) AS total_red
    FROM `Match` m
    JOIN Club hc ON m.home_club_id = hc.club_id
    JOIN Club ac ON m.away_club_id = ac.club_id
    JOIN Stadium s ON m.stadium_id = s.stadium_id
    JOIN Competition comp ON m.competition_id = comp.competition_id
    WHERE m.referee_id = %s
    ORDER BY m.match_datetime DESC
"""


def _history(db, referee_id):
    with db.cursor() as cur:
        cur.execute(ROUTE_QUERY, (referee_id,))
        return cur.fetchall()


class TestOp15RefereeHistory:

    def test_history_matches_referee_assignment_set(self, db):
        """History rows must correspond exactly to matches assigned to that referee."""
        rows = _history(db, 5)
        with db.cursor() as cur:
            cur.execute("SELECT match_id FROM `Match` WHERE referee_id = %s", (5,))
            expected_ids = {r['match_id'] for r in cur.fetchall()}

        row_ids = {r['match_id'] for r in rows}
        assert row_ids == expected_ids

    def test_status_label_matches_result_nullability(self, db):
        """Status must be Completed iff home_goals is not NULL, otherwise Scheduled."""
        rows = _history(db, 5)
        for row in rows:
            if row['home_goals'] is None:
                assert row['status'] == 'Scheduled'
            else:
                assert row['status'] == 'Completed'

    def test_card_totals_match_participation_aggregation(self, db):
        """Per-match total yellow/red in history must equal Match_Participation sums."""
        rows = _history(db, 5)
        with db.cursor() as cur:
            for row in rows:
                cur.execute(
                    """
                    SELECT COALESCE(SUM(yellow_cards), 0) AS y,
                           COALESCE(SUM(red_cards), 0) AS r
                    FROM Match_Participation
                    WHERE match_id = %s
                    """,
                    (row['match_id'],),
                )
                sums = cur.fetchone()
                assert row['total_yellow'] == sums['y']
                assert row['total_red'] == sums['r']

    def test_history_is_reverse_chronological(self, db):
        """Rows must be sorted by match_datetime DESC."""
        rows = _history(db, 5)
        for i in range(len(rows) - 1):
            assert rows[i]['match_datetime'] >= rows[i + 1]['match_datetime']

    def test_scheduled_rows_have_no_final_score(self, db):
        """Scheduled rows should not have final score values."""
        rows = _history(db, 5)
        for row in rows:
            if row['status'] == 'Scheduled':
                assert row['home_goals'] is None
                assert row['away_goals'] is None
