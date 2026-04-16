-- Sample data for TransferDB
-- Run AFTER schema.sql but BEFORE triggers.sql:
--   mysql -u root -p < sql/schema.sql
--   mysql -u root -p DB < sql/seed_data.sql
--   mysql -u root -p DB < sql/triggers.sql
--   python3 seed_users.py

USE DB;

-- ============================================================
-- PERSONS: Managers (1-4), Referees (5-7), Players (8-55)
-- ============================================================

-- Managers
INSERT INTO Person VALUES (1, 'Carlo', 'Ancelotti', 'Italian', '1959-06-10');
INSERT INTO Person VALUES (2, 'Pep', 'Guardiola', 'Spanish', '1971-01-18');
INSERT INTO Person VALUES (3, 'Jurgen', 'Klopp', 'German', '1967-06-16');
INSERT INTO Person VALUES (4, 'Diego', 'Simeone', 'Argentinian', '1970-04-28');

INSERT INTO Manager VALUES (1, '4-3-3', 'Senior');
INSERT INTO Manager VALUES (2, '4-3-3', 'Senior');
INSERT INTO Manager VALUES (3, '4-2-3-1', 'Senior');
INSERT INTO Manager VALUES (4, '4-4-2', 'Senior');

-- Referees
INSERT INTO Person VALUES (5, 'Michael', 'Oliver', 'English', '1985-02-20');
INSERT INTO Person VALUES (6, 'Felix', 'Brych', 'German', '1975-08-03');
INSERT INTO Person VALUES (7, 'Cuneyt', 'Cakir', 'Turkish', '1976-11-23');

INSERT INTO Referee VALUES (5, 'FIFA', 15);
INSERT INTO Referee VALUES (6, 'FIFA', 20);
INSERT INTO Referee VALUES (7, 'FIFA', 18);

-- ============================================================
-- Players: Club 1 (8-19), Club 2 (20-31), Club 3 (32-43), Club 4 (44-55)
-- ============================================================

-- Club 1 players (Royal Madrid)
INSERT INTO Person VALUES (8,  'Thibaut', 'Courtois',   'Belgian',    '1992-05-11');
INSERT INTO Person VALUES (9,  'Dani',    'Carvajal',   'Spanish',    '1992-01-11');
INSERT INTO Person VALUES (10, 'Eder',    'Militao',    'Brazilian',  '1998-01-18');
INSERT INTO Person VALUES (11, 'David',   'Alaba',      'Austrian',   '1992-06-24');
INSERT INTO Person VALUES (12, 'Ferland', 'Mendy',      'French',     '1995-06-08');
INSERT INTO Person VALUES (13, 'Luka',    'Modric',     'Croatian',   '1985-09-09');
INSERT INTO Person VALUES (14, 'Toni',    'Kroos',      'German',     '1990-01-04');
INSERT INTO Person VALUES (15, 'Federico','Valverde',   'Uruguayan',  '1998-07-22');
INSERT INTO Person VALUES (16, 'Vinicius','Junior',     'Brazilian',  '2000-07-12');
INSERT INTO Person VALUES (17, 'Rodrygo', 'Goes',       'Brazilian',  '2001-01-09');
INSERT INTO Person VALUES (18, 'Karim',   'Benzema',    'French',     '1987-12-19');
INSERT INTO Person VALUES (19, 'Eduardo', 'Camavinga',  'French',     '2002-11-10');

-- Club 2 players (Manchester Blues)
INSERT INTO Person VALUES (20, 'Ederson', 'Moraes',     'Brazilian',  '1993-08-17');
INSERT INTO Person VALUES (21, 'Kyle',    'Walker',     'English',    '1990-05-28');
INSERT INTO Person VALUES (22, 'Ruben',   'Dias',       'Portuguese', '1997-05-14');
INSERT INTO Person VALUES (23, 'John',    'Stones',     'English',    '1994-05-28');
INSERT INTO Person VALUES (24, 'Joao',    'Cancelo',    'Portuguese', '1994-05-27');
INSERT INTO Person VALUES (25, 'Rodri',   'Hernandez',  'Spanish',    '1996-06-22');
INSERT INTO Person VALUES (26, 'Kevin',   'DeBruyne',   'Belgian',    '1991-06-28');
INSERT INTO Person VALUES (27, 'Bernardo','Silva',      'Portuguese', '1994-08-10');
INSERT INTO Person VALUES (28, 'Phil',    'Foden',      'English',    '2000-05-28');
INSERT INTO Person VALUES (29, 'Jack',    'Grealish',   'English',    '1995-09-10');
INSERT INTO Person VALUES (30, 'Erling',  'Haaland',    'Norwegian',  '2000-07-21');
INSERT INTO Person VALUES (31, 'Julian',  'Alvarez',    'Argentinian','2000-01-31');

-- Club 3 players (Liverpool Reds)
INSERT INTO Person VALUES (32, 'Alisson', 'Becker',     'Brazilian',  '1992-10-02');
INSERT INTO Person VALUES (33, 'Trent',   'Alexander',  'English',    '1998-10-07');
INSERT INTO Person VALUES (34, 'Virgil',  'VanDijk',    'Dutch',      '1991-07-08');
INSERT INTO Person VALUES (35, 'Ibrahima','Konate',     'French',     '1999-05-25');
INSERT INTO Person VALUES (36, 'Andrew',  'Robertson',  'Scottish',   '1994-03-11');
INSERT INTO Person VALUES (37, 'Fabinho', 'Tavares',    'Brazilian',  '1993-10-23');
INSERT INTO Person VALUES (38, 'Thiago',  'Alcantara',  'Spanish',    '1991-04-11');
INSERT INTO Person VALUES (39, 'Jordan',  'Henderson',  'English',    '1990-06-17');
INSERT INTO Person VALUES (40, 'Mohamed', 'Salah',      'Egyptian',   '1992-06-15');
INSERT INTO Person VALUES (41, 'Sadio',   'Mane',       'Senegalese', '1992-04-10');
INSERT INTO Person VALUES (42, 'Darwin',  'Nunez',      'Uruguayan',  '1999-06-24');
INSERT INTO Person VALUES (43, 'Diogo',   'Jota',       'Portuguese', '1996-12-04');

