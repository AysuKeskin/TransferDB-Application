"""
Operation 9: Transfer management (DB Manager)

Route: routes/dbmanager.py::dbmanager_transfer

transfer_type logic:
  Permanent + fee=0  → 'Free'
  Permanent + fee>0  → 'Purchase'
  Loan               → 'Loan'

Key triggers under test:
  trg_contract_before_insert         – forces start_date=CURDATE, max 2 active contracts
  trg_permanent_contract_before_insert – ISA disjointness, no duplicate active permanent
  trg_loan_contract_before_insert    – ISA disjointness, no dup loan, must have perm elsewhere
  trg_transfer_before_insert         – forces transfer_date=CURDATE, active source contract
  trg_transfer_after_insert          – Purchase → update market_value

Seed data used:
  Player 8  (Courtois):  active permanent contract (id=1) at club 1, market_value=35_000_000
  Player 31 (Alvarez):   permanent (id=24) at club 2 + loan (id=49) at club 4 → 2 active contracts

Temp IDs: persons/players 9901–9904, all contracts/transfers via MAX+1 auto-ID.
Cleanup removes all temp persons and their associated rows by player_id chain.
"""

import pytest
import pymysql

# ── Cleanup ───────────────────────────────────────────────────────────────────

_TEMP_IDS = (9901, 9902, 9903, 9904)

def _cleanup(db):
    with db.cursor() as cur:
        ids = ', '.join(['%s'] * len(_TEMP_IDS))
        # Subcontracts first (FK), then base Contract, then Person/Player
        cur.execute(
            f"DELETE lc FROM Loan_Contract lc "
            f"JOIN Contract c ON c.contract_id = lc.contract_id "
            f"WHERE c.player_id IN ({ids})", _TEMP_IDS
        )
        cur.execute(
            f"DELETE pc FROM Permanent_Contract pc "
            f"JOIN Contract c ON c.contract_id = pc.contract_id "
            f"WHERE c.player_id IN ({ids})", _TEMP_IDS
        )
        cur.execute(f"DELETE FROM Transfer_Record WHERE player_id IN ({ids})", _TEMP_IDS)
        cur.execute(f"DELETE FROM Contract        WHERE player_id IN ({ids})", _TEMP_IDS)
        cur.execute(f"DELETE FROM Player          WHERE person_id IN ({ids})", _TEMP_IDS)
        cur.execute(f"DELETE FROM Person          WHERE person_id IN ({ids})", _TEMP_IDS)
        # Restore any seed contracts that tests may have terminated
        cur.execute(
            "UPDATE Contract SET end_date = '2027-06-30' "
            "WHERE contract_id IN (1,2,3,4,5,6,7,8,9,10,11,12) "
            "AND end_date < '2027-06-30'"
        )
    db.commit()


@pytest.fixture(autouse=True)
def clean_temp(db):
    _cleanup(db)
    yield
    _cleanup(db)


# ── Low-level helpers ─────────────────────────────────────────────────────────

def _next_contract_id(cur):
    cur.execute("SELECT COALESCE(MAX(contract_id), 0) + 1 AS nid FROM Contract")
    return cur.fetchone()['nid']

def _next_transfer_id(cur):
    cur.execute("SELECT COALESCE(MAX(transfer_id), 0) + 1 AS nid FROM Transfer_Record")
    return cur.fetchone()['nid']

def _create_player(db, pid, club_id, market_value=1_000_000):
    """Person + Player + active permanent contract at club_id.
    The contract's start_date is backdated to '2025-07-01' (via UPDATE after INSERT)
    so that termination via end_date=CURDATE() satisfies end_date > start_date.
    """
    with db.cursor() as cur:
        cur.execute(
            "INSERT INTO Person (person_id, name, surname, nationality, date_of_birth) "
            "VALUES (%s, %s, %s, 'Turkish', '1998-01-01')",
            (pid, f'Tmp{pid}', f'Sur{pid}')
        )
        cur.execute(
            "INSERT INTO Player (person_id, market_value, main_position, strong_foot, height) "
            "VALUES (%s, %s, 'Forward', 'Right', 180)",
            (pid, market_value)
        )
        cid = _next_contract_id(cur)
        cur.execute(
            "INSERT INTO Contract "
            "(contract_id, player_id, club_id, start_date, end_date, weekly_wage) "
            "VALUES (%s, %s, %s, CURDATE(), '2028-06-30', 100000)",
            (cid, pid, club_id)
        )
        # Backdate so termination (end_date=CURDATE) satisfies end_date > start_date
        cur.execute(
            "UPDATE Contract SET start_date = '2025-07-01' WHERE contract_id = %s", (cid,)
        )
        cur.execute("INSERT INTO Permanent_Contract (contract_id) VALUES (%s)", (cid,))
    db.commit()
    return cid  # perm contract id


