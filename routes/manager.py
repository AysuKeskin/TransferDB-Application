import pymysql
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from db import execute_read, execute_read_one, get_db
from utils import get_manager_club, login_required, role_required

manager_bp = Blueprint('manager', __name__)


@manager_bp.route('/profile')
@login_required
@role_required('manager')
def manager_profile():
    pid = session['person_id']
    manager = execute_read_one(
        '''SELECT p.name, p.surname, p.nationality, p.date_of_birth,
                  TIMESTAMPDIFF(YEAR, p.date_of_birth, CURDATE()) AS age,
                  m.preferred_formation, m.experience_level
           FROM Person p JOIN Manager m ON p.person_id = m.person_id
           WHERE p.person_id = %s''',
        (pid,)
    )
    club = get_manager_club(pid)
    return render_template('profile_manager.html', manager=manager, club=club)


@manager_bp.route('/fixtures')
@login_required
@role_required('manager')
def manager_fixtures():
    pid = session['person_id']
    club = get_manager_club(pid)
    if not club:
        flash('You are not assigned to any club.', 'error')
        return redirect(url_for('manager.manager_profile'))

    club_id = club['club_id']
    comp_filter = request.args.get('competition_id', '').strip()
    season_filter = request.args.get('season', '').strip()

    competitions = execute_read(
        '''SELECT DISTINCT comp.competition_id, comp.name, comp.season
           FROM Competition comp
           JOIN `Match` m ON m.competition_id = comp.competition_id
           WHERE m.home_club_id = %s OR m.away_club_id = %s
           ORDER BY comp.season DESC, comp.name''',
        (club_id, club_id)
    )

    query = '''
        SELECT m.match_id, m.match_datetime, m.home_goals, m.away_goals,
               CASE WHEN m.home_goals IS NOT NULL THEN 'Completed' ELSE 'Scheduled' END AS status,
               hc.club_name AS home_club, ac.club_name AS away_club,
               s.stadium_name, comp.name AS competition, comp.season,
               CASE WHEN m.home_goals IS NULL THEN 'Scheduled'
                    WHEN (m.home_club_id = %s AND m.home_goals > m.away_goals)
                      OR (m.away_club_id = %s AND m.away_goals > m.home_goals) THEN 'Win'
                    WHEN m.home_goals = m.away_goals THEN 'Draw'
                    ELSE 'Loss' END AS result,
               (SELECT COUNT(*) FROM Match_Participation mp2
                WHERE mp2.match_id = m.match_id AND mp2.club_id = %s) AS squad_submitted
        FROM `Match` m
        JOIN Club hc ON m.home_club_id = hc.club_id
        JOIN Club ac ON m.away_club_id = ac.club_id
        JOIN Stadium s ON m.stadium_id = s.stadium_id
        JOIN Competition comp ON m.competition_id = comp.competition_id
        WHERE (m.home_club_id = %s OR m.away_club_id = %s)
    '''
    params = [club_id, club_id, club_id, club_id, club_id]

    if comp_filter:
        query += ' AND comp.competition_id = %s'
        params.append(comp_filter)
    if season_filter:
        query += ' AND comp.season = %s'
        params.append(season_filter)

    query += ' ORDER BY m.match_datetime DESC'
    matches = execute_read(query, params)

    return render_template('manager_fixtures.html',
                           matches=matches, club=club,
                           competitions=competitions,
                           comp_filter=comp_filter, season_filter=season_filter)