-- Club 4 players (Atletico Madrid)
INSERT INTO Person VALUES (44, 'Jan',     'Oblak',      'Slovenian',  '1993-01-07');
INSERT INTO Person VALUES (45, 'Nahuel',  'Molina',     'Argentinian','1998-04-06');
INSERT INTO Person VALUES (46, 'Jose',    'Gimenez',    'Uruguayan',  '1995-01-20');
INSERT INTO Person VALUES (47, 'Stefan',  'Savic',      'Montenegrin','1991-01-08');
INSERT INTO Person VALUES (48, 'Reinildo','Mandava',    'Mozambican', '1994-01-21');
INSERT INTO Person VALUES (49, 'Koke',    'Resurreccion','Spanish',   '1992-01-08');
INSERT INTO Person VALUES (50, 'Marcos',  'Llorente',   'Spanish',    '1995-01-30');
INSERT INTO Person VALUES (51, 'Rodrigo', 'DePaul',     'Argentinian','1994-05-24');
INSERT INTO Person VALUES (52, 'Antoine', 'Griezmann',  'French',     '1991-03-21');
INSERT INTO Person VALUES (53, 'Angel',   'Correa',     'Argentinian','1995-03-09');
INSERT INTO Person VALUES (54, 'Alvaro',  'Morata',     'Spanish',    '1992-10-23');
INSERT INTO Person VALUES (55, 'Samuel',  'Lino',       'Brazilian',  '1999-12-23');

-- Player records
INSERT INTO Player VALUES (8,  35000000, 'Goalkeeper', 'Right', 199);
INSERT INTO Player VALUES (9,  20000000, 'Defender',   'Right', 173);
INSERT INTO Player VALUES (10, 40000000, 'Defender',   'Right', 186);
INSERT INTO Player VALUES (11, 25000000, 'Defender',   'Left',  180);
INSERT INTO Player VALUES (12, 30000000, 'Defender',   'Left',  180);
INSERT INTO Player VALUES (13, 15000000, 'Midfielder', 'Both',  172);
INSERT INTO Player VALUES (14, 20000000, 'Midfielder', 'Right', 183);
INSERT INTO Player VALUES (15, 80000000, 'Midfielder', 'Right', 182);
INSERT INTO Player VALUES (16,150000000, 'Forward',    'Right', 176);
INSERT INTO Player VALUES (17, 80000000, 'Forward',    'Right', 174);
INSERT INTO Player VALUES (18, 30000000, 'Forward',    'Right', 185);
INSERT INTO Player VALUES (19, 60000000, 'Midfielder', 'Left',  182);

INSERT INTO Player VALUES (20, 40000000, 'Goalkeeper', 'Right', 188);
INSERT INTO Player VALUES (21, 15000000, 'Defender',   'Right', 178);
INSERT INTO Player VALUES (22, 75000000, 'Defender',   'Right', 187);
INSERT INTO Player VALUES (23, 35000000, 'Defender',   'Right', 188);
INSERT INTO Player VALUES (24, 40000000, 'Defender',   'Left',  182);
INSERT INTO Player VALUES (25, 80000000, 'Midfielder', 'Right', 191);
INSERT INTO Player VALUES (26,100000000, 'Midfielder', 'Right', 181);
INSERT INTO Player VALUES (27, 80000000, 'Midfielder', 'Right', 173);
INSERT INTO Player VALUES (28, 90000000, 'Forward',    'Left',  171);
INSERT INTO Player VALUES (29, 45000000, 'Forward',    'Left',  180);
INSERT INTO Player VALUES (30,170000000, 'Forward',    'Left',  194);
INSERT INTO Player VALUES (31, 50000000, 'Forward',    'Right', 170);

INSERT INTO Player VALUES (32, 45000000, 'Goalkeeper', 'Right', 191);
INSERT INTO Player VALUES (33, 70000000, 'Defender',   'Right', 175);
INSERT INTO Player VALUES (34, 45000000, 'Defender',   'Right', 193);
INSERT INTO Player VALUES (35, 55000000, 'Defender',   'Right', 191);
INSERT INTO Player VALUES (36, 20000000, 'Defender',   'Left',  178);
INSERT INTO Player VALUES (37, 25000000, 'Midfielder', 'Right', 188);
INSERT INTO Player VALUES (38, 15000000, 'Midfielder', 'Right', 174);
INSERT INTO Player VALUES (39, 12000000, 'Midfielder', 'Right', 182);
INSERT INTO Player VALUES (40,100000000, 'Forward',    'Left',  175);
INSERT INTO Player VALUES (41, 35000000, 'Forward',    'Right', 175);
INSERT INTO Player VALUES (42, 70000000, 'Forward',    'Right', 187);
INSERT INTO Player VALUES (43, 45000000, 'Forward',    'Right', 178);