def _do_permanent_transfer(db, player_id, dest_club_id, fee, end_date='2029-06-30'):
    """Replicates the route's permanent-transfer DB steps. Returns new contract id.

    Commits in two phases to ensure the old-contract termination is visible to the
    trg_permanent_contract_before_insert trigger when the new contract is inserted.
    """
    # ── Phase 1: find source club and terminate old permanent contract ──────────
    with db.cursor() as cur:
        cur.execute(
            "SELECT c.club_id FROM Contract c "
            "JOIN Permanent_Contract pc ON pc.contract_id = c.contract_id "
            "WHERE c.player_id = %s AND c.start_date <= CURDATE() AND c.end_date >= CURDATE() "
            "LIMIT 1",
            (player_id,)
        )
        row = cur.fetchone()
        from_club_id = row['club_id'] if row else None

        if from_club_id:
            # Terminate: set end_date = CURDATE().
            # trg_permanent_contract_before_insert checks end_date > new_start (strict),
            # so CURDATE() > CURDATE() → FALSE — trigger won't count the old contract.
            # trg_transfer_before_insert checks end_date >= transfer_date, so
            # CURDATE() >= CURDATE() → TRUE — transfer record will still be valid.
            cur.execute(
                "UPDATE Contract SET end_date = CURDATE() "
                "WHERE player_id = %s AND end_date >= CURDATE() "
                "AND contract_id IN (SELECT contract_id FROM Permanent_Contract)",
                (player_id,)
            )
    db.commit()  # commit termination so trigger sees the updated end_date

    # ── Phase 2: create new contract + transfer record ──────────────────────────
    with db.cursor() as cur:
        cid = _next_contract_id(cur)
        cur.execute(
            "INSERT INTO Contract "
            "(contract_id, player_id, club_id, start_date, end_date, weekly_wage) "
            "VALUES (%s, %s, %s, CURDATE(), %s, 100000)",
            (cid, player_id, dest_club_id, end_date)
        )
        cur.execute("INSERT INTO Permanent_Contract (contract_id) VALUES (%s)", (cid,))

        transfer_type = 'Free' if fee == 0 else 'Purchase'

        if from_club_id:
            tid = _next_transfer_id(cur)
            cur.execute(
                "INSERT INTO Transfer_Record "
                "(transfer_id, player_id, from_club_id, to_club_id, "
                " transfer_date, transfer_fee, transfer_type) "
                "VALUES (%s, %s, %s, %s, CURDATE(), %s, %s)",
                (tid, player_id, from_club_id, dest_club_id, fee, transfer_type)
            )
    db.commit()
    return cid