@manager_bp.route('/squad/<int:match_id>', methods=['GET', 'POST'])
@login_required
@role_required('manager')
def manager_squad(match_id):
    pid = session['person_id']
    club = get_manager_club(pid)
    if not club:
        flash('You are not assigned to any club.', 'error')
        return redirect(url_for('manager.manager_fixtures'))

    club_id = club['club_id']

    match = execute_read_one(
        '''SELECT m.match_id, m.match_datetime, m.home_goals,
                  hc.club_name AS home_club, ac.club_name AS away_club,
                  comp.name AS competition, comp.season
           FROM `Match` m
           JOIN Club hc ON m.home_club_id = hc.club_id
           JOIN Club ac ON m.away_club_id = ac.club_id
           JOIN Competition comp ON m.competition_id = comp.competition_id
           WHERE m.match_id = %s
             AND (m.home_club_id = %s OR m.away_club_id = %s)''',
        (match_id, club_id, club_id)
    )
    if not match:
        flash('Match not found or not associated with your club.', 'error')
        return redirect(url_for('manager.manager_fixtures'))

    if match['home_goals'] is not None:
        flash('Cannot modify squad for a completed match.', 'error')
        return redirect(url_for('manager.manager_fixtures'))

    eligible_players = execute_read(
        '''SELECT p.person_id, p.name, p.surname, pl.main_position
           FROM Person p
           JOIN Player pl ON p.person_id = pl.person_id
           JOIN Contract c ON c.player_id = p.person_id
               AND c.club_id = %s
               AND c.start_date <= DATE(%s)
               AND c.end_date   >= DATE(%s)
           WHERE NOT EXISTS (
               SELECT 1 FROM Contract lc
               JOIN Loan_Contract ON Loan_Contract.contract_id = lc.contract_id
               WHERE lc.player_id = p.person_id
                 AND lc.club_id != %s
                 AND lc.start_date <= DATE(%s)
                 AND lc.end_date   >= DATE(%s)
           )
           GROUP BY p.person_id, p.name, p.surname, pl.main_position
           ORDER BY pl.main_position, p.surname''',
        (club_id, match['match_datetime'], match['match_datetime'],
         club_id, match['match_datetime'], match['match_datetime'])
    )

    existing = execute_read(
        'SELECT player_id, is_starter FROM Match_Participation WHERE match_id = %s AND club_id = %s',
        (match_id, club_id)
    )
    existing_map = {row['player_id']: row['is_starter'] for row in existing}

    if request.method == 'POST':
        selected_ids = request.form.getlist('player_ids')
        starter_ids = set(request.form.getlist('starter_ids'))

        if len(selected_ids) < 11 or len(selected_ids) > 23:
            flash('Squad must have between 11 and 23 players.', 'error')
            return render_template('manager_squad.html',
                                   match=match, players=eligible_players,
                                   existing_map=existing_map, club=club)

        starter_count = sum(1 for pid_ in selected_ids if pid_ in starter_ids)
        if starter_count > 11:
            flash('Maximum 11 starters allowed.', 'error')
            return render_template('manager_squad.html',
                                   match=match, players=eligible_players,
                                   existing_map=existing_map, club=club)

        position_map = {str(p['person_id']): p['main_position'] for p in eligible_players}

        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    'DELETE FROM Match_Participation WHERE match_id = %s AND club_id = %s',
                    (match_id, club_id)
                )
                for player_id_str in selected_ids:
                    player_id = int(player_id_str)
                    is_starter = player_id_str in starter_ids
                    position = position_map.get(player_id_str, 'Unknown')
                    cur.execute(
                        '''INSERT INTO Match_Participation
                           (match_id, player_id, club_id, is_starter,
                            minutes_played, position_in_match,
                            goals, assists, yellow_cards, red_cards, rating)
                           VALUES (%s,%s,%s,%s,0,%s,0,0,0,0,5.0)''',
                        (match_id, player_id, club_id, is_starter, position)
                    )
            conn.commit()
            flash('Squad submitted successfully!', 'success')
            return redirect(url_for('manager.manager_fixtures'))
        except pymysql.Error as exc:
            conn.rollback()
            flash(f'Database error: {exc.args[1] if exc.args else exc}', 'error')

    return render_template('manager_squad.html',
                           match=match, players=eligible_players,
                           existing_map=existing_map, club=club)


