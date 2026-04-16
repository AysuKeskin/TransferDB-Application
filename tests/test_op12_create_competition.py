"""
Operation 12: Creating a competition (Database Manager)

Route: routes/dbmanager.py::dbmanager_create_competition

Route behavior:
  - Generates competition_id via MAX+1
  - Inserts (name, season, country, competition_type)

Schema constraints tested:
  - UNIQUE (name, season)
  - CHECK competition_type IN ('League', 'Cup', 'International')

Spec requirement:
  - The exact same competition cannot run twice in one season.
"""

import pytest
import pymysql


def _cleanup(db):
    with db.cursor() as cur:
        cur.execute("DELETE FROM Competition WHERE name LIKE 'TMP_OP12_%'")
    db.commit()


@pytest.fixture(autouse=True)
def clean_temp(db):
    _cleanup(db)
    yield
    _cleanup(db)


def _create_competition(db, name, season, country, comp_type):
    """Replicates the route's MAX+1 id generation and INSERT."""
    with db.cursor() as cur:
        cur.execute("SELECT COALESCE(MAX(competition_id), 0) + 1 AS nid FROM Competition")
        nid = cur.fetchone()['nid']
        cur.execute(
            """INSERT INTO Competition
               (competition_id, name, season, country, competition_type)
               VALUES (%s, %s, %s, %s, %s)""",
            (nid, name, season, country, comp_type),
        )
    db.commit()
    return nid


def _get_competition(db, competition_id):
    with db.cursor() as cur:
        cur.execute("SELECT * FROM Competition WHERE competition_id = %s", (competition_id,))
        return cur.fetchone()


class TestOp12CreateCompetition:

    def test_create_competition_happy_path(self, db):
        """Valid input must create a competition row with correct values."""
        comp_id = _create_competition(
            db,
            name='TMP_OP12_Premier Test',
            season='2030/2031',
            country='Testland',
            comp_type='League',
        )

        row = _get_competition(db, comp_id)
        assert row is not None
        assert row['name'] == 'TMP_OP12_Premier Test'
        assert row['season'] == '2030/2031'
        assert row['country'] == 'Testland'
        assert row['competition_type'] == 'League'

    def test_unique_name_season_rejected(self, db):
        """
        (name, season) must be unique.
        Inserting the exact same pair twice must fail.
        """
        _create_competition(db, 'TMP_OP12_Duplicate', '2031/2032', 'Testland', 'Cup')

        with pytest.raises(pymysql.Error) as exc_info:
            _create_competition(db, 'TMP_OP12_Duplicate', '2031/2032', 'Testland', 'Cup')
        db.rollback()

        msg = str(exc_info.value)
        assert (
            '1062' in msg
            or 'Duplicate' in msg
            or '1644' in msg
            or 'already exists' in msg
        )

    def test_same_name_different_season_allowed(self, db):
        """Same competition name in a different season must be allowed."""
        _create_competition(db, 'TMP_OP12_SameName', '2032/2033', 'Testland', 'League')
        _create_competition(db, 'TMP_OP12_SameName', '2033/2034', 'Testland', 'League')

        with db.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS cnt FROM Competition WHERE name = 'TMP_OP12_SameName'"
            )
            cnt = cur.fetchone()['cnt']
        assert cnt == 2

    def test_different_name_same_season_allowed(self, db):
        """Different names in the same season must be allowed."""
        _create_competition(db, 'TMP_OP12_CupA', '2034/2035', 'Testland', 'Cup')
        _create_competition(db, 'TMP_OP12_CupB', '2034/2035', 'Testland', 'International')

        with db.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS cnt FROM Competition WHERE season = '2034/2035' AND name LIKE 'TMP_OP12_%'"
            )
            cnt = cur.fetchone()['cnt']
        assert cnt == 2

    def test_invalid_competition_type_rejected(self, db):
        """Invalid competition type must be rejected by the DB CHECK constraint."""
        with pytest.raises(pymysql.Error):
            _create_competition(
                db,
                name='TMP_OP12_InvalidType',
                season='2035/2036',
                country='Testland',
                comp_type='Friendly',
            )
        db.rollback()