INSERT INTO Player VALUES (44, 35000000, 'Goalkeeper', 'Right', 188);
INSERT INTO Player VALUES (45, 25000000, 'Defender',   'Right', 175);
INSERT INTO Player VALUES (46, 20000000, 'Defender',   'Right', 185);
INSERT INTO Player VALUES (47, 10000000, 'Defender',   'Right', 187);
INSERT INTO Player VALUES (48, 12000000, 'Defender',   'Left',  184);
INSERT INTO Player VALUES (49, 25000000, 'Midfielder', 'Right', 176);
INSERT INTO Player VALUES (50, 35000000, 'Midfielder', 'Right', 184);
INSERT INTO Player VALUES (51, 22000000, 'Midfielder', 'Right', 180);
INSERT INTO Player VALUES (52, 30000000, 'Forward',    'Left',  176);
INSERT INTO Player VALUES (53, 25000000, 'Forward',    'Right', 171);
INSERT INTO Player VALUES (54, 30000000, 'Forward',    'Right', 189);
INSERT INTO Player VALUES (55, 15000000, 'Forward',    'Left',  175);

-- ============================================================
-- STADIUMS
-- ============================================================
INSERT INTO Stadium VALUES (1, 'Santiago Bernabeu', 'Madrid',      81044);
INSERT INTO Stadium VALUES (2, 'Etihad Stadium',    'Manchester',  53400);
INSERT INTO Stadium VALUES (3, 'Anfield',           'Liverpool',   61276);
INSERT INTO Stadium VALUES (4, 'Wanda Metropolitano','Madrid',     68456);

-- ============================================================
-- CLUBS (manager_id references Manager persons 1-4)
-- ============================================================
INSERT INTO Club VALUES (1, 'Royal Madrid',      1902, 1, 1);
INSERT INTO Club VALUES (2, 'Manchester Blues',   1880, 2, 2);
INSERT INTO Club VALUES (3, 'Liverpool Reds',     1892, 3, 3);
INSERT INTO Club VALUES (4, 'Atletico Madrid',    1903, 4, 4);

-- ============================================================
-- COMPETITIONS
-- ============================================================
INSERT INTO Competition VALUES (1, 'Premier League',        '2025/2026', 'England',  'League');
INSERT INTO Competition VALUES (2, 'Champions League',      '2025/2026', 'Europe',   'Cup');
INSERT INTO Competition VALUES (3, 'Premier League',        '2024/2025', 'England',  'League');

-- ============================================================
-- CONTRACTS (all players get permanent contracts)
-- Active: 2025-07-01 to 2027-06-30
-- ============================================================

-- Club 1 contracts (contract_id 1-12)
INSERT INTO Contract VALUES (1,  8,  1, '2025-07-01', '2027-06-30', 200000);
INSERT INTO Contract VALUES (2,  9,  1, '2025-07-01', '2027-06-30', 180000);
INSERT INTO Contract VALUES (3,  10, 1, '2025-07-01', '2027-06-30', 150000);
INSERT INTO Contract VALUES (4,  11, 1, '2025-07-01', '2027-06-30', 190000);
INSERT INTO Contract VALUES (5,  12, 1, '2025-07-01', '2027-06-30', 140000);
INSERT INTO Contract VALUES (6,  13, 1, '2025-07-01', '2027-06-30', 250000);
INSERT INTO Contract VALUES (7,  14, 1, '2025-07-01', '2027-06-30', 220000);
INSERT INTO Contract VALUES (8,  15, 1, '2025-07-01', '2027-06-30', 160000);
INSERT INTO Contract VALUES (9,  16, 1, '2025-07-01', '2027-06-30', 350000);
-- Vinicius old contract at Liverpool Reds (expired)
INSERT INTO Contract VALUES (50, 16, 3, '2021-07-01', '2025-06-30', 95000);
INSERT INTO Contract VALUES (10, 17, 1, '2025-07-01', '2027-06-30', 200000);
INSERT INTO Contract VALUES (11, 18, 1, '2025-07-01', '2027-06-30', 300000);
INSERT INTO Contract VALUES (12, 19, 1, '2025-07-01', '2027-06-30', 120000);

-- Club 2 contracts (contract_id 13-24)
INSERT INTO Contract VALUES (13, 20, 2, '2025-07-01', '2027-06-30', 180000);
INSERT INTO Contract VALUES (14, 21, 2, '2025-07-01', '2027-06-30', 150000);
INSERT INTO Contract VALUES (15, 22, 2, '2025-07-01', '2027-06-30', 200000);
INSERT INTO Contract VALUES (16, 23, 2, '2025-07-01', '2027-06-30', 160000);
INSERT INTO Contract VALUES (17, 24, 2, '2025-07-01', '2027-06-30', 140000);
INSERT INTO Contract VALUES (18, 25, 2, '2025-07-01', '2027-06-30', 250000);
INSERT INTO Contract VALUES (19, 26, 2, '2025-07-01', '2027-06-30', 400000);
INSERT INTO Contract VALUES (20, 27, 2, '2025-07-01', '2027-06-30', 200000);
INSERT INTO Contract VALUES (21, 28, 2, '2025-07-01', '2027-06-30', 220000);
INSERT INTO Contract VALUES (22, 29, 2, '2025-07-01', '2027-06-30', 180000);
INSERT INTO Contract VALUES (23, 30, 2, '2025-07-01', '2027-06-30', 500000);
INSERT INTO Contract VALUES (24, 31, 2, '2025-07-01', '2027-06-30', 120000);

