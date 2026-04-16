"""
Operation 13: Submitting match results (Referee)

Route: routes/referee.py::referee_submit

Spec requirements tested:
  - Only the assigned referee can submit results.
  - Submission allowed only after match time has passed.
  - Attendance must not exceed stadium capacity.
  - Final score and player-level stats must persist.

Main trigger under test:
  trg_match_before_update (sql/triggers.sql)
"""

from datetime import datetime, timedelta

import pytest
import pymysql

T_MATCH_ID = 9910
T_HOME_CLUB = 9910
T_AWAY_CLUB = 9911
T_ASSIGNED_REFEREE = 5
T_OTHER_REFEREE = 6

HOME_PLAYERS = list(range(9911, 9922))   # 11 players
AWAY_PLAYERS = list(range(9922, 9933))   # 11 players
ALL_PLAYERS = HOME_PLAYERS + AWAY_PLAYERS


def _cleanup(db):
    with db.cursor() as cur:
        cur.execute("DELETE FROM Match_Participation WHERE match_id = %s", (T_MATCH_ID,))
        cur.execute("DELETE FROM `Match` WHERE match_id = %s", (T_MATCH_ID,))

        placeholders = ', '.join(['%s'] * len(ALL_PLAYERS))
        cur.execute(
            f"DELETE FROM Permanent_Contract WHERE contract_id IN ({placeholders})",
            tuple(ALL_PLAYERS),
        )
        cur.execute(
            f"DELETE FROM Contract WHERE contract_id IN ({placeholders})",
            tuple(ALL_PLAYERS),
        )
        cur.execute(
            f"DELETE FROM Player WHERE person_id IN ({placeholders})",
            tuple(ALL_PLAYERS),
        )
        cur.execute(
            f"DELETE FROM Person WHERE person_id IN ({placeholders})",
            tuple(ALL_PLAYERS),
        )

        cur.execute("DELETE FROM Club WHERE club_id IN (%s, %s)", (T_HOME_CLUB, T_AWAY_CLUB))
    db.commit()


@pytest.fixture(autouse=True)
def clean_temp(db):
    _cleanup(db)
    yield
    _cleanup(db)


