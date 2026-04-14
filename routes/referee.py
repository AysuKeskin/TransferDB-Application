import pymysql
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from db import execute_read, execute_read_one, get_db
from utils import login_required, role_required

referee_bp = Blueprint('referee', __name__)


@referee_bp.route('/profile')
@login_required
@role_required('referee')
def referee_profile():
    pid = session['person_id']
    referee = execute_read_one(
        '''SELECT p.name, p.surname, p.nationality, p.date_of_birth,
                  TIMESTAMPDIFF(YEAR, p.date_of_birth, CURDATE()) AS age,
                  r.license_level, r.years_of_experience
           FROM Person p JOIN Referee r ON p.person_id = r.person_id
           WHERE p.person_id = %s''',
        (pid,)
    )
    return render_template('profile_referee.html', referee=referee)


@referee_bp.route('/matches')
@login_required
@role_required('referee')
def referee_matches():
    pid = session['person_id']
    matches = execute_read(
        '''SELECT m.match_id, m.match_datetime,
                  hc.club_name AS home_club, ac.club_name AS away_club,
                  s.stadium_name, comp.name AS competition, comp.season,
                  (SELECT COUNT(*) FROM Match_Participation mp2
                   WHERE mp2.match_id = m.match_id) AS squad_count
           FROM `Match` m
           JOIN Club hc ON m.home_club_id = hc.club_id
           JOIN Club ac ON m.away_club_id = ac.club_id
           JOIN Stadium s ON m.stadium_id = s.stadium_id
           JOIN Competition comp ON m.competition_id = comp.competition_id
           WHERE m.referee_id = %s AND m.home_goals IS NULL AND m.match_datetime < NOW()
           ORDER BY m.match_datetime DESC''',
        (pid,)
    )
    return render_template('referee_matches.html', matches=matches)