-- Club 3 contracts (contract_id 25-36)
INSERT INTO Contract VALUES (25, 32, 3, '2025-07-01', '2027-06-30', 180000);
INSERT INTO Contract VALUES (26, 33, 3, '2025-07-01', '2027-06-30', 200000);
INSERT INTO Contract VALUES (27, 34, 3, '2025-07-01', '2027-06-30', 220000);
INSERT INTO Contract VALUES (28, 35, 3, '2025-07-01', '2027-06-30', 150000);
INSERT INTO Contract VALUES (29, 36, 3, '2025-07-01', '2027-06-30', 130000);
INSERT INTO Contract VALUES (30, 37, 3, '2025-07-01', '2027-06-30', 140000);
INSERT INTO Contract VALUES (31, 38, 3, '2025-07-01', '2027-06-30', 160000);
INSERT INTO Contract VALUES (32, 39, 3, '2025-07-01', '2027-06-30', 120000);
INSERT INTO Contract VALUES (33, 40, 3, '2025-07-01', '2027-06-30', 350000);
INSERT INTO Contract VALUES (34, 41, 3, '2025-07-01', '2027-06-30', 180000);
INSERT INTO Contract VALUES (35, 42, 3, '2025-07-01', '2027-06-30', 200000);
INSERT INTO Contract VALUES (36, 43, 3, '2025-07-01', '2027-06-30', 160000);

-- Club 4 contracts (contract_id 37-48)
INSERT INTO Contract VALUES (37, 44, 4, '2025-07-01', '2027-06-30', 170000);
INSERT INTO Contract VALUES (38, 45, 4, '2025-07-01', '2027-06-30', 100000);
INSERT INTO Contract VALUES (39, 46, 4, '2025-07-01', '2027-06-30', 110000);
INSERT INTO Contract VALUES (40, 47, 4, '2025-07-01', '2027-06-30',  90000);
INSERT INTO Contract VALUES (41, 48, 4, '2025-07-01', '2027-06-30',  80000);
INSERT INTO Contract VALUES (42, 49, 4, '2025-07-01', '2027-06-30', 150000);
INSERT INTO Contract VALUES (43, 50, 4, '2025-07-01', '2027-06-30', 140000);
INSERT INTO Contract VALUES (44, 51, 4, '2025-07-01', '2027-06-30', 120000);
INSERT INTO Contract VALUES (45, 52, 4, '2025-07-01', '2027-06-30', 250000);
INSERT INTO Contract VALUES (46, 53, 4, '2025-07-01', '2027-06-30', 100000);
INSERT INTO Contract VALUES (47, 54, 4, '2025-07-01', '2027-06-30', 180000);
INSERT INTO Contract VALUES (48, 55, 4, '2025-07-01', '2027-06-30',  80000);

-- All contracts are permanent
INSERT INTO Permanent_Contract VALUES (1);
INSERT INTO Permanent_Contract VALUES (2);
INSERT INTO Permanent_Contract VALUES (3);
INSERT INTO Permanent_Contract VALUES (4);
INSERT INTO Permanent_Contract VALUES (5);
INSERT INTO Permanent_Contract VALUES (6);
INSERT INTO Permanent_Contract VALUES (7);
INSERT INTO Permanent_Contract VALUES (8);
INSERT INTO Permanent_Contract VALUES (9);
INSERT INTO Permanent_Contract VALUES (10);
INSERT INTO Permanent_Contract VALUES (11);
INSERT INTO Permanent_Contract VALUES (12);
INSERT INTO Permanent_Contract VALUES (13);
INSERT INTO Permanent_Contract VALUES (14);
INSERT INTO Permanent_Contract VALUES (15);
INSERT INTO Permanent_Contract VALUES (16);
INSERT INTO Permanent_Contract VALUES (17);
INSERT INTO Permanent_Contract VALUES (18);
INSERT INTO Permanent_Contract VALUES (19);
INSERT INTO Permanent_Contract VALUES (20);
INSERT INTO Permanent_Contract VALUES (21);
INSERT INTO Permanent_Contract VALUES (22);
INSERT INTO Permanent_Contract VALUES (23);
INSERT INTO Permanent_Contract VALUES (24);
INSERT INTO Permanent_Contract VALUES (25);
INSERT INTO Permanent_Contract VALUES (26);
INSERT INTO Permanent_Contract VALUES (27);
INSERT INTO Permanent_Contract VALUES (28);
INSERT INTO Permanent_Contract VALUES (29);
INSERT INTO Permanent_Contract VALUES (30);
INSERT INTO Permanent_Contract VALUES (31);
INSERT INTO Permanent_Contract VALUES (32);
INSERT INTO Permanent_Contract VALUES (33);
INSERT INTO Permanent_Contract VALUES (34);
INSERT INTO Permanent_Contract VALUES (35);
INSERT INTO Permanent_Contract VALUES (36);
INSERT INTO Permanent_Contract VALUES (37);
INSERT INTO Permanent_Contract VALUES (38);
INSERT INTO Permanent_Contract VALUES (39);
INSERT INTO Permanent_Contract VALUES (40);
INSERT INTO Permanent_Contract VALUES (41);
INSERT INTO Permanent_Contract VALUES (42);
INSERT INTO Permanent_Contract VALUES (43);
INSERT INTO Permanent_Contract VALUES (44);
INSERT INTO Permanent_Contract VALUES (45);
INSERT INTO Permanent_Contract VALUES (46);
INSERT INTO Permanent_Contract VALUES (47);
INSERT INTO Permanent_Contract VALUES (48);
INSERT INTO Permanent_Contract VALUES (50); -- Vinicius old Liverpool Reds contract

-- ============================================================
-- LOAN example: Julian Alvarez (31) loaned from Club 2 to Club 4
-- ============================================================
INSERT INTO Contract VALUES (49, 31, 4, '2025-09-01', '2026-06-30', 80000);
INSERT INTO Loan_Contract VALUES (49, 24);  -- references his permanent contract at Club 2