@manager_bp.route('/standings')
@login_required
@role_required('manager')
def manager_standings():
    pid = session['person_id']
    club = get_manager_club(pid)
    if not club:
        flash('You are not assigned to any club.', 'error')
        return redirect(url_for('manager.manager_profile'))

    club_id = club['club_id']
    comp_id = request.args.get('competition_id', '').strip()

    competitions = execute_read(
        '''SELECT DISTINCT comp.competition_id, comp.name, comp.season
           FROM Competition comp
           JOIN `Match` m ON m.competition_id = comp.competition_id
           WHERE comp.competition_type = 'League'
             AND (m.home_club_id = %s OR m.away_club_id = %s)
           ORDER BY comp.season DESC, comp.name''',
        (club_id, club_id)
    )

    standings = []
    selected_comp = None
    if comp_id:
        selected_comp = execute_read_one(
            'SELECT * FROM Competition WHERE competition_id = %s', (comp_id,)
        )
        standings = execute_read(
            '''SELECT cl.club_id, cl.club_name,
                      COUNT(*) AS played,
                      SUM(CASE WHEN (m.home_club_id = cl.club_id AND m.home_goals > m.away_goals)
                                 OR (m.away_club_id = cl.club_id AND m.away_goals > m.home_goals)
                               THEN 1 ELSE 0 END) AS wins,
                      SUM(CASE WHEN m.home_goals = m.away_goals THEN 1 ELSE 0 END) AS draws,
                      SUM(CASE WHEN (m.home_club_id = cl.club_id AND m.home_goals < m.away_goals)
                                 OR (m.away_club_id = cl.club_id AND m.away_goals < m.home_goals)
                               THEN 1 ELSE 0 END) AS losses,
                      SUM(CASE WHEN m.home_club_id = cl.club_id THEN m.home_goals
                               ELSE m.away_goals END) AS goals_scored,
                      SUM(CASE WHEN m.home_club_id = cl.club_id THEN m.away_goals
                               ELSE m.home_goals END) AS goals_conceded,
                      SUM(CASE WHEN m.home_club_id = cl.club_id THEN m.home_goals - m.away_goals
                               ELSE m.away_goals - m.home_goals END) AS goal_diff,
                      SUM(CASE WHEN (m.home_club_id = cl.club_id AND m.home_goals > m.away_goals)
                                 OR (m.away_club_id = cl.club_id AND m.away_goals > m.home_goals)
                               THEN 3
                               WHEN m.home_goals = m.away_goals THEN 1
                               ELSE 0 END) AS points
               FROM Club cl
               JOIN `Match` m ON (m.home_club_id = cl.club_id OR m.away_club_id = cl.club_id)
               WHERE m.competition_id = %s AND m.home_goals IS NOT NULL
               GROUP BY cl.club_id, cl.club_name
               ORDER BY points DESC, goal_diff DESC, goals_scored DESC''',
            (comp_id,)
        )

    return render_template('manager_standings.html',
                           competitions=competitions, standings=standings,
                           selected_comp=selected_comp, comp_id=comp_id, club=club)


