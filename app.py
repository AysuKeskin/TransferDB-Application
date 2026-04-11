import re
from functools import wraps

import pymysql
from flask import (Flask, flash, g, redirect, render_template,
                   request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from db import close_db, execute_query, execute_read, execute_read_one, get_db

app = Flask(__name__)
app.secret_key = 'transferdb-cmpe321-secret-2026'
app.teardown_appcontext(close_db)
app.jinja_env.globals['enumerate'] = enumerate


# ─────────────────────────────────────────────
# Auth decorators
# ─────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'username' not in session:
            flash('Please log in first.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'username' not in session:
                flash('Please log in first.', 'error')
                return redirect(url_for('login'))
            if session.get('role') not in roles:
                flash('Access denied: insufficient permissions.', 'error')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated
    return decorator


# ─────────────────────────────────────────────
# Password validation
# ─────────────────────────────────────────────

def validate_password(password):
    errors = []
    if len(password) < 8:
        errors.append('Password must be at least 8 characters.')
    if not re.search(r'[A-Z]', password):
        errors.append('Password must contain at least one uppercase letter.')
    if not re.search(r'[a-z]', password):
        errors.append('Password must contain at least one lowercase letter.')
    if not re.search(r'[0-9]', password):
        errors.append('Password must contain at least one digit.')
    if not re.search(r'[^A-Za-z0-9]', password):
        errors.append('Password must contain at least one special character (@, #, $, %, &, etc.).')
    return errors


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def get_manager_club(person_id):
    return execute_read_one(
        'SELECT club_id, club_name FROM Club WHERE manager_id = %s',
        (person_id,)
    )


def get_player_current_club(person_id):
    """Return club_name for player's current club (loan preferred over permanent)."""
    loan = execute_read_one(
        '''SELECT cl.club_name FROM Contract c
           JOIN Loan_Contract lc ON lc.contract_id = c.contract_id
           JOIN Club cl ON cl.club_id = c.club_id
           WHERE c.player_id = %s AND c.start_date <= CURDATE() AND c.end_date >= CURDATE()
           LIMIT 1''',
        (person_id,)
    )
    if loan:
        return loan['club_name']
    perm = execute_read_one(
        '''SELECT cl.club_name FROM Contract c
           JOIN Permanent_Contract pc ON pc.contract_id = c.contract_id
           JOIN Club cl ON cl.club_id = c.club_id
           WHERE c.player_id = %s AND c.start_date <= CURDATE() AND c.end_date >= CURDATE()
           LIMIT 1''',
        (person_id,)
    )
    return perm['club_name'] if perm else 'No Club'


# ─────────────────────────────────────────────
# Core routes
# ─────────────────────────────────────────────

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    role = session.get('role')
    if role == 'player':
        return redirect(url_for('player_profile'))
    if role == 'manager':
        return redirect(url_for('manager_profile'))
    if role == 'referee':
        return redirect(url_for('referee_profile'))
    if role == 'db_manager':
        return redirect(url_for('dbmanager_dashboard'))
    return redirect(url_for('login'))


# ─────────────────────────────────────────────
# Login / Logout
# ─────────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = execute_read_one(
            'SELECT * FROM User WHERE username = %s',
            (username,)
        )
        if user and check_password_hash(user['password_hash'], password):
            session['username'] = user['username']
            session['role'] = user['role']
            session['person_id'] = user['person_id']
            return redirect(url_for('dashboard'))
        flash('Invalid username or password.', 'error')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ─────────────────────────────────────────────
# Signup
# ─────────────────────────────────────────────

@app.route('/signup')
def signup():
    return render_template('signup_role.html')


@app.route('/signup/dbmanager', methods=['GET', 'POST'])
def signup_dbmanager():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        errors = validate_password(password)
        if not username:
            errors.append('Username is required.')
        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('signup_dbmanager.html', form=request.form)
        try:
            execute_query(
                "INSERT INTO User (username, password_hash, role, person_id) VALUES (%s, %s, 'db_manager', NULL)",
                (username, generate_password_hash(password))
            )
            flash('Account created! Please log in.', 'success')
            return redirect(url_for('login'))
        except pymysql.IntegrityError:
            flash('Username already taken.', 'error')
        except Exception as exc:
            flash(f'Error: {exc}', 'error')
    return render_template('signup_dbmanager.html', form={})


@app.route('/signup/player', methods=['GET', 'POST'])
def signup_player():
    if request.method == 'POST':
        f = request.form
        username = f.get('username', '').strip()
        password = f.get('password', '')
        name = f.get('name', '').strip()
        surname = f.get('surname', '').strip()
        nationality = f.get('nationality', '').strip()
        dob = f.get('date_of_birth', '').strip()
        market_value = f.get('market_value', '').strip()
        main_position = f.get('main_position', '').strip()
        strong_foot = f.get('strong_foot', '').strip()
        height = f.get('height', '').strip()

        errors = validate_password(password)
        if not all([username, name, surname, nationality, dob, market_value, main_position, strong_foot, height]):
            errors.append('All fields are required.')

        mv, ht = None, None
        try:
            mv = float(market_value)
            ht = int(height)
            if mv <= 0:
                errors.append('Market value must be positive.')
            if ht <= 0:
                errors.append('Height must be positive.')
        except (ValueError, TypeError):
            errors.append('Market value and height must be valid numbers.')

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('signup_player.html', form=f)

        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute('SELECT COALESCE(MAX(person_id), 0) + 1 AS nid FROM Person')
                nid = cur.fetchone()['nid']
                cur.execute(
                    'INSERT INTO Person (person_id, name, surname, nationality, date_of_birth) VALUES (%s,%s,%s,%s,%s)',
                    (nid, name, surname, nationality, dob)
                )
                cur.execute(
                    'INSERT INTO Player (person_id, market_value, main_position, strong_foot, height) VALUES (%s,%s,%s,%s,%s)',
                    (nid, mv, main_position, strong_foot, ht)
                )
                cur.execute(
                    "INSERT INTO User (username, password_hash, role, person_id) VALUES (%s,%s,'player',%s)",
                    (username, generate_password_hash(password), nid)
                )
            conn.commit()
            flash('Account created! Please log in.', 'success')
            return redirect(url_for('login'))
        except pymysql.IntegrityError as exc:
            conn.rollback()
            flash('Username already taken.' if 'Duplicate entry' in str(exc) else f'DB error: {exc}', 'error')
        except Exception as exc:
            conn.rollback()
            flash(f'Error: {exc}', 'error')
    return render_template('signup_player.html', form={})


@app.route('/signup/manager', methods=['GET', 'POST'])
def signup_manager():
    if request.method == 'POST':
        f = request.form
        username = f.get('username', '').strip()
        password = f.get('password', '')
        name = f.get('name', '').strip()
        surname = f.get('surname', '').strip()
        nationality = f.get('nationality', '').strip()
        dob = f.get('date_of_birth', '').strip()
        formation = f.get('preferred_formation', '').strip()
        exp_level = f.get('experience_level', '').strip()

        errors = validate_password(password)
        if not all([username, name, surname, nationality, dob, formation, exp_level]):
            errors.append('All fields are required.')

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('signup_manager.html', form=f)

        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute('SELECT COALESCE(MAX(person_id), 0) + 1 AS nid FROM Person')
                nid = cur.fetchone()['nid']
                cur.execute(
                    'INSERT INTO Person (person_id, name, surname, nationality, date_of_birth) VALUES (%s,%s,%s,%s,%s)',
                    (nid, name, surname, nationality, dob)
                )
                cur.execute(
                    'INSERT INTO Manager (person_id, preferred_formation, experience_level) VALUES (%s,%s,%s)',
                    (nid, formation, exp_level)
                )
                cur.execute(
                    "INSERT INTO User (username, password_hash, role, person_id) VALUES (%s,%s,'manager',%s)",
                    (username, generate_password_hash(password), nid)
                )
            conn.commit()
            flash('Account created! Please log in.', 'success')
            return redirect(url_for('login'))
        except pymysql.IntegrityError as exc:
            conn.rollback()
            flash('Username already taken.' if 'Duplicate entry' in str(exc) else f'DB error: {exc}', 'error')
        except Exception as exc:
            conn.rollback()
            flash(f'Error: {exc}', 'error')
    return render_template('signup_manager.html', form={})


@app.route('/signup/referee', methods=['GET', 'POST'])
def signup_referee():
    if request.method == 'POST':
        f = request.form
        username = f.get('username', '').strip()
        password = f.get('password', '')
        name = f.get('name', '').strip()
        surname = f.get('surname', '').strip()
        nationality = f.get('nationality', '').strip()
        dob = f.get('date_of_birth', '').strip()
        license_level = f.get('license_level', '').strip()
        years_exp = f.get('years_of_experience', '').strip()

        errors = validate_password(password)
        if not all([username, name, surname, nationality, dob, license_level, years_exp]):
            errors.append('All fields are required.')

        yoe = None
        try:
            yoe = int(years_exp)
            if yoe < 0:
                errors.append('Years of experience must be non-negative.')
        except (ValueError, TypeError):
            errors.append('Years of experience must be a number.')

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('signup_referee.html', form=f)

        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute('SELECT COALESCE(MAX(person_id), 0) + 1 AS nid FROM Person')
                nid = cur.fetchone()['nid']
                cur.execute(
                    'INSERT INTO Person (person_id, name, surname, nationality, date_of_birth) VALUES (%s,%s,%s,%s,%s)',
                    (nid, name, surname, nationality, dob)
                )
                cur.execute(
                    'INSERT INTO Referee (person_id, license_level, years_of_experience) VALUES (%s,%s,%s)',
                    (nid, license_level, yoe)
                )
                cur.execute(
                    "INSERT INTO User (username, password_hash, role, person_id) VALUES (%s,%s,'referee',%s)",
                    (username, generate_password_hash(password), nid)
                )
            conn.commit()
            flash('Account created! Please log in.', 'success')
            return redirect(url_for('login'))
        except pymysql.IntegrityError as exc:
            conn.rollback()
            flash('Username already taken.' if 'Duplicate entry' in str(exc) else f'DB error: {exc}', 'error')
        except Exception as exc:
            conn.rollback()
            flash(f'Error: {exc}', 'error')
    return render_template('signup_referee.html', form={})


# ─────────────────────────────────────────────
# Player routes
# ─────────────────────────────────────────────

@app.route('/player/profile')
@login_required
@role_required('player')
def player_profile():
    pid = session['person_id']
    player = execute_read_one(
        '''SELECT p.name, p.surname, p.nationality, p.date_of_birth,
                  TIMESTAMPDIFF(YEAR, p.date_of_birth, CURDATE()) AS age,
                  pl.market_value, pl.main_position, pl.strong_foot, pl.height
           FROM Person p JOIN Player pl ON p.person_id = pl.person_id
           WHERE p.person_id = %s''',
        (pid,)
    )
    current_club = get_player_current_club(pid)
    return render_template('profile_player.html', player=player, current_club=current_club)


@app.route('/player/stats')
@login_required
@role_required('player')
def player_stats():
    pid = session['person_id']
    season = request.args.get('season', '').strip()
    comp_id = request.args.get('competition_id', '').strip()

    seasons = execute_read(
        '''SELECT DISTINCT comp.season FROM Competition comp
           JOIN `Match` m ON m.competition_id = comp.competition_id
           JOIN Match_Participation mp ON mp.match_id = m.match_id
           WHERE mp.player_id = %s ORDER BY comp.season DESC''',
        (pid,)
    )

    competitions = []
    if season:
        competitions = execute_read(
            '''SELECT DISTINCT comp.competition_id, comp.name FROM Competition comp
               JOIN `Match` m ON m.competition_id = comp.competition_id
               JOIN Match_Participation mp ON mp.match_id = m.match_id
               WHERE mp.player_id = %s AND comp.season = %s ORDER BY comp.name''',
            (pid, season)
        )

    base_select = '''SELECT COUNT(DISTINCT mp.match_id) AS matches_played,
                            COALESCE(SUM(mp.goals),0) AS goals,
                            COALESCE(SUM(mp.assists),0) AS assists,
                            COALESCE(SUM(mp.yellow_cards),0) AS yellow_cards,
                            COALESCE(SUM(mp.red_cards),0) AS red_cards,
                            COALESCE(ROUND(AVG(mp.rating),2),0) AS avg_rating
                     FROM Match_Participation mp'''

    if season and comp_id:
        stats = execute_read_one(
            base_select + '''
            JOIN `Match` m ON mp.match_id = m.match_id
            JOIN Competition comp ON m.competition_id = comp.competition_id
            WHERE mp.player_id = %s AND comp.season = %s AND comp.competition_id = %s''',
            (pid, season, comp_id)
        )
    elif season:
        stats = execute_read_one(
            base_select + '''
            JOIN `Match` m ON mp.match_id = m.match_id
            JOIN Competition comp ON m.competition_id = comp.competition_id
            WHERE mp.player_id = %s AND comp.season = %s''',
            (pid, season)
        )
    else:
        stats = execute_read_one(base_select + ' WHERE mp.player_id = %s', (pid,))

    return render_template('player_stats.html',
                           stats=stats, seasons=seasons, competitions=competitions,
                           season=season, comp_id=comp_id)


@app.route('/player/matches')
@login_required
@role_required('player')
def player_matches():
    pid = session['person_id']
    matches = execute_read(
        '''SELECT m.match_id, m.match_datetime, m.home_goals, m.away_goals, m.status,
                  comp.name AS competition, comp.season,
                  s.stadium_name,
                  hc.club_name AS home_club, ac.club_name AS away_club,
                  mp.club_id, mp.minutes_played, mp.position_in_match,
                  mp.goals, mp.assists, mp.yellow_cards, mp.red_cards, mp.rating,
                  mp.is_starter,
                  CASE WHEN mp.club_id = m.home_club_id THEN ac.club_name
                       ELSE hc.club_name END AS opposing_club,
                  CASE WHEN m.status != 'Completed' THEN 'Scheduled'
                       WHEN (mp.club_id = m.home_club_id AND m.home_goals > m.away_goals)
                         OR (mp.club_id = m.away_club_id AND m.away_goals > m.home_goals) THEN 'Win'
                       WHEN m.home_goals = m.away_goals THEN 'Draw'
                       ELSE 'Loss' END AS result
           FROM Match_Participation mp
           JOIN `Match` m ON mp.match_id = m.match_id
           JOIN Competition comp ON m.competition_id = comp.competition_id
           JOIN Stadium s ON m.stadium_id = s.stadium_id
           JOIN Club hc ON m.home_club_id = hc.club_id
           JOIN Club ac ON m.away_club_id = ac.club_id
           WHERE mp.player_id = %s
           ORDER BY m.match_datetime DESC''',
        (pid,)
    )
    return render_template('player_matches.html', matches=matches)


@app.route('/player/career')
@login_required
@role_required('player')
def player_career():
    pid = session['person_id']
    contracts = execute_read(
        '''SELECT cl.club_name, con.start_date, con.end_date, con.weekly_wage,
                  CASE WHEN pc.contract_id IS NOT NULL THEN 'Permanent' ELSE 'Loan' END AS contract_type
           FROM Contract con
           JOIN Club cl ON con.club_id = cl.club_id
           LEFT JOIN Permanent_Contract pc ON pc.contract_id = con.contract_id
           WHERE con.player_id = %s
           ORDER BY con.start_date DESC''',
        (pid,)
    )
    transfers = execute_read(
        '''SELECT tr.transfer_date, tr.transfer_fee, tr.transfer_type,
                  fc.club_name AS from_club, tc.club_name AS to_club
           FROM Transfer_Record tr
           JOIN Club fc ON tr.from_club_id = fc.club_id
           JOIN Club tc ON tr.to_club_id = tc.club_id
           WHERE tr.player_id = %s
           ORDER BY tr.transfer_date DESC''',
        (pid,)
    )
    return render_template('player_career.html', contracts=contracts, transfers=transfers)


# ─────────────────────────────────────────────
# Manager routes
# ─────────────────────────────────────────────

@app.route('/manager/profile')
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


@app.route('/manager/fixtures')
@login_required
@role_required('manager')
def manager_fixtures():
    pid = session['person_id']
    club = get_manager_club(pid)
    if not club:
        flash('You are not assigned to any club.', 'error')
        return redirect(url_for('manager_profile'))

    club_id = club['club_id']
    comp_filter = request.args.get('competition_id', '').strip()
    season_filter = request.args.get('season', '').strip()

    # Available competitions for this club
    competitions = execute_read(
        '''SELECT DISTINCT comp.competition_id, comp.name, comp.season
           FROM Competition comp
           JOIN `Match` m ON m.competition_id = comp.competition_id
           WHERE m.home_club_id = %s OR m.away_club_id = %s
           ORDER BY comp.season DESC, comp.name''',
        (club_id, club_id)
    )

    query = '''
        SELECT m.match_id, m.match_datetime, m.home_goals, m.away_goals, m.status,
               hc.club_name AS home_club, ac.club_name AS away_club,
               s.stadium_name, comp.name AS competition, comp.season,
               CASE WHEN m.status != 'Completed' THEN 'Scheduled'
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


@app.route('/manager/squad/<int:match_id>', methods=['GET', 'POST'])
@login_required
@role_required('manager')
def manager_squad(match_id):
    pid = session['person_id']
    club = get_manager_club(pid)
    if not club:
        flash('You are not assigned to any club.', 'error')
        return redirect(url_for('manager_fixtures'))

    club_id = club['club_id']

    match = execute_read_one(
        '''SELECT m.match_id, m.match_datetime, m.status,
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
        return redirect(url_for('manager_fixtures'))

    if match['status'] == 'Completed':
        flash('Cannot modify squad for a completed match.', 'error')
        return redirect(url_for('manager_fixtures'))

    # Players eligible: active contract with club on match date
    eligible_players = execute_read(
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

    # Already selected players
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

        # Build position lookup from already-fetched eligible players
        position_map = {str(p['person_id']): p['main_position'] for p in eligible_players}

        conn = get_db()
        try:
            with conn.cursor() as cur:
                # Remove old entries for this club in this match
                cur.execute(
                    'DELETE FROM Match_Participation WHERE match_id = %s AND club_id = %s',
                    (match_id, club_id)
                )
                # Insert new entries
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
            return redirect(url_for('manager_fixtures'))
        except pymysql.Error as exc:
            conn.rollback()
            flash(f'Database error: {exc.args[1] if exc.args else exc}', 'error')

    return render_template('manager_squad.html',
                           match=match, players=eligible_players,
                           existing_map=existing_map, club=club)


@app.route('/manager/standings')
@login_required
@role_required('manager')
def manager_standings():
    pid = session['person_id']
    club = get_manager_club(pid)
    if not club:
        flash('You are not assigned to any club.', 'error')
        return redirect(url_for('manager_profile'))

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
               WHERE m.competition_id = %s AND m.status = 'Completed'
               GROUP BY cl.club_id, cl.club_name
               ORDER BY points DESC, goal_diff DESC, goals_scored DESC''',
            (comp_id,)
        )

    return render_template('manager_standings.html',
                           competitions=competitions, standings=standings,
                           selected_comp=selected_comp, comp_id=comp_id, club=club)


@app.route('/manager/squad-stats')
@login_required
@role_required('manager')
def manager_squad_stats():
    pid = session['person_id']
    club = get_manager_club(pid)
    if not club:
        flash('You are not assigned to any club.', 'error')
        return redirect(url_for('manager_profile'))

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
        # Default: active squad with all-time stats for this club
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


@app.route('/manager/leaderboard')
@login_required
@role_required('manager')
def manager_leaderboard():
    pid = session['person_id']
    club = get_manager_club(pid)
    if not club:
        flash('You are not assigned to any club.', 'error')
        return redirect(url_for('manager_profile'))

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
            order_col = 'metric'
        elif category == 'assists':
            metric_col = 'SUM(mp.assists) AS metric'
            order_col = 'metric'
        else:  # avg_rating
            metric_col = 'ROUND(AVG(mp.rating),2) AS metric'
            order_col = 'metric'

        having_clause = 'HAVING matches_played >= 3' if category == 'avg_rating' else ''

        leaderboard = execute_read(
            base + metric_col + '''
            FROM Match_Participation mp
            JOIN Person p ON mp.player_id = p.person_id
            JOIN Club cl ON mp.club_id = cl.club_id
            JOIN `Match` m ON mp.match_id = m.match_id
            WHERE m.competition_id = %s AND m.status = 'Completed'
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


# ─────────────────────────────────────────────
# Referee routes
# ─────────────────────────────────────────────

@app.route('/referee/profile')
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


@app.route('/referee/matches')
@login_required
@role_required('referee')
def referee_matches():
    pid = session['person_id']
    matches = execute_read(
        '''SELECT m.match_id, m.match_datetime, m.status,
                  hc.club_name AS home_club, ac.club_name AS away_club,
                  s.stadium_name, comp.name AS competition, comp.season,
                  (SELECT COUNT(*) FROM Match_Participation mp2
                   WHERE mp2.match_id = m.match_id) AS squad_count
           FROM `Match` m
           JOIN Club hc ON m.home_club_id = hc.club_id
           JOIN Club ac ON m.away_club_id = ac.club_id
           JOIN Stadium s ON m.stadium_id = s.stadium_id
           JOIN Competition comp ON m.competition_id = comp.competition_id
           WHERE m.referee_id = %s AND m.status = 'Scheduled' AND m.match_datetime < NOW()
           ORDER BY m.match_datetime DESC''',
        (pid,)
    )
    return render_template('referee_matches.html', matches=matches)


@app.route('/referee/submit/<int:match_id>', methods=['GET', 'POST'])
@login_required
@role_required('referee')
def referee_submit(match_id):
    pid = session['person_id']

    match = execute_read_one(
        '''SELECT m.match_id, m.match_datetime, m.status, m.stadium_id,
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
        return redirect(url_for('referee_matches'))

    if match['status'] == 'Completed':
        flash('Result already submitted for this match.', 'error')
        return redirect(url_for('referee_matches'))

    # Players from both clubs (active contracts on match date)
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
                # Update match (trigger checks attendance <= capacity)
                cur.execute(
                    '''UPDATE `Match`
                       SET home_goals = %s, away_goals = %s,
                           attendance = %s, status = 'Completed'
                       WHERE match_id = %s''',
                    (home_goals, away_goals, attendance, match_id)
                )

                # Process player stats for both clubs
                for club_id in [match['home_club_id'], match['away_club_id']]:
                    players = home_players if club_id == match['home_club_id'] else away_players
                    for pl in players:
                        player_id = pl['person_id']
                        key = f'p_{player_id}'
                        if f.get(f'{key}_played') != 'on':
                            # Remove if was in squad but not listed as played
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

            conn.commit()
            flash('Match result submitted successfully!', 'success')
            return redirect(url_for('referee_matches'))

        except pymysql.Error as exc:
            conn.rollback()
            flash(f'Database error: {exc.args[1] if exc.args else exc}', 'error')

    return render_template('referee_result_form.html',
                           match=match, home_players=home_players,
                           away_players=away_players)


# ─────────────────────────────────────────────
# DB Manager routes
# ─────────────────────────────────────────────

@app.route('/dbmanager/dashboard')
@login_required
@role_required('db_manager')
def dbmanager_dashboard():
    return render_template('dashboard_dbmanager.html')


@app.route('/dbmanager/stadiums')
@login_required
@role_required('db_manager')
def dbmanager_stadiums():
    stadiums = execute_read(
        '''SELECT s.stadium_id, s.stadium_name, s.city, s.capacity,
                  GROUP_CONCAT(cl.club_name SEPARATOR ', ') AS clubs
           FROM Stadium s
           LEFT JOIN Club cl ON cl.stadium_id = s.stadium_id
           GROUP BY s.stadium_id, s.stadium_name, s.city, s.capacity
           ORDER BY s.stadium_name'''
    )
    return render_template('dbmanager_stadiums.html', stadiums=stadiums)


@app.route('/dbmanager/rename-stadium/<int:stadium_id>', methods=['GET', 'POST'])
@login_required
@role_required('db_manager')
def dbmanager_rename_stadium(stadium_id):
    stadium = execute_read_one(
        'SELECT * FROM Stadium WHERE stadium_id = %s', (stadium_id,)
    )
    if not stadium:
        flash('Stadium not found.', 'error')
        return redirect(url_for('dbmanager_stadiums'))

    if request.method == 'POST':
        new_name = request.form.get('new_name', '').strip()
        if not new_name:
            flash('Stadium name cannot be empty.', 'error')
        else:
            try:
                execute_query(
                    'UPDATE Stadium SET stadium_name = %s WHERE stadium_id = %s',
                    (new_name, stadium_id)
                )
                flash(f'Stadium renamed to "{new_name}".', 'success')
                return redirect(url_for('dbmanager_stadiums'))
            except Exception as exc:
                flash(f'Error: {exc}', 'error')

    return render_template('dbmanager_rename_stadium.html', stadium=stadium)


@app.route('/dbmanager/schedule-match', methods=['GET', 'POST'])
@login_required
@role_required('db_manager')
def dbmanager_schedule_match():
    stadiums = execute_read('SELECT stadium_id, stadium_name FROM Stadium ORDER BY stadium_name')
    clubs = execute_read('SELECT club_id, club_name FROM Club ORDER BY club_name')
    referees = execute_read(
        '''SELECT r.person_id, p.name, p.surname
           FROM Referee r JOIN Person p ON r.person_id = p.person_id
           ORDER BY p.surname, p.name'''
    )
    competitions = execute_read(
        'SELECT competition_id, name, season FROM Competition ORDER BY season DESC, name'
    )

    if request.method == 'POST':
        f = request.form
        match_datetime = f.get('match_datetime', '').strip()
        stadium_id = f.get('stadium_id', '').strip()
        home_club_id = f.get('home_club_id', '').strip()
        away_club_id = f.get('away_club_id', '').strip()
        referee_id = f.get('referee_id', '').strip()
        competition_id = f.get('competition_id', '').strip()

        if not all([match_datetime, stadium_id, home_club_id, away_club_id, referee_id, competition_id]):
            flash('All fields are required.', 'error')
        elif home_club_id == away_club_id:
            flash('Home and away clubs must be different.', 'error')
        else:
            conn = get_db()
            try:
                with conn.cursor() as cur:
                    cur.execute('SELECT COALESCE(MAX(match_id), 0) + 1 AS nid FROM `Match`')
                    nid = cur.fetchone()['nid']
                    cur.execute(
                        '''INSERT INTO `Match`
                           (match_id, match_datetime, stadium_id, home_club_id,
                            away_club_id, referee_id, competition_id, status)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, 'Scheduled')''',
                        (nid, match_datetime, stadium_id, home_club_id,
                         away_club_id, referee_id, competition_id)
                    )
                conn.commit()
                flash('Match scheduled successfully!', 'success')
                return redirect(url_for('dbmanager_dashboard'))
            except pymysql.Error as exc:
                conn.rollback()
                msg = exc.args[1] if len(exc.args) > 1 else str(exc)
                flash(f'Database error: {msg}', 'error')

    return render_template('dbmanager_schedule_match.html',
                           stadiums=stadiums, clubs=clubs,
                           referees=referees, competitions=competitions,
                           form=request.form if request.method == 'POST' else {})


@app.route('/dbmanager/transfer', methods=['GET', 'POST'])
@login_required
@role_required('db_manager')
def dbmanager_transfer():
    players = execute_read(
        '''SELECT pl.person_id, p.name, p.surname
           FROM Player pl JOIN Person p ON pl.person_id = p.person_id
           ORDER BY p.surname, p.name'''
    )
    clubs = execute_read('SELECT club_id, club_name FROM Club ORDER BY club_name')

    if request.method == 'POST':
        f = request.form
        player_id = f.get('player_id', '').strip()
        dest_club_id = f.get('dest_club_id', '').strip()
        contract_type = f.get('contract_type', '').strip()
        salary = f.get('salary', '').strip()
        transfer_fee = f.get('transfer_fee', '').strip()
        end_date = f.get('end_date', '').strip()

        errors = []
        if not all([player_id, dest_club_id, contract_type, salary, transfer_fee, end_date]):
            errors.append('All fields are required.')

        fee_val, sal_val = None, None
        try:
            fee_val = float(transfer_fee)
            sal_val = float(salary)
        except (ValueError, TypeError):
            errors.append('Salary and transfer fee must be valid numbers.')

        if contract_type not in ('Permanent', 'Loan'):
            errors.append('Contract type must be Permanent or Loan.')

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('dbmanager_transfer.html',
                                   players=players, clubs=clubs, form=f)

        conn = get_db()
        try:
            with conn.cursor() as cur:
                today = None
                cur.execute('SELECT CURDATE() AS today')
                today = cur.fetchone()['today']

                # Find source club (current permanent contract club)
                source = cur.execute(
                    '''SELECT c.club_id FROM Contract c
                       JOIN Permanent_Contract pc ON pc.contract_id = c.contract_id
                       WHERE c.player_id = %s AND c.start_date <= CURDATE() AND c.end_date >= CURDATE()
                       LIMIT 1''',
                    (player_id,)
                )
                source_row = cur.fetchone()
                from_club_id = source_row['club_id'] if source_row else None

                # For permanent transfer: terminate old permanent contract
                if contract_type == 'Permanent' and from_club_id:
                    cur.execute(
                        '''UPDATE Contract SET end_date = CURDATE()
                           WHERE player_id = %s AND end_date >= CURDATE()
                             AND contract_id IN (SELECT contract_id FROM Permanent_Contract)''',
                        (player_id,)
                    )

                # Create new contract
                cur.execute('SELECT COALESCE(MAX(contract_id), 0) + 1 AS nid FROM Contract')
                cid = cur.fetchone()['nid']
                cur.execute(
                    '''INSERT INTO Contract (contract_id, player_id, club_id, start_date, end_date, weekly_wage)
                       VALUES (%s, %s, %s, CURDATE(), %s, %s)''',
                    (cid, player_id, dest_club_id, end_date, sal_val)
                )

                if contract_type == 'Permanent':
                    cur.execute(
                        'INSERT INTO Permanent_Contract (contract_id) VALUES (%s)', (cid,)
                    )
                    # Update market value to match transfer fee
                    cur.execute(
                        'UPDATE Player SET market_value = %s WHERE person_id = %s',
                        (fee_val, player_id)
                    )
                else:
                    # Loan: find the player's active permanent contract
                    cur.execute(
                        '''SELECT pc.contract_id FROM Permanent_Contract pc
                           JOIN Contract c ON c.contract_id = pc.contract_id
                           WHERE c.player_id = %s
                             AND c.start_date <= CURDATE()
                             AND c.end_date >= CURDATE()
                           LIMIT 1''',
                        (player_id,)
                    )
                    perm_row = cur.fetchone()
                    if not perm_row:
                        conn.rollback()
                        flash('Cannot create loan: player has no active permanent contract.', 'error')
                        return render_template('dbmanager_transfer.html',
                                               players=players, clubs=clubs, form=f)
                    cur.execute(
                        'INSERT INTO Loan_Contract (contract_id, permanent_contract_id) VALUES (%s, %s)',
                        (cid, perm_row['contract_id'])
                    )

                # Create transfer record
                cur.execute('SELECT COALESCE(MAX(transfer_id), 0) + 1 AS nid FROM Transfer_Record')
                tid = cur.fetchone()['nid']

                transfer_type = contract_type  # 'Permanent' or 'Loan'
                cur.execute(
                    '''INSERT INTO Transfer_Record
                       (transfer_id, player_id, from_club_id, to_club_id,
                        transfer_date, transfer_fee, transfer_type)
                       VALUES (%s, %s, %s, %s, CURDATE(), %s, %s)''',
                    (tid, player_id,
                     from_club_id if from_club_id else dest_club_id,
                     dest_club_id, fee_val, transfer_type)
                )

            conn.commit()
            flash('Transfer and contract registered successfully!', 'success')
            return redirect(url_for('dbmanager_dashboard'))
        except pymysql.Error as exc:
            conn.rollback()
            msg = exc.args[1] if len(exc.args) > 1 else str(exc)
            flash(f'Database error: {msg}', 'error')
        except Exception as exc:
            conn.rollback()
            flash(f'Error: {exc}', 'error')

    return render_template('dbmanager_transfer.html',
                           players=players, clubs=clubs, form={})


@app.route('/dbmanager/assign-manager', methods=['GET', 'POST'])
@login_required
@role_required('db_manager')
def dbmanager_assign_manager():
    managers = execute_read(
        '''SELECT m.person_id, p.name, p.surname,
                  cl.club_name AS current_club
           FROM Manager m
           JOIN Person p ON m.person_id = p.person_id
           LEFT JOIN Club cl ON cl.manager_id = m.person_id
           ORDER BY p.surname, p.name'''
    )
    clubs = execute_read(
        '''SELECT c.club_id, c.club_name, c.manager_id,
                  CONCAT(p.name, ' ', p.surname) AS current_manager_name
           FROM Club c
           LEFT JOIN Person p ON c.manager_id = p.person_id
           ORDER BY c.club_name'''
    )

    if request.method == 'POST':
        manager_id = request.form.get('manager_id', '').strip()
        club_id = request.form.get('club_id', '').strip()

        if not manager_id or not club_id:
            flash('Both manager and club are required.', 'error')
        else:
            conn = get_db()
            try:
                with conn.cursor() as cur:
                    # Remove manager from any current club
                    cur.execute(
                        'UPDATE Club SET manager_id = NULL WHERE manager_id = %s',
                        (manager_id,)
                    )
                    # Remove any existing manager from the target club
                    cur.execute(
                        'UPDATE Club SET manager_id = NULL WHERE club_id = %s',
                        (club_id,)
                    )
                    # Assign manager to club
                    cur.execute(
                        'UPDATE Club SET manager_id = %s WHERE club_id = %s',
                        (manager_id, club_id)
                    )
                conn.commit()
                flash('Manager assigned successfully!', 'success')
                return redirect(url_for('dbmanager_assign_manager'))
            except pymysql.Error as exc:
                conn.rollback()
                flash(f'Database error: {exc}', 'error')

    return render_template('dbmanager_assign_manager.html',
                           managers=managers, clubs=clubs)


@app.route('/dbmanager/create-competition', methods=['GET', 'POST'])
@login_required
@role_required('db_manager')
def dbmanager_create_competition():
    if request.method == 'POST':
        f = request.form
        name = f.get('name', '').strip()
        season = f.get('season', '').strip()
        country = f.get('country', '').strip()
        comp_type = f.get('competition_type', '').strip()

        if not all([name, season, country, comp_type]):
            flash('All fields are required.', 'error')
        elif comp_type not in ('League', 'Cup', 'International'):
            flash('Invalid competition type.', 'error')
        else:
            conn = get_db()
            try:
                with conn.cursor() as cur:
                    cur.execute('SELECT COALESCE(MAX(competition_id), 0) + 1 AS nid FROM Competition')
                    nid = cur.fetchone()['nid']
                    cur.execute(
                        '''INSERT INTO Competition
                           (competition_id, name, season, country, competition_type)
                           VALUES (%s, %s, %s, %s, %s)''',
                        (nid, name, season, country, comp_type)
                    )
                conn.commit()
                flash('Competition created successfully!', 'success')
                return redirect(url_for('dbmanager_dashboard'))
            except pymysql.Error as exc:
                conn.rollback()
                msg = exc.args[1] if len(exc.args) > 1 else str(exc)
                flash(f'Database error: {msg}', 'error')

    return render_template('dbmanager_create_competition.html',
                           form=request.form if request.method == 'POST' else {})


@app.route('/dbmanager/create-user', methods=['GET', 'POST'])
@login_required
@role_required('db_manager')
def dbmanager_create_user():
    if request.method == 'POST':
        f = request.form
        role = f.get('role', '').strip()
        username = f.get('username', '').strip()
        password = f.get('password', '')
        name = f.get('name', '').strip()
        surname = f.get('surname', '').strip()
        nationality = f.get('nationality', '').strip()
        dob = f.get('date_of_birth', '').strip()

        errors = validate_password(password)
        if not all([role, username, name, surname, nationality, dob]):
            errors.append('All common fields are required.')
        if role not in ('player', 'manager', 'referee'):
            errors.append('Invalid role.')

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('dbmanager_create_user.html', form=f)

        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute('SELECT COALESCE(MAX(person_id), 0) + 1 AS nid FROM Person')
                nid = cur.fetchone()['nid']
                cur.execute(
                    'INSERT INTO Person (person_id, name, surname, nationality, date_of_birth) VALUES (%s,%s,%s,%s,%s)',
                    (nid, name, surname, nationality, dob)
                )

                if role == 'player':
                    market_value = f.get('market_value', '0')
                    main_position = f.get('main_position', '').strip()
                    strong_foot = f.get('strong_foot', '').strip()
                    height = f.get('height', '0')
                    try:
                        mv = float(market_value)
                        ht = int(height)
                    except (ValueError, TypeError):
                        mv, ht = 0, 0
                    cur.execute(
                        'INSERT INTO Player (person_id, market_value, main_position, strong_foot, height) VALUES (%s,%s,%s,%s,%s)',
                        (nid, mv, main_position, strong_foot, ht)
                    )
                elif role == 'manager':
                    formation = f.get('preferred_formation', '').strip()
                    exp_level = f.get('experience_level', '').strip()
                    cur.execute(
                        'INSERT INTO Manager (person_id, preferred_formation, experience_level) VALUES (%s,%s,%s)',
                        (nid, formation, exp_level)
                    )
                elif role == 'referee':
                    license_level = f.get('license_level', '').strip()
                    years_exp = f.get('years_of_experience', '0')
                    try:
                        yoe = int(years_exp)
                    except (ValueError, TypeError):
                        yoe = 0
                    cur.execute(
                        'INSERT INTO Referee (person_id, license_level, years_of_experience) VALUES (%s,%s,%s)',
                        (nid, license_level, yoe)
                    )

                cur.execute(
                    "INSERT INTO User (username, password_hash, role, person_id) VALUES (%s,%s,%s,%s)",
                    (username, generate_password_hash(password), role, nid)
                )
            conn.commit()
            flash(f'{role.title()} user created successfully!', 'success')
            return redirect(url_for('dbmanager_dashboard'))
        except pymysql.IntegrityError as exc:
            conn.rollback()
            flash('Username already taken.' if 'Duplicate entry' in str(exc) else f'DB error: {exc}', 'error')
        except Exception as exc:
            conn.rollback()
            flash(f'Error: {exc}', 'error')

    return render_template('dbmanager_create_user.html', form={})


# ─────────────────────────────────────────────
# Referee additional routes
# ─────────────────────────────────────────────

@app.route('/referee/stats')
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
           WHERE m.referee_id = %s AND m.status = 'Completed' ''',
        (pid,)
    )
    return render_template('referee_stats.html', stats=stats)


@app.route('/referee/history')
@login_required
@role_required('referee')
def referee_history():
    pid = session['person_id']
    matches = execute_read(
        '''SELECT m.match_id, m.match_datetime, m.status,
                  m.home_goals, m.away_goals, m.attendance,
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


if __name__ == '__main__':
    app.run(debug=True)