-- ============================================================
-- TRANSFER RECORDS
-- ============================================================
INSERT INTO Transfer_Record VALUES (1, 30, 4, 2, '2025-07-01', 75000000, 'Purchase');
INSERT INTO Transfer_Record VALUES (2, 42, 2, 3, '2025-07-15', 68000000, 'Purchase');
INSERT INTO Transfer_Record VALUES (3, 31, 2, 4, '2025-09-01', 5000000,  'Loan');
-- Vinicius: Liverpool Reds → Royal Madrid, summer 2025
INSERT INTO Transfer_Record VALUES (4, 16, 3, 1, '2025-07-01', 180000000, 'Purchase');

-- ============================================================
-- COMPLETED MATCHES (past dates, with results)
-- ============================================================

-- Match 1: Royal Madrid vs Manchester Blues (Premier League)
INSERT INTO `Match` VALUES (1, 1, 1, 2, 1, '2025-09-15 16:00:00', 75000, 2, 1, 5);
-- Match 2: Liverpool Reds vs Atletico Madrid (Premier League)
INSERT INTO `Match` VALUES (2, 1, 3, 4, 3, '2025-09-15 20:00:00', 55000, 3, 0, 6);
-- Match 3: Manchester Blues vs Liverpool Reds (Premier League)
INSERT INTO `Match` VALUES (3, 1, 2, 3, 2, '2025-10-05 17:30:00', 52000, 1, 1, 7);
-- Match 4: Atletico Madrid vs Royal Madrid (Premier League)
INSERT INTO `Match` VALUES (4, 1, 4, 1, 4, '2025-10-20 21:00:00', 63000, 0, 3, 5);
-- Match 5: Royal Madrid vs Liverpool Reds (Champions League)
INSERT INTO `Match` VALUES (5, 2, 1, 3, 1, '2025-11-05 21:00:00', 78000, 2, 2, 6);
-- Match 6: Manchester Blues vs Atletico Madrid (Champions League)
INSERT INTO `Match` VALUES (6, 2, 2, 4, 2, '2025-11-05 21:00:00', 50000, 4, 1, 7);

-- ============================================================
-- MATCH PARTICIPATIONS (11 starters per club, completed matches)
-- ============================================================

-- Match 1: Royal Madrid (club 1) vs Manchester Blues (club 2)
-- Royal Madrid starters (8-18)
INSERT INTO Match_Participation VALUES (1, 8,  1, 1, 90, 'Goalkeeper', 0, 0, 0, 0, 7.5);
INSERT INTO Match_Participation VALUES (1, 9,  1, 1, 90, 'Defender',   0, 0, 0, 0, 7.0);
INSERT INTO Match_Participation VALUES (1, 10, 1, 1, 90, 'Defender',   0, 0, 1, 0, 6.5);
INSERT INTO Match_Participation VALUES (1, 11, 1, 1, 90, 'Defender',   0, 0, 0, 0, 7.0);
INSERT INTO Match_Participation VALUES (1, 12, 1, 1, 90, 'Defender',   0, 1, 0, 0, 7.5);
INSERT INTO Match_Participation VALUES (1, 13, 1, 1, 90, 'Midfielder', 0, 0, 0, 0, 8.0);
INSERT INTO Match_Participation VALUES (1, 14, 1, 1, 90, 'Midfielder', 0, 0, 0, 0, 7.5);
INSERT INTO Match_Participation VALUES (1, 15, 1, 1, 90, 'Midfielder', 1, 0, 0, 0, 8.5);
INSERT INTO Match_Participation VALUES (1, 16, 1, 1, 90, 'Forward',    1, 0, 0, 0, 9.0);
INSERT INTO Match_Participation VALUES (1, 17, 1, 1, 90, 'Forward',    0, 1, 0, 0, 7.0);
INSERT INTO Match_Participation VALUES (1, 18, 1, 1, 90, 'Forward',    0, 0, 0, 0, 6.5);
-- Manchester Blues starters (20-30)
INSERT INTO Match_Participation VALUES (1, 20, 2, 1, 90, 'Goalkeeper', 0, 0, 0, 0, 6.0);
INSERT INTO Match_Participation VALUES (1, 21, 2, 1, 90, 'Defender',   0, 0, 0, 0, 6.0);
INSERT INTO Match_Participation VALUES (1, 22, 2, 1, 90, 'Defender',   0, 0, 0, 0, 6.5);
INSERT INTO Match_Participation VALUES (1, 23, 2, 1, 90, 'Defender',   0, 0, 1, 0, 5.5);
INSERT INTO Match_Participation VALUES (1, 24, 2, 1, 90, 'Defender',   0, 0, 0, 0, 6.0);
INSERT INTO Match_Participation VALUES (1, 25, 2, 1, 90, 'Midfielder', 0, 0, 1, 0, 6.5);
INSERT INTO Match_Participation VALUES (1, 26, 2, 1, 90, 'Midfielder', 0, 0, 0, 0, 7.0);
INSERT INTO Match_Participation VALUES (1, 27, 2, 1, 90, 'Midfielder', 0, 0, 0, 0, 6.5);
INSERT INTO Match_Participation VALUES (1, 28, 2, 1, 90, 'Forward',    0, 0, 0, 0, 6.0);
INSERT INTO Match_Participation VALUES (1, 29, 2, 1, 90, 'Forward',    0, 1, 0, 0, 6.5);
INSERT INTO Match_Participation VALUES (1, 30, 2, 1, 90, 'Forward',    1, 0, 0, 0, 7.5);

