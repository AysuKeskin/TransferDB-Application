"""
Operation 11: Managing club manager assignments (Database Manager)

Route: routes/dbmanager.py::dbmanager_assign_manager

The route enforces two business rules via three sequential UPDATEs:
  1. A manager can only manage one club at a time
  2. A club can only have one active manager at a time
  3. A club may legitimately have manager_id = NULL (no manager)

Route SQL (verbatim):
  UPDATE Club SET manager_id = NULL WHERE manager_id = %s   -- unassign from current club
  UPDATE Club SET manager_id = NULL WHERE club_id    = %s   -- clear target club's manager
  UPDATE Club SET manager_id = %s    WHERE club_id   = %s   -- assign

Schema constraints tested:
  Club.manager_id INT UNIQUE   – at most one club per manager; multiple NULLs allowed
  FK: manager_id → Manager(person_id)  ON DELETE SET NULL ON UPDATE CASCADE

Temp IDs:
  T_MANAGER_A = 9901, T_MANAGER_B = 9902  (Person + Manager)
  T_CLUB_A    = 9901, T_CLUB_B    = 9902  (Club, always using stadium_id=1)

Seed clubs 1–4 and managers 1–4 are never mutated.
"""

import pytest
import pymysql

T_MANAGER_A = 9901
T_MANAGER_B = 9902
T_CLUB_A    = 9901
T_CLUB_B    = 9902

_TEMP_PERSON_IDS = (T_MANAGER_A, T_MANAGER_B)
_TEMP_CLUB_IDS   = (T_CLUB_A,    T_CLUB_B)


# ── Cleanup ────────────────────────────────────────────────────────────────────

def _cleanup(db):
    with db.cursor() as cur:
        # FK-safe order: Club references Manager(person_id), so delete clubs first
        ids_c = ', '.join(['%s'] * len(_TEMP_CLUB_IDS))
        ids_p = ', '.join(['%s'] * len(_TEMP_PERSON_IDS))
        cur.execute(f"DELETE FROM Club    WHERE club_id    IN ({ids_c})", _TEMP_CLUB_IDS)
        cur.execute(f"DELETE FROM Manager WHERE person_id IN ({ids_p})", _TEMP_PERSON_IDS)
        cur.execute(f"DELETE FROM Person  WHERE person_id IN ({ids_p})", _TEMP_PERSON_IDS)
    db.commit()


@pytest.fixture(autouse=True)
def clean_temp(db):
    _cleanup(db)
    yield
    _cleanup(db)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _insert_manager(db, pid, name='TmpMgr', surname=None):
    if surname is None:
        surname = f'Sur{pid}'
    with db.cursor() as cur:
        cur.execute(
            "INSERT INTO Person (person_id, name, surname, nationality, date_of_birth) "
            "VALUES (%s, %s, %s, 'Turkish', '1970-01-01')",
            (pid, name, surname),
        )
        cur.execute(
            "INSERT INTO Manager (person_id, preferred_formation, experience_level) "
            "VALUES (%s, '4-3-3', 'Senior')",
            (pid,),
        )
    db.commit()


def _insert_club(db, club_id, name, manager_id=None):
    with db.cursor() as cur:
        cur.execute(
            "INSERT INTO Club (club_id, club_name, foundation_year, stadium_id, manager_id) "
            "VALUES (%s, %s, 2000, 1, %s)",
            (club_id, name, manager_id),
        )
    db.commit()


def _assign_manager(db, manager_id, club_id):
    """Replicates the route's three-step assignment logic."""
    with db.cursor() as cur:
        cur.execute("UPDATE Club SET manager_id = NULL WHERE manager_id = %s", (manager_id,))
        cur.execute("UPDATE Club SET manager_id = NULL WHERE club_id    = %s", (club_id,))
        cur.execute("UPDATE Club SET manager_id = %s   WHERE club_id   = %s", (manager_id, club_id))
    db.commit()


def _get_club(db, club_id):
    with db.cursor() as cur:
        cur.execute("SELECT * FROM Club WHERE club_id = %s", (club_id,))
        return cur.fetchone()


# ── Tests ──────────────────────────────────────────────────────────────────────

