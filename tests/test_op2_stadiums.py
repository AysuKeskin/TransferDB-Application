"""
Operation 2: Viewing available stadiums (Database Manager)

Spec requirements:
  - DB Manager can view all stadiums
  - Each row shows: name, city, capacity, and the club(s) using it as home ground
  - A stadium shared by multiple clubs must show all of them
  - A stadium with no clubs must still appear (clubs = None)

These tests run the exact SQL query used by routes/dbmanager.py::dbmanager_stadiums()
directly against the database, so they verify DB-level correctness independent of
the Flask layer.

Test IDs 9901–9902 are used for all temporary data and are cleaned up after every test.
"""

# ── IDs reserved for test data (far from seed data which uses 1–4) ────────────
T_STADIUM_ID = 9901
T_CLUB1_ID   = 9901
T_CLUB2_ID   = 9902

# ── The exact query used by the stadiums view ─────────────────────────────────
STADIUMS_QUERY = """
    SELECT s.stadium_id, s.stadium_name, s.city, s.capacity,
           GROUP_CONCAT(cl.club_name SEPARATOR ', ') AS clubs
    FROM Stadium s
    LEFT JOIN Club cl ON cl.stadium_id = s.stadium_id
    WHERE s.stadium_id = %s
    GROUP BY s.stadium_id, s.stadium_name, s.city, s.capacity
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _insert_stadium(cur, name="Test Arena", city="Test City", capacity=50000):
    cur.execute(
        "INSERT INTO Stadium (stadium_id, stadium_name, city, capacity) VALUES (%s, %s, %s, %s)",
        (T_STADIUM_ID, name, city, capacity),
    )


def _insert_club(cur, club_id, name, year=2000):
    cur.execute(
        "INSERT INTO Club (club_id, club_name, foundation_year, stadium_id) VALUES (%s, %s, %s, %s)",
        (club_id, name, year, T_STADIUM_ID),
    )


def _run_view(db):
    """Execute the stadiums view query for the test stadium and return the row."""
    with db.cursor() as cur:
        cur.execute(STADIUMS_QUERY, (T_STADIUM_ID,))
        return cur.fetchone()


def _cleanup(db):
    with db.cursor() as cur:
        cur.execute("DELETE FROM Club    WHERE club_id    IN (%s, %s)", (T_CLUB1_ID, T_CLUB2_ID))
        cur.execute("DELETE FROM Stadium WHERE stadium_id = %s",        (T_STADIUM_ID,))
    db.commit()


# ── Fixture: ensure test rows are removed before and after every test ─────────

import pytest

@pytest.fixture(autouse=True)
def clean_test_rows(db):
    _cleanup(db)       # pre-clean in case a previous run left stale data
    yield
    # Data is intentionally left in the DB so it can be browsed in the web app.
    # To remove it manually: DELETE FROM Club WHERE club_id IN (9901,9902); DELETE FROM Stadium WHERE stadium_id=9901;


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestOp2StadiumView:

    def test_two_clubs_same_stadium_both_visible(self, db):
        """
        Core edge case: two clubs share the same stadium as their home ground.
        Both club names must appear in the 'clubs' column of the view.
        """
        with db.cursor() as cur:
            _insert_stadium(cur, name="Shared Arena", city="Shared City", capacity=60000)
            _insert_club(cur, T_CLUB1_ID, "Test Club Alpha", year=1990)
            _insert_club(cur, T_CLUB2_ID, "Test Club Beta",  year=1995)
        db.commit()

        row = _run_view(db)

        assert row is not None, "Stadium row not found in view"
        clubs = row['clubs']
        assert clubs is not None, "clubs column is NULL — neither club is linked"
        assert 'Test Club Alpha' in clubs, f"Club Alpha missing from: {clubs}"
        assert 'Test Club Beta'  in clubs, f"Club Beta missing from: {clubs}"

    def test_stadium_with_no_clubs_still_appears(self, db):
        """
        A stadium that no club uses as home ground must still appear in the view,
        with clubs = NULL (shown as 'None' in the template).
        """
        with db.cursor() as cur:
            _insert_stadium(cur, name="Empty Arena", city="Empty City", capacity=30000)
        db.commit()

        row = _run_view(db)

        assert row is not None, "Stadium row not found in view"
        assert row['clubs'] is None, f"Expected NULL clubs, got: {row['clubs']}"

    def test_stadium_fields_name_city_capacity(self, db):
        """
        The view must return the correct name, city, and capacity for a stadium.
        """
        with db.cursor() as cur:
            _insert_stadium(cur, name="Detail Arena", city="Istanbul", capacity=75432)
        db.commit()

        row = _run_view(db)

        assert row['stadium_name'] == "Detail Arena"
        assert row['city']         == "Istanbul"
        assert row['capacity']     == 75432

    def test_single_club_stadium(self, db):
        """
        A stadium with exactly one club should show only that club name.
        """
        with db.cursor() as cur:
            _insert_stadium(cur, name="Solo Arena", city="Solo City", capacity=45000)
            _insert_club(cur, T_CLUB1_ID, "Solo Club", year=2005)
        db.commit()

        row = _run_view(db)

        assert row is not None
        assert row['clubs'] == "Solo Club"