@referee_bp.route('/submit/<int:match_id>', methods=['GET', 'POST'])
@login_required
@role_required('referee')
def referee_submit(match_id):
    pid = session['person_id']

    match = execute_read_one(
        '''SELECT m.match_id, m.match_datetime, m.home_goals, m.stadium_id,
                  m.home_club_id, m.away_club_id,
                  hc.club_name AS home_club, ac.club_name AS away_club,
                  s.stadium_name, s.capacity,
                  comp.name AS competition, comp.season
           FROM `Match` m
           JOIN Club hc ON m.home_club_id = hc.club_id
           JOIN Club ac ON m.away_club_id = ac.club_id
           JOIN Stadium s ON m.stadium_id = s.stadium_id
           JOIN Competition comp ON m.competition_id = comp.competition_id
           WHERE m.match_id = %s AND m.referee_id = %s''',
        (match_id, pid)
    )
    if not match:
        flash('Match not found or not assigned to you.', 'error')
        return redirect(url_for('referee.referee_matches'))

    if match['home_goals'] is not None:
        flash('Result already submitted for this match.', 'error')
        return redirect(url_for('referee.referee_matches'))

    def get_club_players(club_id):
        return execute_read(
            '''SELECT p.person_id, p.name, p.surname, pl.main_position
               FROM Person p
               JOIN Player pl ON p.person_id = pl.person_id
               JOIN Contract c ON c.player_id = p.person_id
                   AND c.club_id = %s
                   AND c.start_date <= DATE(%s)
                   AND c.end_date   >= DATE(%s)
               GROUP BY p.person_id, p.name, p.surname, pl.main_position
               ORDER BY pl.main_position, p.surname''',
            (club_id, match['match_datetime'], match['match_datetime'])
        )

    home_players = get_club_players(match['home_club_id'])
    away_players = get_club_players(match['away_club_id'])

    if request.method == 'POST':
        f = request.form
        try:
            home_goals = int(f.get('home_goals', 0))
            away_goals = int(f.get('away_goals', 0))
            attendance = int(f.get('attendance', 0))
        except (ValueError, TypeError):
            flash('Score and attendance must be valid integers.', 'error')
            return render_template('referee_result_form.html',
                                   match=match, home_players=home_players,
                                   away_players=away_players)

        if home_goals < 0 or away_goals < 0:
            flash('Goals cannot be negative.', 'error')
            return render_template('referee_result_form.html',
                                   match=match, home_players=home_players,
                                   away_players=away_players)

        conn = get_db()
        try:
            with conn.cursor() as cur:
                # Process player stats FIRST (before marking match completed,
                # since DB trigger blocks participation inserts on completed matches)
                for club_id in [match['home_club_id'], match['away_club_id']]:
                    players = home_players if club_id == match['home_club_id'] else away_players
                    for pl in players:
                        player_id = pl['person_id']
                        key = f'p_{player_id}'
                        if f.get(f'{key}_played') != 'on':
                            cur.execute(
                                'DELETE FROM Match_Participation WHERE match_id=%s AND player_id=%s',
                                (match_id, player_id)
                            )
                            continue

                        is_starter = f.get(f'{key}_starter') == 'on'
                        try:
                            minutes = int(f.get(f'{key}_minutes', 0))
                            goals = int(f.get(f'{key}_goals', 0))
                            assists = int(f.get(f'{key}_assists', 0))
                            yellow = int(f.get(f'{key}_yellow', 0))
                            red = int(f.get(f'{key}_red', 0))
                            rating = float(f.get(f'{key}_rating', 5.0))
                        except (ValueError, TypeError):
                            flash(f'Invalid stats for player {pl["name"]} {pl["surname"]}.', 'error')
                            conn.rollback()
                            return render_template('referee_result_form.html',
                                                   match=match, home_players=home_players,
                                                   away_players=away_players)

                        position = f.get(f'{key}_position', pl['main_position'])

                        cur.execute(
                            '''INSERT INTO Match_Participation
                               (match_id, player_id, club_id, is_starter,
                                minutes_played, position_in_match,
                                goals, assists, yellow_cards, red_cards, rating)
                               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                               ON DUPLICATE KEY UPDATE
                                   is_starter       = VALUES(is_starter),
                                   minutes_played   = VALUES(minutes_played),
                                   position_in_match = VALUES(position_in_match),
                                   goals            = VALUES(goals),
                                   assists          = VALUES(assists),
                                   yellow_cards     = VALUES(yellow_cards),
                                   red_cards        = VALUES(red_cards),
                                   rating           = VALUES(rating)''',
                            (match_id, player_id, club_id, is_starter,
                             minutes, position, goals, assists, yellow, red, rating)
                        )

                # Update match score LAST (trigger checks attendance <= capacity)
                cur.execute(
                    '''UPDATE `Match`
                       SET home_goals = %s, away_goals = %s,
                           attendance = %s
                       WHERE match_id = %s''',
                    (home_goals, away_goals, attendance, match_id)
                )

            conn.commit()
            flash('Match result submitted successfully!', 'success')
            return redirect(url_for('referee.referee_matches'))

        except pymysql.Error as exc:
            conn.rollback()
            flash(f'Database error: {exc.args[1] if exc.args else exc}', 'error')

    return render_template('referee_result_form.html',
                           match=match, home_players=home_players,
                           away_players=away_players)


@referee_bp.route('/stats')
@login_required
@role_required('referee')
def referee_stats():
    pid = session['person_id']
    stats = execute_read_one(
        '''SELECT COUNT(DISTINCT m.match_id) AS matches_officiated,
                  COALESCE(SUM(mp.yellow_cards), 0) AS total_yellow,
                  COALESCE(SUM(mp.red_cards), 0) AS total_red
           FROM `Match` m
           LEFT JOIN Match_Participation mp ON mp.match_id = m.match_id
           WHERE m.referee_id = %s AND m.home_goals IS NOT NULL ''',
        (pid,)
    )
    return render_template('referee_stats.html', stats=stats)


@referee_bp.route('/history')
@login_required
@role_required('referee')
def referee_history():
    pid = session['person_id']
    matches = execute_read(
        '''SELECT m.match_id, m.match_datetime,
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
           ORDER BY m.match_datetime DESC''',
        (pid,)
    )
    return render_template('referee_history.html', matches=matches)