class TestOp11AssignManager:

    # ── Happy paths ────────────────────────────────────────────────────────────

    def test_basic_assignment(self, db):
        """
        Simplest happy path: unassigned manager assigned to a club that has no manager.
        Club.manager_id must be set to the manager's person_id.
        """
        _insert_manager(db, T_MANAGER_A)
        _insert_club(db, T_CLUB_A, 'Temp Club A', manager_id=None)

        _assign_manager(db, T_MANAGER_A, T_CLUB_A)

        row = _get_club(db, T_CLUB_A)
        assert row is not None
        assert row['manager_id'] == T_MANAGER_A

    def test_manager_moves_clubs_old_club_loses_manager(self, db):
        """
        Manager A is currently at Club A, then assigned to Club B.
        Club A must become unmanaged; Club B must acquire Manager A.
        """
        _insert_manager(db, T_MANAGER_A)
        _insert_club(db, T_CLUB_A, 'Temp Club A', manager_id=T_MANAGER_A)
        _insert_club(db, T_CLUB_B, 'Temp Club B', manager_id=None)

        _assign_manager(db, T_MANAGER_A, T_CLUB_B)

        club_a = _get_club(db, T_CLUB_A)
        club_b = _get_club(db, T_CLUB_B)
        assert club_b['manager_id'] == T_MANAGER_A, "Club B must now have Manager A"
        assert club_a['manager_id'] is None,         "Club A must be unmanaged after manager left"

    def test_club_displaces_existing_manager(self, db):
        """
        Club A has Manager A. Assign unassigned Manager B to Club A.
        Manager A must become free; Club A must now have Manager B.
        """
        _insert_manager(db, T_MANAGER_A)
        _insert_manager(db, T_MANAGER_B)
        _insert_club(db, T_CLUB_A, 'Temp Club A', manager_id=T_MANAGER_A)

        _assign_manager(db, T_MANAGER_B, T_CLUB_A)

        club_a = _get_club(db, T_CLUB_A)
        assert club_a['manager_id'] == T_MANAGER_B, "Club A must now have Manager B"

        with db.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS cnt FROM Club WHERE manager_id = %s", (T_MANAGER_A,))
            cnt = cur.fetchone()['cnt']
        assert cnt == 0, "Manager A must not be assigned to any club after displacement"

    def test_both_sides_reassigned_simultaneously(self, db):
        """
        Manager A at Club A, Manager B at Club B.
        Assign Manager A to Club B (the most complex scenario):
          - Step 1 clears A from Club A  → Club A becomes NULL
          - Step 2 clears B from Club B  → Club B becomes NULL (B is now free)
          - Step 3 sets A on Club B      → Club B gets A

        Expected final state:
          Club A: manager_id = NULL
          Club B: manager_id = A
          Manager B: not assigned to any club
        """
        _insert_manager(db, T_MANAGER_A)
        _insert_manager(db, T_MANAGER_B)
        _insert_club(db, T_CLUB_A, 'Temp Club A', manager_id=T_MANAGER_A)
        _insert_club(db, T_CLUB_B, 'Temp Club B', manager_id=T_MANAGER_B)

        _assign_manager(db, T_MANAGER_A, T_CLUB_B)

        club_a = _get_club(db, T_CLUB_A)
        club_b = _get_club(db, T_CLUB_B)
        assert club_b['manager_id'] == T_MANAGER_A, "Club B must have Manager A"
        assert club_a['manager_id'] is None,         "Club A must be unmanaged"

        with db.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS cnt FROM Club WHERE manager_id = %s", (T_MANAGER_B,))
            cnt = cur.fetchone()['cnt']
        assert cnt == 0, "Manager B must not be assigned to any club"

    # ── NULL / no-manager validity ─────────────────────────────────────────────

    def test_club_can_be_left_without_manager(self, db):
        """
        A club with manager_id=NULL is a valid persisted state, not just transient.
        The nullable column must accept and return NULL.
        """
        _insert_club(db, T_CLUB_A, 'Temp Club A', manager_id=None)

        row = _get_club(db, T_CLUB_A)
        assert row is not None
        assert row['manager_id'] is None

    def test_multiple_clubs_with_null_manager_allowed(self, db):
        """
        UNIQUE constraint on Club.manager_id must permit multiple NULL values
        (SQL standard: NULLs are not considered duplicates for UNIQUE).
        Both clubs inserted with manager_id=NULL must coexist without error.
        """
        _insert_club(db, T_CLUB_A, 'Temp Club A', manager_id=None)
        _insert_club(db, T_CLUB_B, 'Temp Club B', manager_id=None)

        with db.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS cnt FROM Club "
                "WHERE club_id IN (%s, %s) AND manager_id IS NULL",
                (T_CLUB_A, T_CLUB_B),
            )
            cnt = cur.fetchone()['cnt']
        assert cnt == 2, "Both clubs with NULL manager_id must exist"

    # ── Constraint enforcement ─────────────────────────────────────────────────

    def test_fk_violation_nonexistent_manager_rejected(self, db):
        """
        Assigning manager_id to a person_id that does not exist in Manager
        must be rejected by the FK constraint (errno 1452).
        After rollback, the club must remain unchanged.
        """
        _insert_club(db, T_CLUB_A, 'Temp Club A', manager_id=None)
        GHOST_ID = 9903  # never inserted into Person or Manager

        with pytest.raises(pymysql.Error):
            with db.cursor() as cur:
                cur.execute(
                    "UPDATE Club SET manager_id = %s WHERE club_id = %s",
                    (GHOST_ID, T_CLUB_A),
                )
            db.commit()
        db.rollback()

        row = _get_club(db, T_CLUB_A)
        assert row['manager_id'] is None, "Club must remain unmanaged after FK rejection"

    def test_unique_constraint_prevents_direct_duplicate_manager_id(self, db):
        """
        If the 3-step unassign logic is bypassed and the same manager_id is directly
        written to a second club, the UNIQUE constraint must reject it (errno 1062).
        Both clubs must remain in their original state after rollback.
        """
        _insert_manager(db, T_MANAGER_A)
        _insert_club(db, T_CLUB_A, 'Temp Club A', manager_id=T_MANAGER_A)
        _insert_club(db, T_CLUB_B, 'Temp Club B', manager_id=None)

        with pytest.raises(pymysql.Error) as exc_info:
            with db.cursor() as cur:
                # Skip step 1 (the unassign) — directly set the same manager on club B
                cur.execute(
                    "UPDATE Club SET manager_id = %s WHERE club_id = %s",
                    (T_MANAGER_A, T_CLUB_B),
                )
            db.commit()
        db.rollback()

        # Duplicate-entry error
        assert '1062' in str(exc_info.value) or 'Duplicate' in str(exc_info.value)

        club_a = _get_club(db, T_CLUB_A)
        club_b = _get_club(db, T_CLUB_B)
        assert club_a['manager_id'] == T_MANAGER_A, "Club A must still have Manager A"
        assert club_b['manager_id'] is None,         "Club B must remain unmanaged"

    # ── Join-query consistency ─────────────────────────────────────────────────

    def test_join_query_reflects_assignment(self, db):
        """
        After assignment, the route's manager-list JOIN query must return the
        correct manager name and their current club name.
        """
        _insert_manager(db, T_MANAGER_A, name='Test', surname='Mgr')
        _insert_club(db, T_CLUB_A, 'Temp Club A', manager_id=None)

        _assign_manager(db, T_MANAGER_A, T_CLUB_A)

        # Mirror the route's SELECT (routes/dbmanager.py, manager list query)
        with db.cursor() as cur:
            cur.execute(
                """
                SELECT m.person_id, p.name, p.surname,
                       cl.club_name AS current_club
                FROM Manager m
                JOIN Person p ON m.person_id = p.person_id
                LEFT JOIN Club cl ON cl.manager_id = m.person_id
                WHERE m.person_id = %s
                """,
                (T_MANAGER_A,),
            )
            row = cur.fetchone()

        assert row is not None
        assert row['name']         == 'Test'
        assert row['surname']      == 'Mgr'
        assert row['current_club'] == 'Temp Club A'