-- Match 2: Liverpool Reds (club 3) vs Atletico Madrid (club 4)
-- Liverpool starters (32-42)
INSERT INTO Match_Participation VALUES (2, 32, 3, 1, 90, 'Goalkeeper', 0, 0, 0, 0, 7.0);
INSERT INTO Match_Participation VALUES (2, 33, 3, 1, 90, 'Defender',   0, 1, 0, 0, 7.5);
INSERT INTO Match_Participation VALUES (2, 34, 3, 1, 90, 'Defender',   1, 0, 0, 0, 8.0);
INSERT INTO Match_Participation VALUES (2, 35, 3, 1, 90, 'Defender',   0, 0, 0, 0, 7.0);
INSERT INTO Match_Participation VALUES (2, 36, 3, 1, 90, 'Defender',   0, 0, 0, 0, 7.0);
INSERT INTO Match_Participation VALUES (2, 37, 3, 1, 90, 'Midfielder', 0, 0, 0, 0, 7.5);
INSERT INTO Match_Participation VALUES (2, 38, 3, 1, 90, 'Midfielder', 0, 1, 0, 0, 8.0);
INSERT INTO Match_Participation VALUES (2, 39, 3, 1, 90, 'Midfielder', 0, 0, 1, 0, 6.5);
INSERT INTO Match_Participation VALUES (2, 40, 3, 1, 90, 'Forward',    2, 0, 0, 0, 9.5);
INSERT INTO Match_Participation VALUES (2, 41, 3, 1, 90, 'Forward',    0, 1, 0, 0, 7.0);
INSERT INTO Match_Participation VALUES (2, 42, 3, 1, 90, 'Forward',    0, 0, 0, 0, 6.5);
-- Atletico starters (44-54)
INSERT INTO Match_Participation VALUES (2, 44, 4, 1, 90, 'Goalkeeper', 0, 0, 0, 0, 5.5);
INSERT INTO Match_Participation VALUES (2, 45, 4, 1, 90, 'Defender',   0, 0, 1, 0, 5.0);
INSERT INTO Match_Participation VALUES (2, 46, 4, 1, 90, 'Defender',   0, 0, 0, 0, 5.5);
INSERT INTO Match_Participation VALUES (2, 47, 4, 1, 90, 'Defender',   0, 0, 0, 0, 5.0);
INSERT INTO Match_Participation VALUES (2, 48, 4, 1, 90, 'Defender',   0, 0, 0, 0, 5.5);
INSERT INTO Match_Participation VALUES (2, 49, 4, 1, 90, 'Midfielder', 0, 0, 1, 0, 5.0);
INSERT INTO Match_Participation VALUES (2, 50, 4, 1, 90, 'Midfielder', 0, 0, 0, 0, 5.5);
INSERT INTO Match_Participation VALUES (2, 51, 4, 1, 90, 'Midfielder', 0, 0, 0, 0, 5.0);
INSERT INTO Match_Participation VALUES (2, 52, 4, 1, 90, 'Forward',    0, 0, 0, 0, 5.5);
INSERT INTO Match_Participation VALUES (2, 53, 4, 1, 90, 'Forward',    0, 0, 0, 0, 5.0);
INSERT INTO Match_Participation VALUES (2, 54, 4, 1, 90, 'Forward',    0, 0, 1, 0, 4.5);

-- Match 3: Manchester Blues (club 2) vs Liverpool Reds (club 3)
INSERT INTO Match_Participation VALUES (3, 20, 2, 1, 90, 'Goalkeeper', 0, 0, 0, 0, 7.0);
INSERT INTO Match_Participation VALUES (3, 21, 2, 1, 90, 'Defender',   0, 0, 0, 0, 6.5);
INSERT INTO Match_Participation VALUES (3, 22, 2, 1, 90, 'Defender',   0, 0, 0, 0, 7.0);
INSERT INTO Match_Participation VALUES (3, 23, 2, 1, 90, 'Defender',   0, 0, 0, 0, 6.5);
INSERT INTO Match_Participation VALUES (3, 24, 2, 1, 90, 'Defender',   0, 0, 0, 0, 6.5);
INSERT INTO Match_Participation VALUES (3, 25, 2, 1, 90, 'Midfielder', 0, 0, 0, 0, 7.5);
INSERT INTO Match_Participation VALUES (3, 26, 2, 1, 90, 'Midfielder', 1, 0, 0, 0, 8.5);
INSERT INTO Match_Participation VALUES (3, 27, 2, 1, 90, 'Midfielder', 0, 1, 0, 0, 7.0);
INSERT INTO Match_Participation VALUES (3, 28, 2, 1, 90, 'Forward',    0, 0, 0, 0, 6.5);
INSERT INTO Match_Participation VALUES (3, 29, 2, 1, 90, 'Forward',    0, 0, 1, 0, 6.0);
INSERT INTO Match_Participation VALUES (3, 30, 2, 1, 90, 'Forward',    0, 0, 0, 0, 7.0);

INSERT INTO Match_Participation VALUES (3, 32, 3, 1, 90, 'Goalkeeper', 0, 0, 0, 0, 7.0);
INSERT INTO Match_Participation VALUES (3, 33, 3, 1, 90, 'Defender',   0, 0, 0, 0, 6.5);
INSERT INTO Match_Participation VALUES (3, 34, 3, 1, 90, 'Defender',   0, 0, 0, 0, 7.5);
INSERT INTO Match_Participation VALUES (3, 35, 3, 1, 90, 'Defender',   0, 0, 0, 0, 6.5);
INSERT INTO Match_Participation VALUES (3, 36, 3, 1, 90, 'Defender',   0, 0, 0, 0, 6.5);
INSERT INTO Match_Participation VALUES (3, 37, 3, 1, 90, 'Midfielder', 0, 0, 0, 0, 7.0);
INSERT INTO Match_Participation VALUES (3, 38, 3, 1, 90, 'Midfielder', 0, 0, 0, 0, 7.0);
INSERT INTO Match_Participation VALUES (3, 39, 3, 1, 90, 'Midfielder', 0, 0, 0, 0, 6.5);
INSERT INTO Match_Participation VALUES (3, 40, 3, 1, 90, 'Forward',    1, 0, 0, 0, 8.0);
INSERT INTO Match_Participation VALUES (3, 41, 3, 1, 90, 'Forward',    0, 1, 0, 0, 7.0);
INSERT INTO Match_Participation VALUES (3, 42, 3, 1, 90, 'Forward',    0, 0, 0, 0, 6.0);