def _setup_match_with_squads(db):
    """Create temp clubs, 22 players with active contracts, one scheduled match, and 11v11 squads."""
    with db.cursor() as cur:
        cur.execute(
            "INSERT INTO Club (club_id, club_name, foundation_year, stadium_id, manager_id) "
            "VALUES (%s, 'TMP_OP13_HOME', 2000, 1, NULL)",
            (T_HOME_CLUB,),
        )
        cur.execute(
            "INSERT INTO Club (club_id, club_name, foundation_year, stadium_id, manager_id) "
            "VALUES (%s, 'TMP_OP13_AWAY', 2000, 2, NULL)",
            (T_AWAY_CLUB,),
        )

        for i, pid in enumerate(HOME_PLAYERS):
            cur.execute(
                "INSERT INTO Person (person_id, name, surname, nationality, date_of_birth) "
                "VALUES (%s, %s, %s, 'Turkish', '2000-01-01')",
                (pid, f'TmpH{i}', f'Home{i}'),
            )
            cur.execute(
                "INSERT INTO Player (person_id, market_value, main_position, strong_foot, height) "
                "VALUES (%s, 1000000, 'Forward', 'Right', 180)",
                (pid,),
            )
            cur.execute(
                "INSERT INTO Contract (contract_id, player_id, club_id, start_date, end_date, weekly_wage) "
                "VALUES (%s, %s, %s, CURDATE(), '2099-12-31', 50000)",
                (pid, pid, T_HOME_CLUB),
            )
            cur.execute("INSERT INTO Permanent_Contract (contract_id) VALUES (%s)", (pid,))

        for i, pid in enumerate(AWAY_PLAYERS):
            cur.execute(
                "INSERT INTO Person (person_id, name, surname, nationality, date_of_birth) "
                "VALUES (%s, %s, %s, 'Turkish', '2000-01-01')",
                (pid, f'TmpA{i}', f'Away{i}'),
            )
            cur.execute(
                "INSERT INTO Player (person_id, market_value, main_position, strong_foot, height) "
                "VALUES (%s, 1000000, 'Forward', 'Right', 180)",
                (pid,),
            )
            cur.execute(
                "INSERT INTO Contract (contract_id, player_id, club_id, start_date, end_date, weekly_wage) "
                "VALUES (%s, %s, %s, CURDATE(), '2099-12-31', 50000)",
                (pid, pid, T_AWAY_CLUB),
            )
            cur.execute("INSERT INTO Permanent_Contract (contract_id) VALUES (%s)", (pid,))

        match_dt = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S')
        cur.execute(
            """INSERT INTO `Match`
               (match_id, competition_id, home_club_id, away_club_id,
                stadium_id, match_datetime, referee_id)
               VALUES (%s, 1, %s, %s, 1, %s, %s)""",
            (T_MATCH_ID, T_HOME_CLUB, T_AWAY_CLUB, match_dt, T_ASSIGNED_REFEREE),
        )

        for pid in HOME_PLAYERS:
            cur.execute(
                """INSERT INTO Match_Participation
                   (match_id, player_id, club_id, is_starter, minutes_played,
                    position_in_match, goals, assists, yellow_cards, red_cards, rating)
                   VALUES (%s, %s, %s, 1, 0, 'Forward', 0, 0, 0, 0, 5.0)""",
                (T_MATCH_ID, pid, T_HOME_CLUB),
            )

        for pid in AWAY_PLAYERS:
            cur.execute(
                """INSERT INTO Match_Participation
                   (match_id, player_id, club_id, is_starter, minutes_played,
                    position_in_match, goals, assists, yellow_cards, red_cards, rating)
                   VALUES (%s, %s, %s, 1, 0, 'Forward', 0, 0, 0, 0, 5.0)""",
                (T_MATCH_ID, pid, T_AWAY_CLUB),
            )
    db.commit()


def _set_match_datetime_to_past(db):
    with db.cursor() as cur:
        cur.execute(
            "UPDATE `Match` SET match_datetime = DATE_SUB(NOW(), INTERVAL 1 DAY) WHERE match_id = %s",
            (T_MATCH_ID,),
        )
    db.commit()


def _set_match_datetime_to_future(db):
    with db.cursor() as cur:
        cur.execute(
            "UPDATE `Match` SET match_datetime = DATE_ADD(NOW(), INTERVAL 1 DAY) WHERE match_id = %s",
            (T_MATCH_ID,),
        )
    db.commit()


def _submit_result(db, app_person_id, home_goals, away_goals, attendance):
    """Replicates route logic: update player stats, set app person, update match result."""
    with db.cursor() as cur:
        cur.execute(
            """UPDATE Match_Participation
               SET minutes_played = 90, position_in_match = 'Forward',
                   goals = 1, assists = 0, yellow_cards = 0, red_cards = 0, rating = 8.5
               WHERE match_id = %s AND player_id = %s AND club_id = %s""",
            (T_MATCH_ID, HOME_PLAYERS[0], T_HOME_CLUB),
        )
        cur.execute(
            """UPDATE Match_Participation
               SET minutes_played = 90, position_in_match = 'Forward',
                   goals = 0, assists = 1, yellow_cards = 1, red_cards = 0, rating = 7.0
               WHERE match_id = %s AND player_id = %s AND club_id = %s""",
            (T_MATCH_ID, AWAY_PLAYERS[0], T_AWAY_CLUB),
        )

        cur.execute('SET @app_person_id = %s', (app_person_id,))
        cur.execute(
            "UPDATE `Match` SET home_goals = %s, away_goals = %s, attendance = %s WHERE match_id = %s",
            (home_goals, away_goals, attendance, T_MATCH_ID),
        )
    db.commit()


