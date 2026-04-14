import pymysql
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from db import execute_read_one, get_db
from utils import validate_password

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('auth.dashboard'))
    return redirect(url_for('auth.login'))


@auth_bp.route('/dashboard')
def dashboard():
    role = session.get('role')
    if role == 'player':
        return redirect(url_for('player.player_profile'))
    if role == 'manager':
        return redirect(url_for('manager.manager_profile'))
    if role == 'referee':
        return redirect(url_for('referee.referee_profile'))
    if role == 'db_manager':
        return redirect(url_for('dbmanager.dbmanager_dashboard'))
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('auth.dashboard'))
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
            return redirect(url_for('auth.dashboard'))
        flash('Invalid username or password.', 'error')
    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))


@auth_bp.route('/signup')
def signup():
    return render_template('signup_role.html')


@auth_bp.route('/signup/dbmanager', methods=['GET', 'POST'])
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
            from db import execute_query
            execute_query(
                "INSERT INTO User (username, password_hash, role, person_id) VALUES (%s, %s, 'db_manager', NULL)",
                (username, generate_password_hash(password))
            )
            flash('Account created! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except pymysql.IntegrityError:
            flash('Username already taken.', 'error')
        except Exception as exc:
            flash(f'Error: {exc}', 'error')
    return render_template('signup_dbmanager.html', form={})


@auth_bp.route('/signup/player', methods=['GET', 'POST'])
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
            return redirect(url_for('auth.login'))
        except pymysql.IntegrityError as exc:
            conn.rollback()
            flash('Username already taken.' if 'Duplicate entry' in str(exc) else f'DB error: {exc}', 'error')
        except Exception as exc:
            conn.rollback()
            flash(f'Error: {exc}', 'error')
    return render_template('signup_player.html', form={})


@auth_bp.route('/signup/manager', methods=['GET', 'POST'])
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
            return redirect(url_for('auth.login'))
        except pymysql.IntegrityError as exc:
            conn.rollback()
            flash('Username already taken.' if 'Duplicate entry' in str(exc) else f'DB error: {exc}', 'error')
        except Exception as exc:
            conn.rollback()
            flash(f'Error: {exc}', 'error')
    return render_template('signup_manager.html', form={})


@auth_bp.route('/signup/referee', methods=['GET', 'POST'])
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
            return redirect(url_for('auth.login'))
        except pymysql.IntegrityError as exc:
            conn.rollback()
            flash('Username already taken.' if 'Duplicate entry' in str(exc) else f'DB error: {exc}', 'error')
        except Exception as exc:
            conn.rollback()
            flash(f'Error: {exc}', 'error')
    return render_template('signup_referee.html', form={})
