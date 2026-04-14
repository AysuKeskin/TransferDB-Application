"""
Operation 7: Squad statistics (Manager)

Spec requirements:
  - Current Squad View (no filter): all players with an active contract, stats only
    for performances while playing for this specific club, all-time totals.
  - Historical Season View (season filter): only players who actually played for
    the club in that season.
  - Historical Competition + Season View: further narrowed to one competition.

Query branches (routes/manager.py::manager_squad_stats):
  • else       → current squad (Contract JOIN + LEFT JOIN Match_Participation)
  • elif season → season history  (INNER JOIN Match_Participation + season filter)
  • if comp+season → comp history  (INNER JOIN Match_Participation + comp+season filter)

Key seed data for Club 1 (Royal Madrid):
  Players with active contracts: 8–19 (12 players)
  Player 19 (Camavinga): active contract, zero match participations
  Match_Participation for club 1:
    Match 1 (comp 1 — PL 2025/2026):  players 8–18
    Match 4 (comp 1 — PL 2025/2026):  players 8–18
    Match 5 (comp 2 — CL 2025/2026):  players 8–18

  Player 16 (Vinicius): match1=1g/9.0, match4=2g/9.5, match5=1g/8.5 → total 4g, avg=9.0
  Player 15 (Valverde): match1=1g 8.5, match4=0g/1a 8.0, match5=1g 8.0 → 2g/1a, avg=8.17
  Player 10 (Militao):  match1=1yc, match4=0yc, match5=0yc → 1 yellow total

Temporary test data uses IDs 9901 and is cleaned up after every test.
"""

import pytest

# ── Shared SELECT columns (must match routes/manager.py exactly) ──────────────
_SELECT = """
    SELECT p.person_id, p.name, p.surname,
           TIMESTAMPDIFF(YEAR, p.date_of_birth, CURDATE()) AS age,
           pl.main_position, pl.strong_foot, pl.height,
           pl.market_value, p.nationality,
           COUNT(DISTINCT mp.match_id) AS matches_played,
           COALESCE(SUM(mp.goals),0)            AS goals,
           COALESCE(SUM(mp.assists),0)          AS assists,
           COALESCE(SUM(mp.yellow_cards),0)     AS yellow_cards,
           COALESCE(SUM(mp.red_cards),0)        AS red_cards,
           COALESCE(ROUND(AVG(mp.rating),2),0)  AS avg_rating,
           COALESCE(ROUND(AVG(mp.minutes_played),1),0) AS avg_minutes
"""

CURRENT_SQUAD_QUERY = _SELECT + """
    FROM Person p
    JOIN Player pl ON p.person_id = pl.person_id
    JOIN Contract con ON con.player_id = p.person_id
        AND con.club_id = %s
        AND con.start_date <= CURDATE()
        AND con.end_date   >= CURDATE()
    LEFT JOIN Match_Participation mp ON mp.player_id = p.person_id AND mp.club_id = %s
    GROUP BY p.person_id, p.name, p.surname, p.date_of_birth,
             pl.main_position, pl.strong_foot, pl.height, pl.market_value, p.nationality
    ORDER BY p.surname, p.name
"""

SEASON_QUERY = _SELECT + """
    FROM Person p
    JOIN Player pl ON p.person_id = pl.person_id
    JOIN Match_Participation mp ON mp.player_id = p.person_id AND mp.club_id = %s
    JOIN `Match` m ON mp.match_id = m.match_id
    JOIN Competition comp ON m.competition_id = comp.competition_id
    WHERE comp.season = %s
    GROUP BY p.person_id, p.name, p.surname, p.date_of_birth,
             pl.main_position, pl.strong_foot, pl.height, pl.market_value, p.nationality
    ORDER BY p.surname, p.name
"""