-- Match 4: Atletico (club 4) vs Royal Madrid (club 1)
INSERT INTO Match_Participation VALUES (4, 44, 4, 1, 90, 'Goalkeeper', 0, 0, 0, 0, 6.0);
INSERT INTO Match_Participation VALUES (4, 45, 4, 1, 90, 'Defender',   0, 0, 0, 0, 5.5);
INSERT INTO Match_Participation VALUES (4, 46, 4, 1, 90, 'Defender',   0, 0, 0, 0, 5.5);
INSERT INTO Match_Participation VALUES (4, 47, 4, 1, 90, 'Defender',   0, 0, 1, 0, 5.0);
INSERT INTO Match_Participation VALUES (4, 48, 4, 1, 90, 'Defender',   0, 0, 0, 0, 5.5);
INSERT INTO Match_Participation VALUES (4, 49, 4, 1, 90, 'Midfielder', 0, 0, 0, 0, 5.5);
INSERT INTO Match_Participation VALUES (4, 50, 4, 1, 90, 'Midfielder', 0, 0, 0, 0, 5.0);
INSERT INTO Match_Participation VALUES (4, 51, 4, 1, 90, 'Midfielder', 0, 0, 0, 0, 5.0);
INSERT INTO Match_Participation VALUES (4, 52, 4, 1, 90, 'Forward',    0, 0, 0, 0, 5.0);
INSERT INTO Match_Participation VALUES (4, 53, 4, 1, 90, 'Forward',    0, 0, 0, 0, 5.0);
INSERT INTO Match_Participation VALUES (4, 54, 4, 1, 90, 'Forward',    0, 0, 1, 0, 4.5);

INSERT INTO Match_Participation VALUES (4, 8,  1, 1, 90, 'Goalkeeper', 0, 0, 0, 0, 8.0);
INSERT INTO Match_Participation VALUES (4, 9,  1, 1, 90, 'Defender',   0, 0, 0, 0, 7.5);
INSERT INTO Match_Participation VALUES (4, 10, 1, 1, 90, 'Defender',   0, 0, 0, 0, 7.5);
INSERT INTO Match_Participation VALUES (4, 11, 1, 1, 90, 'Defender',   0, 0, 0, 0, 7.0);
INSERT INTO Match_Participation VALUES (4, 12, 1, 1, 90, 'Defender',   0, 0, 0, 0, 7.0);
INSERT INTO Match_Participation VALUES (4, 13, 1, 1, 90, 'Midfielder', 1, 0, 0, 0, 8.5);
INSERT INTO Match_Participation VALUES (4, 14, 1, 1, 90, 'Midfielder', 0, 1, 0, 0, 8.0);
INSERT INTO Match_Participation VALUES (4, 15, 1, 1, 90, 'Midfielder', 0, 1, 0, 0, 8.0);
INSERT INTO Match_Participation VALUES (4, 16, 1, 1, 90, 'Forward',    2, 0, 0, 0, 9.5);
INSERT INTO Match_Participation VALUES (4, 17, 1, 1, 90, 'Forward',    0, 1, 0, 0, 7.5);
INSERT INTO Match_Participation VALUES (4, 18, 1, 1, 90, 'Forward',    0, 0, 0, 0, 7.0);

-- Match 5: Royal Madrid (club 1) vs Liverpool Reds (club 3) - Champions League
INSERT INTO Match_Participation VALUES (5, 8,  1, 1, 90, 'Goalkeeper', 0, 0, 0, 0, 6.5);
INSERT INTO Match_Participation VALUES (5, 9,  1, 1, 90, 'Defender',   0, 0, 0, 0, 6.5);
INSERT INTO Match_Participation VALUES (5, 10, 1, 1, 90, 'Defender',   0, 0, 0, 0, 6.5);
INSERT INTO Match_Participation VALUES (5, 11, 1, 1, 90, 'Defender',   0, 0, 0, 0, 6.0);
INSERT INTO Match_Participation VALUES (5, 12, 1, 1, 90, 'Defender',   0, 0, 0, 0, 6.5);
INSERT INTO Match_Participation VALUES (5, 13, 1, 1, 90, 'Midfielder', 0, 1, 0, 0, 7.5);
INSERT INTO Match_Participation VALUES (5, 14, 1, 1, 90, 'Midfielder', 0, 0, 0, 0, 7.0);
INSERT INTO Match_Participation VALUES (5, 15, 1, 1, 90, 'Midfielder', 1, 0, 0, 0, 8.0);
INSERT INTO Match_Participation VALUES (5, 16, 1, 1, 90, 'Forward',    1, 0, 0, 0, 8.5);
INSERT INTO Match_Participation VALUES (5, 17, 1, 1, 90, 'Forward',    0, 1, 0, 0, 7.0);
INSERT INTO Match_Participation VALUES (5, 18, 1, 1, 90, 'Forward',    0, 0, 0, 0, 6.5);