class TestOp13SubmitMatchResults:

    def test_assigned_referee_can_submit_after_match_time(self, db):
        """Assigned referee should be able to submit score+attendance after kickoff time."""
        _setup_match_with_squads(db)
        _set_match_datetime_to_past(db)

        _submit_result(db, app_person_id=T_ASSIGNED_REFEREE, home_goals=2, away_goals=1, attendance=50000)

        with db.cursor() as cur:
            cur.execute(
                "SELECT home_goals, away_goals, attendance FROM `Match` WHERE match_id = %s",
                (T_MATCH_ID,),
            )
            row = cur.fetchone()

        assert row is not None
        assert row['home_goals'] == 2
        assert row['away_goals'] == 1
        assert row['attendance'] == 50000

    def test_non_assigned_referee_rejected(self, db):
        """Only assigned referee can submit initial result (trigger-enforced)."""
        _setup_match_with_squads(db)
        _set_match_datetime_to_past(db)

        with pytest.raises(pymysql.Error):
            _submit_result(db, app_person_id=T_OTHER_REFEREE, home_goals=1, away_goals=0, attendance=45000)
        db.rollback()

        with db.cursor() as cur:
            cur.execute(
                "SELECT home_goals, away_goals, attendance FROM `Match` WHERE match_id = %s",
                (T_MATCH_ID,),
            )
            row = cur.fetchone()
        assert row['home_goals'] is None
        assert row['away_goals'] is None
        assert row['attendance'] is None

    def test_attendance_cannot_exceed_stadium_capacity(self, db):
        """Attendance above Stadium.capacity must be rejected."""
        _setup_match_with_squads(db)
        _set_match_datetime_to_past(db)

        with pytest.raises(pymysql.Error):
            _submit_result(db, app_person_id=T_ASSIGNED_REFEREE, home_goals=1, away_goals=1, attendance=999999)
        db.rollback()

        with db.cursor() as cur:
            cur.execute("SELECT attendance FROM `Match` WHERE match_id = %s", (T_MATCH_ID,))
            row = cur.fetchone()
        assert row['attendance'] is None

    def test_before_match_time_submission_rejected(self, db):
        """Result submission before scheduled datetime must be rejected."""
        _setup_match_with_squads(db)
        _set_match_datetime_to_future(db)

        with pytest.raises(pymysql.Error):
            _submit_result(db, app_person_id=T_ASSIGNED_REFEREE, home_goals=3, away_goals=2, attendance=42000)
        db.rollback()

        with db.cursor() as cur:
            cur.execute(
                "SELECT home_goals, away_goals FROM `Match` WHERE match_id = %s",
                (T_MATCH_ID,),
            )
            row = cur.fetchone()
        assert row['home_goals'] is None
        assert row['away_goals'] is None

    def test_player_stats_persist_with_result_submission(self, db):
        """Player-level match stats entered during submission must be persisted."""
        _setup_match_with_squads(db)
        _set_match_datetime_to_past(db)
        _submit_result(db, app_person_id=T_ASSIGNED_REFEREE, home_goals=2, away_goals=1, attendance=50000)

        with db.cursor() as cur:
            cur.execute(
                """SELECT goals, assists, yellow_cards, red_cards, minutes_played, rating
                   FROM Match_Participation
                   WHERE match_id = %s AND player_id = %s AND club_id = %s""",
                (T_MATCH_ID, HOME_PLAYERS[0], T_HOME_CLUB),
            )
            home = cur.fetchone()
            cur.execute(
                """SELECT goals, assists, yellow_cards, red_cards, minutes_played, rating
                   FROM Match_Participation
                   WHERE match_id = %s AND player_id = %s AND club_id = %s""",
                (T_MATCH_ID, AWAY_PLAYERS[0], T_AWAY_CLUB),
            )
            away = cur.fetchone()

        assert home is not None and away is not None
        assert home['goals'] == 1
        assert home['assists'] == 0
        assert home['yellow_cards'] == 0
        assert home['red_cards'] == 0
        assert home['minutes_played'] == 90
        assert float(home['rating']) == 8.5

        assert away['goals'] == 0
        assert away['assists'] == 1
        assert away['yellow_cards'] == 1
        assert away['red_cards'] == 0
        assert away['minutes_played'] == 90
        assert float(away['rating']) == 7.0
