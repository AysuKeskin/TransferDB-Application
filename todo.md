# TransferDB — Pending Questions & Tasks

## Unanswered Design Question

### Operation 9: Transfer Type in Transfer_Record

When a DB manager registers a transfer + contract, the PDF specifies the following inputs:
- Player
- Destination club
- Contract type (Permanent or Loan)
- Salary
- Transfer fee
- End date of new contract

**Question:** How should the `transfer_type` field in `Transfer_Record` be determined?

**Option A — Infer from inputs (Recommended):**
- Contract type = Loan → `transfer_type = 'Loan'`
- Contract type = Permanent + fee = 0 → `transfer_type = 'Free'`
- Contract type = Permanent + fee > 0 → `transfer_type = 'Purchase'`

**Option B — User selects explicitly:**
- DB manager picks Free / Purchase / Loan as a separate field, independent of contract type.

**Decision needed before demo.**

---

## Known Issues

### Squad Re-submission (app.py ~line 660)
- Current behavior: manager CAN re-submit squad (old entries are deleted and replaced).
- Spec says: one-time submission only.
- Status: deferred — decide before demo whether to add the guard.