@manager_bp.route('/squad-stats')
@login_required
@role_required('manager')
def manager_squad_stats():
    pid = session['person_id']
    club = get_manager_club(pid)
    if not club:
        flash('You are not assigned to any club.', 'error')
        return redirect(url_for('manager.manager_profile'))

    club_id = club['club_id']
    comp_id = request.args.get('competition_id', '').strip()
    season = request.args.get('season', '').strip()

    competitions = execute_read(
        '''SELECT DISTINCT comp.competition_id, comp.name, comp.season
           FROM Competition comp
           JOIN `Match` m ON m.competition_id = comp.competition_id
           WHERE m.home_club_id = %s OR m.away_club_id = %s
           ORDER BY comp.season DESC, comp.name''',
        (club_id, club_id)
    )

    select_cols = '''SELECT p.person_id, p.name, p.surname,
                            TIMESTAMPDIFF(YEAR, p.date_of_birth, CURDATE()) AS age,
                            pl.main_position, pl.strong_foot, pl.height,
                            pl.market_value, p.nationality,
                            COUNT(DISTINCT mp.match_id) AS matches_played,
                            COALESCE(SUM(mp.goals),0) AS goals,
                            COALESCE(SUM(mp.assists),0) AS assists,
                            COALESCE(SUM(mp.yellow_cards),0) AS yellow_cards,
                            COALESCE(SUM(mp.red_cards),0) AS red_cards,
                            COALESCE(ROUND(AVG(mp.rating),2),0) AS avg_rating,
                            COALESCE(ROUND(AVG(mp.minutes_played),1),0) AS avg_minutes'''

    if comp_id and season:
        players = execute_read(
            select_cols + '''
            FROM Person p
            JOIN Player pl ON p.person_id = pl.person_id
            JOIN Match_Participation mp ON mp.player_id = p.person_id AND mp.club_id = %s
            JOIN `Match` m ON mp.match_id = m.match_id
            JOIN Competition comp ON m.competition_id = comp.competition_id
            WHERE comp.competition_id = %s AND comp.season = %s
            GROUP BY p.person_id, p.name, p.surname, p.date_of_birth,
                     pl.main_position, pl.strong_foot, pl.height, pl.market_value, p.nationality
            ORDER BY p.surname, p.name''',
            (club_id, comp_id, season)
        )
    elif season:
        players = execute_read(
            select_cols + '''
            FROM Person p
            JOIN Player pl ON p.person_id = pl.person_id
            JOIN Match_Participation mp ON mp.player_id = p.person_id AND mp.club_id = %s
            JOIN `Match` m ON mp.match_id = m.match_id
            JOIN Competition comp ON m.competition_id = comp.competition_id
            WHERE comp.season = %s
            GROUP BY p.person_id, p.name, p.surname, p.date_of_birth,
                     pl.main_position, pl.strong_foot, pl.height, pl.market_value, p.nationality
            ORDER BY p.surname, p.name''',
            (club_id, season)
        )
    else:
        players = execute_read(
            select_cols + '''
            FROM Person p
            JOIN Player pl ON p.person_id = pl.person_id
            JOIN Contract con ON con.player_id = p.person_id
                AND con.club_id = %s
                AND con.start_date <= CURDATE()
                AND con.end_date   >= CURDATE()
            LEFT JOIN Match_Participation mp ON mp.player_id = p.person_id AND mp.club_id = %s
            GROUP BY p.person_id, p.name, p.surname, p.date_of_birth,
                     pl.main_position, pl.strong_foot, pl.height, pl.market_value, p.nationality
            ORDER BY p.surname, p.name''',
            (club_id, club_id)
        )

    seasons = execute_read(
        '''SELECT DISTINCT comp.season FROM Competition comp
           JOIN `Match` m ON m.competition_id = comp.competition_id
           WHERE m.home_club_id = %s OR m.away_club_id = %s
           ORDER BY comp.season DESC''',
        (club_id, club_id)
    )

    return render_template('manager_squad_stats.html',
                           players=players, competitions=competitions,
                           seasons=seasons, comp_id=comp_id, season=season, club=club)


@manager_bp.route('/leaderboard')
@login_required
@role_required('manager')
def manager_leaderboard():
    pid = session['person_id']
    club = get_manager_club(pid)
    if not club:
        flash('You are not assigned to any club.', 'error')
        return redirect(url_for('manager.manager_profile'))

    club_id = club['club_id']
    comp_id = request.args.get('competition_id', '').strip()
    category = request.args.get('category', 'goals').strip()

    competitions = execute_read(
        '''SELECT DISTINCT comp.competition_id, comp.name, comp.season
           FROM Competition comp
           JOIN `Match` m ON m.competition_id = comp.competition_id
           WHERE m.home_club_id = %s OR m.away_club_id = %s
           ORDER BY comp.season DESC, comp.name''',
        (club_id, club_id)
    )

    leaderboard = []
    selected_comp = None
    if comp_id:
        selected_comp = execute_read_one(
            'SELECT * FROM Competition WHERE competition_id = %s', (comp_id,)
        )

        base = '''SELECT p.name, p.surname, cl.club_name,
                         COUNT(DISTINCT mp.match_id) AS matches_played,'''

        if category == 'goals':
            metric_col = 'SUM(mp.goals) AS metric'
        elif category == 'assists':
            metric_col = 'SUM(mp.assists) AS metric'
        else:  # avg_rating
            metric_col = 'ROUND(AVG(mp.rating),2) AS metric'

        having_clause = 'HAVING matches_played >= 3' if category == 'avg_rating' else ''

        leaderboard = execute_read(
            base + metric_col + '''
            FROM Match_Participation mp
            JOIN Person p ON mp.player_id = p.person_id
            JOIN Club cl ON mp.club_id = cl.club_id
            JOIN `Match` m ON mp.match_id = m.match_id
            WHERE m.competition_id = %s AND m.home_goals IS NOT NULL
            GROUP BY mp.player_id, p.name, p.surname, cl.club_name
            ''' + having_clause + '''
            ORDER BY metric DESC
            LIMIT 10''',
            (comp_id,)
        )

    return render_template('manager_leaderboard.html',
                           competitions=competitions, leaderboard=leaderboard,
                           selected_comp=selected_comp, comp_id=comp_id,
                           category=category, club=club)