INSERT INTO Match_Participation VALUES (5, 32, 3, 1, 90, 'Goalkeeper', 0, 0, 0, 0, 7.0);
INSERT INTO Match_Participation VALUES (5, 33, 3, 1, 90, 'Defender',   0, 0, 0, 0, 6.5);
INSERT INTO Match_Participation VALUES (5, 34, 3, 1, 90, 'Defender',   0, 0, 0, 0, 7.0);
INSERT INTO Match_Participation VALUES (5, 35, 3, 1, 90, 'Defender',   0, 0, 0, 0, 6.5);
INSERT INTO Match_Participation VALUES (5, 36, 3, 1, 90, 'Defender',   0, 1, 0, 0, 7.0);
INSERT INTO Match_Participation VALUES (5, 37, 3, 1, 90, 'Midfielder', 0, 0, 0, 0, 7.0);
INSERT INTO Match_Participation VALUES (5, 38, 3, 1, 90, 'Midfielder', 0, 0, 1, 0, 6.5);
INSERT INTO Match_Participation VALUES (5, 39, 3, 1, 90, 'Midfielder', 0, 0, 0, 0, 6.5);
INSERT INTO Match_Participation VALUES (5, 40, 3, 1, 90, 'Forward',    1, 0, 0, 0, 8.5);
INSERT INTO Match_Participation VALUES (5, 41, 3, 1, 90, 'Forward',    1, 0, 0, 0, 8.0);
INSERT INTO Match_Participation VALUES (5, 42, 3, 1, 90, 'Forward',    0, 1, 0, 0, 7.0);

-- Match 6: Manchester Blues (club 2) vs Atletico Madrid (club 4) - Champions League
INSERT INTO Match_Participation VALUES (6, 20, 2, 1, 90, 'Goalkeeper', 0, 0, 0, 0, 7.5);
INSERT INTO Match_Participation VALUES (6, 21, 2, 1, 90, 'Defender',   0, 0, 0, 0, 7.0);
INSERT INTO Match_Participation VALUES (6, 22, 2, 1, 90, 'Defender',   0, 0, 0, 0, 7.5);
INSERT INTO Match_Participation VALUES (6, 23, 2, 1, 90, 'Defender',   0, 0, 0, 0, 7.0);
INSERT INTO Match_Participation VALUES (6, 24, 2, 1, 90, 'Defender',   0, 1, 0, 0, 7.5);
INSERT INTO Match_Participation VALUES (6, 25, 2, 1, 90, 'Midfielder', 1, 0, 0, 0, 8.0);
INSERT INTO Match_Participation VALUES (6, 26, 2, 1, 90, 'Midfielder', 1, 1, 0, 0, 9.0);
INSERT INTO Match_Participation VALUES (6, 27, 2, 1, 90, 'Midfielder', 0, 1, 0, 0, 7.5);
INSERT INTO Match_Participation VALUES (6, 28, 2, 1, 90, 'Forward',    0, 0, 0, 0, 7.0);
INSERT INTO Match_Participation VALUES (6, 29, 2, 1, 90, 'Forward',    0, 1, 0, 0, 7.0);
INSERT INTO Match_Participation VALUES (6, 30, 2, 1, 90, 'Forward',    2, 0, 0, 0, 9.5);

INSERT INTO Match_Participation VALUES (6, 44, 4, 1, 90, 'Goalkeeper', 0, 0, 0, 0, 5.5);
INSERT INTO Match_Participation VALUES (6, 45, 4, 1, 90, 'Defender',   0, 0, 1, 0, 5.0);
INSERT INTO Match_Participation VALUES (6, 46, 4, 1, 90, 'Defender',   0, 0, 0, 0, 5.5);
INSERT INTO Match_Participation VALUES (6, 47, 4, 1, 90, 'Defender',   0, 0, 0, 0, 5.0);
INSERT INTO Match_Participation VALUES (6, 48, 4, 1, 90, 'Defender',   0, 0, 0, 0, 5.0);
INSERT INTO Match_Participation VALUES (6, 49, 4, 1, 90, 'Midfielder', 0, 0, 0, 0, 5.5);
INSERT INTO Match_Participation VALUES (6, 50, 4, 1, 90, 'Midfielder', 0, 0, 0, 0, 5.0);
INSERT INTO Match_Participation VALUES (6, 51, 4, 1, 90, 'Midfielder', 0, 1, 0, 0, 6.0);
INSERT INTO Match_Participation VALUES (6, 52, 4, 1, 90, 'Forward',    1, 0, 0, 0, 7.0);
INSERT INTO Match_Participation VALUES (6, 53, 4, 1, 90, 'Forward',    0, 0, 0, 0, 5.0);
INSERT INTO Match_Participation VALUES (6, 54, 4, 1, 90, 'Forward',    0, 0, 0, 1, 3.0);

-- ============================================================
-- SCHEDULED FUTURE MATCHES (no results yet)
-- ============================================================
INSERT INTO `Match` (match_id, competition_id, home_club_id, away_club_id, stadium_id, match_datetime, referee_id)
VALUES (7, 1, 1, 3, 1, '2026-05-10 17:00:00', 5);
INSERT INTO `Match` (match_id, competition_id, home_club_id, away_club_id, stadium_id, match_datetime, referee_id)
VALUES (8, 1, 4, 2, 4, '2026-05-10 20:00:00', 6);
INSERT INTO `Match` (match_id, competition_id, home_club_id, away_club_id, stadium_id, match_datetime, referee_id)
VALUES (9, 2, 3, 2, 3, '2026-05-17 21:00:00', 7);
INSERT INTO `Match` (match_id, competition_id, home_club_id, away_club_id, stadium_id, match_datetime, referee_id)
VALUES (10, 1, 2, 1, 2, '2026-06-01 16:00:00', 5);
