"""
Seed user accounts into the User table.
Run AFTER schema.sql and seed_data.sql:
    python3 seed_users.py
"""
import os

import pymysql
from werkzeug.security import generate_password_hash

DB_CONFIG = {
    'host': 'localhost',
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'database': os.environ.get('DB_NAME', 'DB'),
    'charset': 'utf8mb4',
}

# DB Manager accounts (from initial data spreadsheet)
DB_MANAGERS = [
    ('admin',   'admin'),
    ('kevin',   'K3v!n#2024'),
    ('bob',     'Bob@Secure88'),
    ('admin1',  '326593'),
    ('jessica', 'secretpw.33#'),
    ('admin2',  'admin2pw'),
    ('fatima',  'F4tima!DBmngr'),
    ('yusuf',   'Yu$ufSecure1'),
    ('maria',   'M@r1a321'),
]

# Manager accounts (person_id -> username, password)
MANAGERS = [
    (1, 'ancelotti', 'Carlo!Mgr1'),
    (2, 'guardiola', 'Pep@Coach2'),
    (3, 'klopp',     'Jurgen#K03'),
    (4, 'simeone',   'Diego$Sim4'),
]

# Referee accounts
REFEREES = [
    (5, 'oliver',  'Mike!Ref55'),
    (6, 'brych',   'Felix@Ref6'),
    (7, 'cakir',   'Cuneyt#R77'),
]

# Player accounts (a few key players)
PLAYERS = [
    (16, 'vinicius',  'Vini!Jr016'),
    (30, 'haaland',   'Erling@H30'),
    (40, 'salah',     'Mo$Salah40'),
    (52, 'griezmann', 'Antoine#52'),
    (13, 'modric',    'Luka!Mod13'),
    (26, 'debruyne',  'Kevin@DB26'),
    (34, 'vandijk',   'Virgil#V34'),
    (54, 'morata',    'Alvaro$M54'),
]


def main():
    conn = pymysql.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            for username, password in DB_MANAGERS:
                pw_hash = generate_password_hash(password)
                cur.execute(
                    "INSERT INTO User (username, password_hash, role, person_id) "
                    "VALUES (%s, %s, 'db_manager', NULL)",
                    (username, pw_hash)
                )
                print(f'  [db_manager] {username}')

            for person_id, username, password in MANAGERS:
                pw_hash = generate_password_hash(password)
                cur.execute(
                    "INSERT INTO User (username, password_hash, role, person_id) "
                    "VALUES (%s, %s, 'manager', %s)",
                    (username, pw_hash, person_id)
                )
                print(f'  [manager]    {username} (person_id={person_id})')

            for person_id, username, password in REFEREES:
                pw_hash = generate_password_hash(password)
                cur.execute(
                    "INSERT INTO User (username, password_hash, role, person_id) "
                    "VALUES (%s, %s, 'referee', %s)",
                    (username, pw_hash, person_id)
                )
                print(f'  [referee]    {username} (person_id={person_id})')

            for person_id, username, password in PLAYERS:
                pw_hash = generate_password_hash(password)
                cur.execute(
                    "INSERT INTO User (username, password_hash, role, person_id) "
                    "VALUES (%s, %s, 'player', %s)",
                    (username, pw_hash, person_id)
                )
                print(f'  [player]     {username} (person_id={person_id})')

        conn.commit()
        total = len(DB_MANAGERS) + len(MANAGERS) + len(REFEREES) + len(PLAYERS)
        print(f'\nDone. {total} users seeded.')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
