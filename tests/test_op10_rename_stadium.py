"""
Operation 10: Renaming a stadium (Database Manager)

Route: routes/dbmanager.py::dbmanager_rename_stadium

The DB Manager issues:
    UPDATE Stadium SET stadium_name = %s WHERE stadium_id = %s

Consistency requirement: because Club and Match reference stadium_id (not
stadium_name), any subsequent query that JOINs Stadium automatically reflects
the new name — there is a single source of truth.

Tests use a temporary stadium (id=9901) and, where needed, a temporary club
(id=9901) and match rows. All temp data is cleaned up before and after every
test.

Seed stadiums (ids 1-4) are only read, never mutated.
"""

import pytest
import pymysql

T_STADIUM_ID = 9901
T_CLUB_ID    = 9901


# ── Cleanup ────────────────────────────────────────────────────────────────────

def _cleanup(db):
    with db.cursor() as cur:
        cur.execute("DELETE FROM `Match` WHERE stadium_id = %s", (T_STADIUM_ID,))
        cur.execute("DELETE FROM Club    WHERE club_id    = %s", (T_CLUB_ID,))
        cur.execute("DELETE FROM Stadium WHERE stadium_id = %s", (T_STADIUM_ID,))
    db.commit()


@pytest.fixture(autouse=True)
def clean_temp(db):
    _cleanup(db)
    yield
    _cleanup(db)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _insert_stadium(db, name="Old Arena", city="Test City", capacity=50000):
    with db.cursor() as cur:
        cur.execute(
            "INSERT INTO Stadium (stadium_id, stadium_name, city, capacity) "
            "VALUES (%s, %s, %s, %s)",
            (T_STADIUM_ID, name, city, capacity),
        )
    db.commit()


def _rename_stadium(db, stadium_id, new_name):
    """Replicates the route's UPDATE statement."""
    with db.cursor() as cur:
        cur.execute(
            "UPDATE Stadium SET stadium_name = %s WHERE stadium_id = %s",
            (new_name, stadium_id),
        )
    db.commit()


def _get_stadium(db, stadium_id):
    with db.cursor() as cur:
        cur.execute("SELECT * FROM Stadium WHERE stadium_id = %s", (stadium_id,))
        return cur.fetchone()


# ── Tests ──────────────────────────────────────────────────────────────────────

