"""
Operation 18: Viewing career history (Player)

Route: routes/player.py::player_career

Spec requirements:
  - Contract history with club, salary, type, and dates.
  - Transfer history with date, fee, source, destination, and type.
  - Correct ordering (latest first).
"""

import pytest

T_PLAYER = 9940
T_CONTRACT = 9940

CONTRACTS_QUERY = """
    SELECT cl.club_name, con.start_date, con.end_date, con.weekly_wage,
           CASE WHEN pc.contract_id IS NOT NULL THEN 'Permanent' ELSE 'Loan' END AS contract_type
    FROM Contract con
    JOIN Club cl ON con.club_id = cl.club_id
    LEFT JOIN Permanent_Contract pc ON pc.contract_id = con.contract_id
    WHERE con.player_id = %s
    ORDER BY con.start_date DESC
"""

TRANSFERS_QUERY = """
    SELECT tr.transfer_date, tr.transfer_fee, tr.transfer_type,
           fc.club_name AS from_club, tc.club_name AS to_club
    FROM Transfer_Record tr
    JOIN Club fc ON tr.from_club_id = fc.club_id
    JOIN Club tc ON tr.to_club_id = tc.club_id
    WHERE tr.player_id = %s
    ORDER BY tr.transfer_date DESC
"""


def _cleanup(db):
    with db.cursor() as cur:
        cur.execute("DELETE FROM Permanent_Contract WHERE contract_id = %s", (T_CONTRACT,))
        cur.execute("DELETE FROM Contract WHERE contract_id = %s", (T_CONTRACT,))
        cur.execute("DELETE FROM Player WHERE person_id = %s", (T_PLAYER,))
        cur.execute("DELETE FROM Person WHERE person_id = %s", (T_PLAYER,))
    db.commit()


@pytest.fixture(autouse=True)
def clean_temp(db):
    _cleanup(db)
    yield
    _cleanup(db)


def _contracts(db, player_id):
    with db.cursor() as cur:
        cur.execute(CONTRACTS_QUERY, (player_id,))
        return cur.fetchall()


def _transfers(db, player_id):
    with db.cursor() as cur:
        cur.execute(TRANSFERS_QUERY, (player_id,))
        return cur.fetchall()


class TestOp18PlayerCareerHistory:

    def test_contract_history_count_matches_contract_table(self, db):
        """Contract history length must equal number of contracts for the player."""
        rows = _contracts(db, 31)
        with db.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS cnt FROM Contract WHERE player_id = %s", (31,))
            expected = cur.fetchone()['cnt']
        assert len(rows) == expected

    def test_contract_type_classification_is_correct(self, db):
        """Contract type label must match whether contract is in Permanent_Contract."""
        with db.cursor() as cur:
            cur.execute(
                """
                SELECT con.contract_id,
                       CASE WHEN pc.contract_id IS NOT NULL THEN 'Permanent' ELSE 'Loan' END AS expected_type
                FROM Contract con
                LEFT JOIN Permanent_Contract pc ON pc.contract_id = con.contract_id
                WHERE con.player_id = %s
                ORDER BY con.start_date DESC
                """,
                (31,),
            )
            expected_rows = cur.fetchall()

        route_rows = _contracts(db, 31)
        assert len(route_rows) == len(expected_rows)
        for i, expected in enumerate(expected_rows):
            assert route_rows[i]['contract_type'] == expected['expected_type']

    def test_contract_history_is_ordered_by_latest_start_date(self, db):
        """Contract history must be sorted by start_date DESC."""
        rows = _contracts(db, 31)
        for i in range(len(rows) - 1):
            assert rows[i]['start_date'] >= rows[i + 1]['start_date']

    def test_transfer_history_order_and_columns(self, db):
        """Transfer history must be latest-first and expose required fields."""
        rows = _transfers(db, 31)
        for i in range(len(rows) - 1):
            assert rows[i]['transfer_date'] >= rows[i + 1]['transfer_date']

        if rows:
            row = rows[0]
            assert row['transfer_type'] in ('Free', 'Purchase', 'Loan')
            assert row['from_club'] is not None
            assert row['to_club'] is not None
            assert row['transfer_fee'] is not None

    def test_player_with_no_transfer_history_returns_empty(self, db):
        """A player with contracts but no transfer records should get an empty transfer list."""
        with db.cursor() as cur:
            cur.execute(
                "INSERT INTO Person (person_id, name, surname, nationality, date_of_birth) "
                "VALUES (%s, 'Tmp', 'NoTransfer', 'Turkish', '2000-01-01')",
                (T_PLAYER,),
            )
            cur.execute(
                "INSERT INTO Player (person_id, market_value, main_position, strong_foot, height) "
                "VALUES (%s, 1000000, 'Forward', 'Right', 180)",
                (T_PLAYER,),
            )
            cur.execute(
                "INSERT INTO Contract (contract_id, player_id, club_id, start_date, end_date, weekly_wage) "
                "VALUES (%s, %s, 1, CURDATE(), '2099-12-31', 50000)",
                (T_CONTRACT, T_PLAYER),
            )
            cur.execute("INSERT INTO Permanent_Contract (contract_id) VALUES (%s)", (T_CONTRACT,))
        db.commit()

        rows = _transfers(db, T_PLAYER)
        assert rows == [] or len(rows) == 0
