"""
Seed user accounts into the User table from initial_data.xlsx.
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

MANAGERS = [
    (2001, 'fatih_terim',    'hash_M@nager1'),
    (2002, 'jorge_jesus',    'hash_M@nager2'),
    (2003, 'ismail_kartal',  'hash_M3'),
    (2004, 'pep_guardiola',  'hash_M4'),
    (2005, 'jurgen_klopp',   'hash_M5'),
    (2006, 'sergen_yalcin',  'hash_M6'),
    (2007, 'okan_buruk',     'hash_M7'),
    (2008, 'jose_mourinho',  'hash_M8'),
    (2009, 'volkan_demirel', 'hash_M9'),
    (2010, 'clubs_coach',    'coach123'),
]

REFEREES = [
    (1001, 'cuneyt_cakir',       'hash_R3feree!'),
    (1002, 'halil_meler',        'hash_R3feree2'),
    (1003, 'michael_oliver',     'hash_Ref03'),
    (1004, 'anthony_taylor',     'hash_Ref04'),
    (1005, 'szymon_marciniak',   'hash_Ref05'),
    (1006, 'stephanie_frappart', 'hash_Ref06'),
    (1007, 'ali_palabiyik',      'hash_Ref07'),
]

PLAYERS = [
    (1,  'burak_yilmaz',     'hash_Str0ng!1'),
    (2,  'arda_guler',       'hash_Str0ng!2'),
    (3,  'gedson_fernandes', 'hash_Str0ng!3'),
    (4,  'fernando_muslera', 'hash_Str0ng!4'),
    (5,  'altay_bayindir',   'hash_1'),
    (6,  'ferdi_kadioglu',   'hash_2'),
    (7,  'caglar_soyuncu',   'hash_3'),
    (8,  'ozan_kabak',       'hash_4'),
    (9,  'salih_ozcan',      'hash_5'),
    (10, 'hakan_calhanoglu', 'hash_6'),
    (11, 'orkun_kokcu',      'hash_7'),
    (12, 'kerem_akturkoglu', 'hash_8'),
    (13, 'baris_yilmaz',     'hash_9'),
    (14, 'enes_unal',        'hash_10'),
    (15, 'cengiz_under',     'hash_11'),
    (16, 'arzgr222',         'arzgr222'),
    (17, 'berkgkts',         'berkgkts'),
    (18, 'b_ayd23',          'b_ayd23'),
]


def main():
    conn = pymysql.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            for username, password in DB_MANAGERS:
                pw_hash = generate_password_hash(str(password))
                cur.execute(
                    "INSERT INTO User (username, password_hash, role, person_id) "
                    "VALUES (%s, %s, 'db_manager', NULL)",
                    (username, pw_hash)
                )
                print(f'  [db_manager] {username}')

            for person_id, username, password in MANAGERS:
                pw_hash = generate_password_hash(str(password))
                cur.execute(
                    "INSERT INTO User (username, password_hash, role, person_id) "
                    "VALUES (%s, %s, 'manager', %s)",
                    (username, pw_hash, person_id)
                )
                print(f'  [manager]    {username} (person_id={person_id})')

            for person_id, username, password in REFEREES:
                pw_hash = generate_password_hash(str(password))
                cur.execute(
                    "INSERT INTO User (username, password_hash, role, person_id) "
                    "VALUES (%s, %s, 'referee', %s)",
                    (username, pw_hash, person_id)
                )
                print(f'  [referee]    {username} (person_id={person_id})')

            for person_id, username, password in PLAYERS:
                pw_hash = generate_password_hash(str(password))
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