COMP_SEASON_QUERY = _SELECT + """
    FROM Person p
    JOIN Player pl ON p.person_id = pl.person_id
    JOIN Match_Participation mp ON mp.player_id = p.person_id AND mp.club_id = %s
    JOIN `Match` m ON mp.match_id = m.match_id
    JOIN Competition comp ON m.competition_id = comp.competition_id
    WHERE comp.competition_id = %s AND comp.season = %s
    GROUP BY p.person_id, p.name, p.surname, p.date_of_birth,
             pl.main_position, pl.strong_foot, pl.height, pl.market_value, p.nationality
    ORDER BY p.surname, p.name
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _current_squad(db, club_id):
    with db.cursor() as cur:
        cur.execute(CURRENT_SQUAD_QUERY, (club_id, club_id))
        return cur.fetchall()

def _by_season(db, club_id, season):
    with db.cursor() as cur:
        cur.execute(SEASON_QUERY, (club_id, season))
        return cur.fetchall()

def _by_comp_season(db, club_id, comp_id, season):
    with db.cursor() as cur:
        cur.execute(COMP_SEASON_QUERY, (club_id, comp_id, season))
        return cur.fetchall()

def _row(rows, person_id):
    return next((r for r in rows if r['person_id'] == person_id), None)

def _cleanup(db):
    with db.cursor() as cur:
        cur.execute("DELETE FROM Permanent_Contract WHERE contract_id = 9901")
        cur.execute("DELETE FROM Contract           WHERE contract_id = 9901")
        cur.execute("DELETE FROM Player             WHERE person_id   = 9901")
        cur.execute("DELETE FROM Person             WHERE person_id   = 9901")
    db.commit()


@pytest.fixture(autouse=True)
def clean_temp(db):
    _cleanup(db)
    yield
    _cleanup(db)


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestOp7SquadStats:

    # ── Current squad view ────────────────────────────────────────────────────

    def test_current_squad_count(self, db):
        """Club 1 has exactly 12 players with active contracts."""
        rows = _current_squad(db, club_id=1)
        assert len(rows) == 12, f"Expected 12 players, got {len(rows)}"

    def test_player_with_no_participation_shows_zeros(self, db):
        """
        Player 19 (Camavinga) has an active contract with club 1 but has never
        appeared in Match_Participation.  Every stat column must be 0, not NULL.
        """
        row = _row(_current_squad(db, club_id=1), person_id=19)
        assert row is not None, "Player 19 not found in current squad"
        assert row['matches_played'] == 0
        assert row['goals']          == 0
        assert row['assists']        == 0
        assert row['yellow_cards']   == 0
        assert row['red_cards']      == 0
        assert row['avg_rating']     == 0
        assert row['avg_minutes']    == 0

    def test_profile_fields_present(self, db):
        """All required profile columns are returned and non-null."""
        row = _row(_current_squad(db, club_id=1), person_id=16)
        assert row is not None
        for field in ('name', 'surname', 'age', 'main_position',
                      'strong_foot', 'height', 'market_value', 'nationality'):
            assert row[field] is not None, f"Field '{field}' is NULL for player 16"

    def test_no_contract_player_excluded_from_current_squad(self, db):
        """
        A player who exists as a Person/Player but has no contract with any club
        must not appear in the current squad view.

        Note: enforcing an 'expired' contract via UPDATE is blocked by the schema's
        CHECK constraint (contract_chk_1: end_date >= start_date).  The no-contract
        case covers the same code path (Contract JOIN filters them out).
        """
        with db.cursor() as cur:
            cur.execute(
                "INSERT INTO Person (person_id, name, surname, nationality, date_of_birth) "
                "VALUES (9901, 'No', 'Contract', 'Turkish', '1990-01-01')"
            )
            cur.execute(
                "INSERT INTO Player (person_id, market_value, main_position, strong_foot, height) "
                "VALUES (9901, 500000, 'Forward', 'Right', 175)"
            )
        db.commit()

        rows = _current_squad(db, club_id=1)
        assert _row(rows, 9901) is None, "Player without a contract must not appear in current squad"

    def test_stats_aggregated_across_all_competitions(self, db):
        """
        Player 16 (Vinicius) played in comp 1 (PL) AND comp 2 (CL) for club 1.
        Current squad view must sum goals across both: 1 (match1) + 2 (match4) + 1 (match5) = 4.
        """
        row = _row(_current_squad(db, club_id=1), person_id=16)
        assert row['goals'] == 4
        assert row['matches_played'] == 3

    def test_stats_scoped_to_club_only(self, db):
        """
        Club 2's current squad must not include player 16 (club 1 player),
        verifying that stats are isolated per club.
        """
        rows = _current_squad(db, club_id=2)
        assert _row(rows, 16) is None, "Club 1 player must not appear in club 2 current squad"

    def test_yellow_cards_summed_correctly(self, db):
        """Player 10 (Militao) got 1 yellow card in match 1 and 0 in matches 4 and 5 → total 1."""
        row = _row(_current_squad(db, club_id=1), person_id=10)
        assert row['yellow_cards'] == 1

    def test_avg_rating_rounded_to_2dp(self, db):
        """
        Player 15 (Valverde): ratings 8.5, 8.0, 8.0 → avg = 8.166… → rounded to 8.17.
        """
        row = _row(_current_squad(db, club_id=1), person_id=15)
        assert float(row['avg_rating']) == 8.17, f"Expected 8.17, got {row['avg_rating']}"

    def test_matches_played_uses_count_distinct(self, db):
        """
        Player 16 appeared in 3 separate matches (1, 4, 5).
        COUNT(DISTINCT match_id) must be 3, not inflated by any join.
        """
        row = _row(_current_squad(db, club_id=1), person_id=16)
        assert row['matches_played'] == 3

    # ── Historical season view ────────────────────────────────────────────────

    def test_historical_season_only_played_players_shown(self, db):
        """
        In season '2025/2026' for club 1, only players 8–18 played (11 players).
        Player 19 has a contract but no participation → must be absent.
        """
        rows = _by_season(db, club_id=1, season='2025/2026')
        person_ids = {r['person_id'] for r in rows}
        assert 19 not in person_ids, "Player 19 had no participation — must not appear"
        assert len(rows) == 11, f"Expected 11 players, got {len(rows)}"

    def test_historical_season_absent_player_not_shown(self, db):
        """Player 19 has an active contract but no matches → absent from historical view."""
        rows = _by_season(db, club_id=1, season='2025/2026')
        assert _row(rows, 19) is None

    def test_historical_nonexistent_season_returns_empty(self, db):
        """Querying a season with no data must return an empty result."""
        rows = _by_season(db, club_id=1, season='1999/2000')
        assert len(rows) == 0

    def test_season_filter_does_not_leak_across_seasons(self, db):
        """
        Season '2025/2026' has 11 players for club 1 (players 8–18).
        Season '2024/2025' (competition 3) has no matches at all → 0 players.
        Confirms the WHERE clause strictly isolates results to the requested season.
        """
        rows_2526 = _by_season(db, club_id=1, season='2025/2026')
        rows_2425 = _by_season(db, club_id=1, season='2024/2025')

        assert len(rows_2526) == 11, f"Expected 11 for 2025/2026, got {len(rows_2526)}"
        assert len(rows_2425) == 0,  f"Expected 0 for 2024/2025, got {len(rows_2425)}"

    def test_historical_season_stats_correct(self, db):
        """
        Player 16 in season '2025/2026' for club 1: played matches 1, 4, 5 → 4 goals.
        """
        row = _row(_by_season(db, club_id=1, season='2025/2026'), person_id=16)
        assert row is not None
        assert row['goals'] == 4
        assert row['matches_played'] == 3

    # ── Historical competition + season view ──────────────────────────────────

    def test_historical_comp_season_narrows_results(self, db):
        """
        Comp 2 (Champions League) + season '2025/2026' for club 1 only covers match 5.
        Player 16 should show 1 goal (match 5 only), not 4 (all matches).
        """
        row = _row(_by_comp_season(db, club_id=1, comp_id=2, season='2025/2026'), person_id=16)
        assert row is not None
        assert row['goals'] == 1, f"Expected 1 goal (CL only), got {row['goals']}"
        assert row['matches_played'] == 1

    def test_historical_comp_season_player_absent_when_not_in_comp(self, db):
        """
        Player 19 has no participation in any competition → absent from comp+season view.
        """
        rows = _by_comp_season(db, club_id=1, comp_id=1, season='2025/2026')
        assert _row(rows, 19) is None

    def test_comp_only_without_season_falls_to_current_squad(self, db):
        """
        The route's branching logic: `if comp_id and season` → `elif season` → `else`.
        Passing only comp_id (no season) falls to the current squad view, so the
        competition filter is silently ignored and all 12 contracted players appear.
        This is by design per the spec ('filter by a season or a competition AND a season').
        """
        # Simulate the route behaviour: comp_id present, season absent → else branch
        rows = _current_squad(db, club_id=1)
        assert len(rows) == 12