class TestOp10RenameStadium:

    # ── Basic rename ───────────────────────────────────────────────────────────

    def test_rename_updates_stadium_name(self, db):
        """After renaming, Stadium.stadium_name reflects the new value."""
        _insert_stadium(db, name="Old Arena")
        _rename_stadium(db, T_STADIUM_ID, "New Arena")

        row = _get_stadium(db, T_STADIUM_ID)
        assert row is not None
        assert row['stadium_name'] == "New Arena"

    def test_rename_preserves_city_and_capacity(self, db):
        """Renaming must not alter city or capacity."""
        _insert_stadium(db, name="Old Arena", city="Istanbul", capacity=75000)
        _rename_stadium(db, T_STADIUM_ID, "New Arena")

        row = _get_stadium(db, T_STADIUM_ID)
        assert row['city']     == "Istanbul"
        assert row['capacity'] == 75000

    def test_rename_to_same_name_is_idempotent(self, db):
        """Updating to the same name must succeed and leave the row unchanged."""
        _insert_stadium(db, name="Stable Arena")
        _rename_stadium(db, T_STADIUM_ID, "Stable Arena")

        row = _get_stadium(db, T_STADIUM_ID)
        assert row['stadium_name'] == "Stable Arena"

    # ── Consistency: related records see the new name ──────────────────────────

    def test_club_join_reflects_new_stadium_name(self, db):
        """
        A Club linked to the stadium via stadium_id must expose the new name
        when JOINed — no data duplication, single source of truth.
        """
        _insert_stadium(db, name="Old Arena")
        with db.cursor() as cur:
            cur.execute(
                "INSERT INTO Club (club_id, club_name, foundation_year, stadium_id) "
                "VALUES (%s, 'Temp FC', 2000, %s)",
                (T_CLUB_ID, T_STADIUM_ID),
            )
        db.commit()

        _rename_stadium(db, T_STADIUM_ID, "Renamed Arena")

        with db.cursor() as cur:
            cur.execute(
                "SELECT s.stadium_name "
                "FROM Club c JOIN Stadium s ON s.stadium_id = c.stadium_id "
                "WHERE c.club_id = %s",
                (T_CLUB_ID,),
            )
            row = cur.fetchone()

        assert row is not None
        assert row['stadium_name'] == "Renamed Arena"

    def test_match_join_reflects_new_stadium_name(self, db):
        """
        Matches scheduled at the stadium must expose the new name when JOINed.
        Uses seed clubs (1, 2), competition (1), and referee (1) which are
        guaranteed to exist in the seed data.
        """
        _insert_stadium(db, name="Old Match Arena")

        with db.cursor() as cur:
            # Use MAX+1 to avoid colliding with seed matches
            cur.execute("SELECT COALESCE(MAX(match_id), 0) + 1 AS nid FROM `Match`")
            match_id = cur.fetchone()['nid']
            cur.execute(
                "INSERT INTO `Match` "
                "(match_id, competition_id, home_club_id, away_club_id, "
                " stadium_id, match_datetime, referee_id) "
                "VALUES (%s, 1, 1, 2, %s, '2030-08-01 20:00:00', 5)",
                (match_id, T_STADIUM_ID),
            )
        db.commit()

        _rename_stadium(db, T_STADIUM_ID, "New Match Arena")

        with db.cursor() as cur:
            cur.execute(
                "SELECT s.stadium_name "
                "FROM `Match` m JOIN Stadium s ON s.stadium_id = m.stadium_id "
                "WHERE m.match_id = %s",
                (match_id,),
            )
            row = cur.fetchone()

        assert row is not None
        assert row['stadium_name'] == "New Match Arena"

    # ── Constraint enforcement ─────────────────────────────────────────────────

    def test_rename_to_duplicate_name_same_city_rejected(self, db):
        """
        Stadium has a UNIQUE (stadium_name, city) constraint.
        Renaming to a (name, city) pair that already exists must be rejected.
        """
        _insert_stadium(db, name="Unique Arena", city="Madrid")
        # seed: stadium_id=1 has ('Santiago Bernabeu', 'Madrid')
        with pytest.raises(pymysql.Error):
            with db.cursor() as cur:
                cur.execute(
                    "UPDATE Stadium SET stadium_name = 'Santiago Bernabeu' "
                    "WHERE stadium_id = %s",
                    (T_STADIUM_ID,),
                )
            db.commit()
        db.rollback()

    def test_rename_same_name_different_city_allowed(self, db):
        """
        The UNIQUE constraint is on (stadium_name, city) together.
        Reusing a name that exists only in a *different* city must succeed.
        """
        # 'Santiago Bernabeu' exists in 'Madrid'; reuse name in a different city
        _insert_stadium(db, name="Placeholder", city="Barcelona")
        _rename_stadium(db, T_STADIUM_ID, "Santiago Bernabeu")  # different city → OK

        row = _get_stadium(db, T_STADIUM_ID)
        assert row['stadium_name'] == "Santiago Bernabeu"
        assert row['city']         == "Barcelona"

    def test_nonexistent_stadium_update_affects_zero_rows(self, db):
        """
        Trying to rename a stadium that doesn't exist must silently affect 0 rows
        (no error, but nothing changes).
        """
        with db.cursor() as cur:
            cur.execute(
                "UPDATE Stadium SET stadium_name = 'Ghost Arena' WHERE stadium_id = 99999"
            )
            affected = cur.rowcount
        db.commit()
        assert affected == 0
