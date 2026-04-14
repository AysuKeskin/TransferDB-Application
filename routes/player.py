from flask import Blueprint, render_template, session

from db import execute_read, execute_read_one
from utils import get_player_current_club, login_required, role_required

player_bp = Blueprint('player', __name__)


@player_bp.route('/profile')
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


@player_bp.route('/stats')
@login_required
@role_required('player')
def player_stats():
    pid = session['person_id']
    from flask import request
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


@player_bp.route('/matches')
@login_required
@role_required('player')
def player_matches():
    pid = session['person_id']
    matches = execute_read(
        '''SELECT m.match_id, m.match_datetime, m.home_goals, m.away_goals,
                  CASE WHEN m.home_goals IS NOT NULL THEN 'Completed' ELSE 'Scheduled' END AS status,
                  comp.name AS competition, comp.season,
                  s.stadium_name,
                  hc.club_name AS home_club, ac.club_name AS away_club,
                  mp.club_id, mp.minutes_played, mp.position_in_match,
                  mp.goals, mp.assists, mp.yellow_cards, mp.red_cards, mp.rating,
                  mp.is_starter,
                  CASE WHEN mp.club_id = m.home_club_id THEN ac.club_name
                       ELSE hc.club_name END AS opposing_club,
                  CASE WHEN m.home_goals IS NULL THEN 'Scheduled'
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


@player_bp.route('/career')
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
