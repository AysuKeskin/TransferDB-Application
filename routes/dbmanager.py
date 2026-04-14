import pymysql
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash

from db import execute_query, execute_read, execute_read_one, get_db
from utils import login_required, role_required, validate_password

dbmanager_bp = Blueprint('dbmanager', __name__)


@dbmanager_bp.route('/dashboard')
@login_required
@role_required('db_manager')
def dbmanager_dashboard():
    return render_template('dashboard_dbmanager.html')


@dbmanager_bp.route('/stadiums')
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


@dbmanager_bp.route('/rename-stadium/<int:stadium_id>', methods=['GET', 'POST'])
@login_required
@role_required('db_manager')
def dbmanager_rename_stadium(stadium_id):
    stadium = execute_read_one(
        'SELECT * FROM Stadium WHERE stadium_id = %s', (stadium_id,)
    )
    if not stadium:
        flash('Stadium not found.', 'error')
        return redirect(url_for('dbmanager.dbmanager_stadiums'))

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
                return redirect(url_for('dbmanager.dbmanager_stadiums'))
            except Exception as exc:
                flash(f'Error: {exc}', 'error')

    return render_template('dbmanager_rename_stadium.html', stadium=stadium)


@dbmanager_bp.route('/schedule-match', methods=['GET', 'POST'])
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
                            away_club_id, referee_id, competition_id)
                           VALUES (%s, %s, %s, %s, %s, %s, %s)''',
                        (nid, match_datetime, stadium_id, home_club_id,
                         away_club_id, referee_id, competition_id)
                    )
                conn.commit()
                flash('Match scheduled successfully!', 'success')
                return redirect(url_for('dbmanager.dbmanager_dashboard'))
            except pymysql.Error as exc:
                conn.rollback()
                msg = exc.args[1] if len(exc.args) > 1 else str(exc)
                flash(f'Database error: {msg}', 'error')

    return render_template('dbmanager_schedule_match.html',
                           stadiums=stadiums, clubs=clubs,
                           referees=referees, competitions=competitions,
                           form=request.form if request.method == 'POST' else {})


@dbmanager_bp.route('/transfer', methods=['GET', 'POST'])
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
                cur.execute('SELECT CURDATE() AS today')
                today = cur.fetchone()['today']

                # Find source club (current permanent contract club)
                cur.execute(
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
                else:
                    # Loan: find the player's active permanent contract at a different club
                    cur.execute(
                        '''SELECT pc.contract_id FROM Permanent_Contract pc
                           JOIN Contract c ON c.contract_id = pc.contract_id
                           WHERE c.player_id = %s
                             AND c.club_id != %s
                             AND c.start_date <= CURDATE()
                             AND c.end_date > CURDATE()
                           LIMIT 1''',
                        (player_id, dest_club_id)
                    )
                    perm_row = cur.fetchone()
                    if not perm_row:
                        conn.rollback()
                        flash('Cannot create loan: player has no active permanent contract with another club.', 'error')
                        return render_template('dbmanager_transfer.html',
                                               players=players, clubs=clubs, form=f)
                    cur.execute(
                        'INSERT INTO Loan_Contract (contract_id, permanent_contract_id) VALUES (%s, %s)',
                        (cid, perm_row['contract_id'])
                    )

                # Determine transfer type and enforce fee rules
                if contract_type == 'Permanent':
                    transfer_type = 'Free' if fee_val == 0 else 'Purchase'
                else:
                    transfer_type = 'Loan'

                # Create transfer record only if player has a source club (i.e. this is a transfer, not a first registration)
                if from_club_id:
                    cur.execute('SELECT COALESCE(MAX(transfer_id), 0) + 1 AS nid FROM Transfer_Record')
                    tid = cur.fetchone()['nid']

                    cur.execute(
                        '''INSERT INTO Transfer_Record
                           (transfer_id, player_id, from_club_id, to_club_id,
                            transfer_date, transfer_fee, transfer_type)
                           VALUES (%s, %s, %s, %s, CURDATE(), %s, %s)''',
                        (tid, player_id, from_club_id, dest_club_id, fee_val, transfer_type)
                    )

            conn.commit()
            flash('Transfer and contract registered successfully!', 'success')
            return redirect(url_for('dbmanager.dbmanager_dashboard'))
        except pymysql.Error as exc:
            conn.rollback()
            msg = exc.args[1] if len(exc.args) > 1 else str(exc)
            flash(f'Database error: {msg}', 'error')
        except Exception as exc:
            conn.rollback()
            flash(f'Error: {exc}', 'error')

    return render_template('dbmanager_transfer.html',
                           players=players, clubs=clubs, form={})


@dbmanager_bp.route('/assign-manager', methods=['GET', 'POST'])
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
                return redirect(url_for('dbmanager.dbmanager_assign_manager'))
            except pymysql.Error as exc:
                conn.rollback()
                flash(f'Database error: {exc}', 'error')

    return render_template('dbmanager_assign_manager.html',
                           managers=managers, clubs=clubs)


@dbmanager_bp.route('/create-competition', methods=['GET', 'POST'])
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
                return redirect(url_for('dbmanager.dbmanager_dashboard'))
            except pymysql.Error as exc:
                conn.rollback()
                msg = exc.args[1] if len(exc.args) > 1 else str(exc)
                flash(f'Database error: {msg}', 'error')

    return render_template('dbmanager_create_competition.html',
                           form=request.form if request.method == 'POST' else {})


@dbmanager_bp.route('/create-user', methods=['GET', 'POST'])
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
            return redirect(url_for('dbmanager.dbmanager_dashboard'))
        except pymysql.IntegrityError as exc:
            conn.rollback()
            flash('Username already taken.' if 'Duplicate entry' in str(exc) else f'DB error: {exc}', 'error')
        except Exception as exc:
            conn.rollback()
            flash(f'Error: {exc}', 'error')

    return render_template('dbmanager_create_user.html', form={})