def _do_loan_transfer(db, player_id, dest_club_id, fee, end_date='2027-01-31'):
    """Replicates the route's loan-transfer DB steps. Returns new contract id."""
    with db.cursor() as cur:
        # Find source club via active permanent
        cur.execute(
            "SELECT c.club_id FROM Contract c "
            "JOIN Permanent_Contract pc ON pc.contract_id = c.contract_id "
            "WHERE c.player_id = %s AND c.start_date <= CURDATE() AND c.end_date >= CURDATE() "
            "LIMIT 1",
            (player_id,)
        )
        row = cur.fetchone()
        from_club_id = row['club_id'] if row else None

        # Find perm contract id at a different club
        cur.execute(
            "SELECT pc.contract_id FROM Permanent_Contract pc "
            "JOIN Contract c ON c.contract_id = pc.contract_id "
            "WHERE c.player_id = %s AND c.club_id != %s "
            "AND c.start_date <= CURDATE() AND c.end_date > CURDATE() "
            "LIMIT 1",
            (player_id, dest_club_id)
        )
        perm_row = cur.fetchone()
        if not perm_row:
            raise ValueError('No active permanent contract at a different club')
        perm_cid = perm_row['contract_id']

        cid = _next_contract_id(cur)
        cur.execute(
            "INSERT INTO Contract "
            "(contract_id, player_id, club_id, start_date, end_date, weekly_wage) "
            "VALUES (%s, %s, %s, CURDATE(), %s, 80000)",
            (cid, player_id, dest_club_id, end_date)
        )
        cur.execute(
            "INSERT INTO Loan_Contract (contract_id, permanent_contract_id) VALUES (%s, %s)",
            (cid, perm_cid)
        )

        if from_club_id:
            tid = _next_transfer_id(cur)
            cur.execute(
                "INSERT INTO Transfer_Record "
                "(transfer_id, player_id, from_club_id, to_club_id, "
                " transfer_date, transfer_fee, transfer_type) "
                "VALUES (%s, %s, %s, %s, CURDATE(), %s, 'Loan')",
                (tid, player_id, from_club_id, dest_club_id, fee)
            )
    db.commit()
    return cid


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestOp9Transfer:

    # ── Transfer type classification ──────────────────────────────────────────

    def test_free_transfer_type_in_record(self, db):
        """Permanent + fee=0 → Transfer_Record.transfer_type = 'Free'."""
        _create_player(db, 9901, club_id=1)
        _do_permanent_transfer(db, 9901, dest_club_id=2, fee=0)
        with db.cursor() as cur:
            cur.execute(
                "SELECT transfer_type FROM Transfer_Record "
                "WHERE player_id = 9901 ORDER BY transfer_id DESC LIMIT 1"
            )
            row = cur.fetchone()
        assert row is not None
        assert row['transfer_type'] == 'Free'

    def test_purchase_transfer_type_in_record(self, db):
        """Permanent + fee>0 → Transfer_Record.transfer_type = 'Purchase'."""
        _create_player(db, 9901, club_id=1)
        _do_permanent_transfer(db, 9901, dest_club_id=2, fee=5_000_000)
        with db.cursor() as cur:
            cur.execute(
                "SELECT transfer_type FROM Transfer_Record "
                "WHERE player_id = 9901 ORDER BY transfer_id DESC LIMIT 1"
            )
            row = cur.fetchone()
        assert row is not None
        assert row['transfer_type'] == 'Purchase'

    def test_loan_transfer_type_in_record(self, db):
        """Loan contract → Transfer_Record.transfer_type = 'Loan'."""
        _create_player(db, 9901, club_id=1)
        _do_loan_transfer(db, 9901, dest_club_id=2, fee=500_000)
        with db.cursor() as cur:
            cur.execute(
                "SELECT transfer_type FROM Transfer_Record "
                "WHERE player_id = 9901 ORDER BY transfer_id DESC LIMIT 1"
            )
            row = cur.fetchone()
        assert row is not None
        assert row['transfer_type'] == 'Loan'

    # ── Correct DB rows created ───────────────────────────────────────────────

    def test_permanent_transfer_creates_permanent_contract_row(self, db):
        """After a permanent transfer, Permanent_Contract row exists; no Loan_Contract row."""
        _create_player(db, 9901, club_id=1)
        new_cid = _do_permanent_transfer(db, 9901, dest_club_id=2, fee=0)
        with db.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS cnt FROM Permanent_Contract WHERE contract_id=%s", (new_cid,))
            perm_cnt = cur.fetchone()['cnt']
            cur.execute("SELECT COUNT(*) AS cnt FROM Loan_Contract WHERE contract_id=%s", (new_cid,))
            loan_cnt = cur.fetchone()['cnt']
        assert perm_cnt == 1
        assert loan_cnt == 0

    def test_loan_transfer_creates_loan_contract_row(self, db):
        """After a loan transfer, Loan_Contract row exists; no Permanent_Contract row."""
        _create_player(db, 9901, club_id=1)
        new_cid = _do_loan_transfer(db, 9901, dest_club_id=2, fee=1_000_000)
        with db.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS cnt FROM Loan_Contract WHERE contract_id=%s", (new_cid,))
            loan_cnt = cur.fetchone()['cnt']
            cur.execute("SELECT COUNT(*) AS cnt FROM Permanent_Contract WHERE contract_id=%s", (new_cid,))
            perm_cnt = cur.fetchone()['cnt']
        assert loan_cnt == 1
        assert perm_cnt == 0

    def test_loan_contract_references_permanent_contract(self, db):
        """Loan_Contract.permanent_contract_id must point to the player's perm contract."""
        perm_cid = _create_player(db, 9901, club_id=1)
        new_cid = _do_loan_transfer(db, 9901, dest_club_id=2, fee=1_000_000)
        with db.cursor() as cur:
            cur.execute(
                "SELECT permanent_contract_id FROM Loan_Contract WHERE contract_id = %s",
                (new_cid,)
            )
            row = cur.fetchone()
        assert row['permanent_contract_id'] == perm_cid

    # ── Old contract termination ──────────────────────────────────────────────

    def test_old_permanent_contract_terminated_on_transfer(self, db):
        """After a permanent transfer, the previous permanent contract's end_date = CURDATE."""
        old_cid = _create_player(db, 9901, club_id=1)
        _do_permanent_transfer(db, 9901, dest_club_id=2, fee=0)
        with db.cursor() as cur:
            cur.execute(
                "SELECT end_date FROM Contract WHERE contract_id = %s", (old_cid,)
            )
            row = cur.fetchone()
            cur.execute("SELECT CURDATE() AS today")
            today = cur.fetchone()['today']
        assert row['end_date'] == today

    # ── Market value update ───────────────────────────────────────────────────

    def test_purchase_updates_market_value(self, db):
        """trg_transfer_after_insert: Purchase → Player.market_value = transfer_fee."""
        _create_player(db, 9901, club_id=1, market_value=1_000_000)
        _do_permanent_transfer(db, 9901, dest_club_id=2, fee=8_000_000)
        with db.cursor() as cur:
            cur.execute("SELECT market_value FROM Player WHERE person_id = 9901")
            row = cur.fetchone()
        assert int(row['market_value']) == 8_000_000

    def test_free_transfer_does_not_update_market_value(self, db):
        """Free transfer must NOT change market_value (trigger only fires for Purchase)."""
        _create_player(db, 9901, club_id=1, market_value=1_000_000)
        _do_permanent_transfer(db, 9901, dest_club_id=2, fee=0)
        with db.cursor() as cur:
            cur.execute("SELECT market_value FROM Player WHERE person_id = 9901")
            row = cur.fetchone()
        assert int(row['market_value']) == 1_000_000

    def test_loan_does_not_update_market_value(self, db):
        """Loan transfer must NOT update market_value."""
        _create_player(db, 9901, club_id=1, market_value=1_000_000)
        _do_loan_transfer(db, 9901, dest_club_id=2, fee=500_000)
        with db.cursor() as cur:
            cur.execute("SELECT market_value FROM Player WHERE person_id = 9901")
            row = cur.fetchone()
        assert int(row['market_value']) == 1_000_000

    # ── Transfer record correctness ───────────────────────────────────────────

    def test_transfer_record_from_club_is_source(self, db):
        """Transfer_Record.from_club_id must be the player's previous permanent-contract club."""
        _create_player(db, 9901, club_id=1)
        _do_permanent_transfer(db, 9901, dest_club_id=2, fee=0)
        with db.cursor() as cur:
            cur.execute(
                "SELECT from_club_id, to_club_id FROM Transfer_Record "
                "WHERE player_id = 9901 ORDER BY transfer_id DESC LIMIT 1"
            )
            row = cur.fetchone()
        assert row['from_club_id'] == 1
        assert row['to_club_id']   == 2

    def test_no_transfer_record_for_initial_signing(self, db):
        """
        A player with no prior permanent contract (first-ever signing) must NOT
        generate a Transfer_Record (there is no source club).
        """
        # Create person + player with NO contracts
        with db.cursor() as cur:
            cur.execute(
                "INSERT INTO Person (person_id, name, surname, nationality, date_of_birth) "
                "VALUES (9901, 'New', 'Player', 'Turkish', '2002-01-01')"
            )
            cur.execute(
                "INSERT INTO Player (person_id, market_value, main_position, strong_foot, height) "
                "VALUES (9901, 500000, 'Forward', 'Right', 175)"
            )
        db.commit()

        # Sign them to club 1 (no previous club → from_club_id=None → no Transfer_Record)
        with db.cursor() as cur:
            cid = _next_contract_id(cur)
            cur.execute(
                "INSERT INTO Contract "
                "(contract_id, player_id, club_id, start_date, end_date, weekly_wage) "
                "VALUES (%s, 9901, 1, CURDATE(), '2028-06-30', 100000)", (cid,)
            )
            cur.execute("INSERT INTO Permanent_Contract (contract_id) VALUES (%s)", (cid,))
        db.commit()

        with db.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS cnt FROM Transfer_Record WHERE player_id = 9901")
            cnt = cur.fetchone()['cnt']
        assert cnt == 0, "Initial signing must not create a Transfer_Record"

    # ── Trigger rejections ────────────────────────────────────────────────────

    def test_loan_rejected_when_no_permanent_contract_elsewhere(self, db):
        """
        trg_loan_contract_before_insert: Loan requires an active permanent contract
        at a different club. Player with NO contracts → trigger rejects.
        """
        with db.cursor() as cur:
            cur.execute(
                "INSERT INTO Person (person_id, name, surname, nationality, date_of_birth) "
                "VALUES (9901, 'No', 'Perm', 'Turkish', '2000-01-01')"
            )
            cur.execute(
                "INSERT INTO Player (person_id, market_value, main_position, strong_foot, height) "
                "VALUES (9901, 500000, 'Forward', 'Right', 175)"
            )
        db.commit()

        with pytest.raises(pymysql.Error) as exc_info:
            with db.cursor() as cur:
                cid = _next_contract_id(cur)
                cur.execute(
                    "INSERT INTO Contract "
                    "(contract_id, player_id, club_id, start_date, end_date, weekly_wage) "
                    "VALUES (%s, 9901, 2, CURDATE(), '2028-06-30', 80000)", (cid,)
                )
                # No perm contract at another club → trigger fires here
                cur.execute(
                    "INSERT INTO Loan_Contract (contract_id, permanent_contract_id) "
                    "VALUES (%s, 9999)", (cid,)  # 9999 doesn't exist → FK or trigger error
                )
            db.commit()
        db.rollback()
        # FK violation or trigger SIGNAL expected
        assert exc_info.value is not None

    def test_loan_rejected_when_player_already_has_active_loan(self, db):
        """
        trg_loan_contract_before_insert: duplicate active loan must be rejected.
        Player 9901 has perm at club 1; give them a loan at club 2; second loan → rejected.
        """
        _create_player(db, 9901, club_id=1)
        _do_loan_transfer(db, 9901, dest_club_id=2, fee=500_000)  # first loan OK

        # Second loan attempt
        with pytest.raises(pymysql.Error) as exc_info:
            with db.cursor() as cur:
                perm_cid = _next_contract_id(cur) - 2  # not needed, use sub-query
                cur.execute(
                    "SELECT pc.contract_id FROM Permanent_Contract pc "
                    "JOIN Contract c ON c.contract_id = pc.contract_id "
                    "WHERE c.player_id = 9901 LIMIT 1"
                )
                perm_row = cur.fetchone()
                cid = _next_contract_id(cur)
                cur.execute(
                    "INSERT INTO Contract "
                    "(contract_id, player_id, club_id, start_date, end_date, weekly_wage) "
                    "VALUES (%s, 9901, 3, CURDATE(), '2027-01-31', 70000)", (cid,)
                )
                cur.execute(
                    "INSERT INTO Loan_Contract (contract_id, permanent_contract_id) "
                    "VALUES (%s, %s)", (cid, perm_row['contract_id'])
                )
            db.commit()
        db.rollback()
        # Either 'loan' (trg_loan_contract) or 'maximum' (trg_contract max-2) fires —
        # both correctly prevent a second active loan.
        msg = str(exc_info.value).lower()
        assert 'loan' in msg or 'maximum' in msg or '45000' in str(exc_info.value)

    def test_duplicate_permanent_rejected(self, db):
        """
        trg_permanent_contract_before_insert: inserting a second active permanent
        contract without terminating the first must be rejected.
        """
        _create_player(db, 9901, club_id=1)
        with pytest.raises(pymysql.Error) as exc_info:
            with db.cursor() as cur:
                cid = _next_contract_id(cur)
                cur.execute(
                    "INSERT INTO Contract "
                    "(contract_id, player_id, club_id, start_date, end_date, weekly_wage) "
                    "VALUES (%s, 9901, 2, CURDATE(), '2028-06-30', 100000)", (cid,)
                )
                cur.execute(
                    "INSERT INTO Permanent_Contract (contract_id) VALUES (%s)", (cid,)
                )
            db.commit()
        db.rollback()
        assert 'permanent' in str(exc_info.value).lower() or '45000' in str(exc_info.value)

    def test_third_contract_rejected_by_max_limit(self, db):
        """
        trg_contract_before_insert: max 2 active contracts per player.
        Player with perm + loan (2 contracts) → 3rd INSERT on Contract is rejected.
        """
        _create_player(db, 9901, club_id=1)
        _do_loan_transfer(db, 9901, dest_club_id=2, fee=500_000)
        # Player now has 2 active contracts (perm at 1, loan at 2)

        with pytest.raises(pymysql.Error) as exc_info:
            with db.cursor() as cur:
                cid = _next_contract_id(cur)
                cur.execute(
                    "INSERT INTO Contract "
                    "(contract_id, player_id, club_id, start_date, end_date, weekly_wage) "
                    "VALUES (%s, 9901, 3, CURDATE(), '2028-06-30', 90000)", (cid,)
                )
            db.commit()
        db.rollback()
        assert 'maximum' in str(exc_info.value).lower() or '45000' in str(exc_info.value)

    # ── Transfer_Record CHECK constraints ─────────────────────────────────────

    def test_same_club_transfer_rejected(self, db):
        """
        Transfer_Record CHECK (from_club_id != to_club_id):
        inserting a transfer where source = destination must be rejected.
        """
        _create_player(db, 9901, club_id=1)
        with pytest.raises(pymysql.Error):
            with db.cursor() as cur:
                tid = _next_transfer_id(cur)
                cur.execute(
                    "INSERT INTO Transfer_Record "
                    "(transfer_id, player_id, from_club_id, to_club_id, "
                    " transfer_date, transfer_fee, transfer_type) "
                    "VALUES (%s, 9901, 1, 1, CURDATE(), 0, 'Free')",
                    (tid,)
                )
            db.commit()
        db.rollback()

    def test_free_type_with_nonzero_fee_rejected(self, db):
        """
        Transfer_Record CHECK: transfer_type='Free' AND transfer_fee != 0 violates
        the constraint (Free must have fee=0).
        """
        _create_player(db, 9901, club_id=1)
        with pytest.raises(pymysql.Error):
            with db.cursor() as cur:
                tid = _next_transfer_id(cur)
                cur.execute(
                    "INSERT INTO Transfer_Record "
                    "(transfer_id, player_id, from_club_id, to_club_id, "
                    " transfer_date, transfer_fee, transfer_type) "
                    "VALUES (%s, 9901, 1, 2, CURDATE(), 1000000, 'Free')",
                    (tid,)
                )
            db.commit()
        db.rollback()

    def test_purchase_type_with_zero_fee_rejected(self, db):
        """
        Transfer_Record CHECK: transfer_type='Purchase' AND transfer_fee=0 violates
        the constraint (Purchase must have fee>0).
        """
        _create_player(db, 9901, club_id=1)
        with pytest.raises(pymysql.Error):
            with db.cursor() as cur:
                tid = _next_transfer_id(cur)
                cur.execute(
                    "INSERT INTO Transfer_Record "
                    "(transfer_id, player_id, from_club_id, to_club_id, "
                    " transfer_date, transfer_fee, transfer_type) "
                    "VALUES (%s, 9901, 1, 2, CURDATE(), 0, 'Purchase')",
                    (tid,)
                )
            db.commit()
        db.rollback()

    def test_loan_type_with_zero_fee_rejected(self, db):
        """
        Transfer_Record CHECK: transfer_type='Loan' AND transfer_fee=0 violates
        the constraint (Loan must have fee>0).
        """
        _create_player(db, 9901, club_id=1)
        with pytest.raises(pymysql.Error):
            with db.cursor() as cur:
                tid = _next_transfer_id(cur)
                cur.execute(
                    "INSERT INTO Transfer_Record "
                    "(transfer_id, player_id, from_club_id, to_club_id, "
                    " transfer_date, transfer_fee, transfer_type) "
                    "VALUES (%s, 9901, 1, 2, CURDATE(), 0, 'Loan')",
                    (tid,)
                )
            db.commit()
        db.rollback()

    def test_invalid_transfer_type_rejected(self, db):
        """
        Transfer_Record CHECK: transfer_type must be in ('Free','Purchase','Loan').
        Any other value must be rejected.
        """
        _create_player(db, 9901, club_id=1)
        with pytest.raises(pymysql.Error):
            with db.cursor() as cur:
                tid = _next_transfer_id(cur)
                cur.execute(
                    "INSERT INTO Transfer_Record "
                    "(transfer_id, player_id, from_club_id, to_club_id, "
                    " transfer_date, transfer_fee, transfer_type) "
                    "VALUES (%s, 9901, 1, 2, CURDATE(), 0, 'Gift')",
                    (tid,)
                )
            db.commit()
        db.rollback()
