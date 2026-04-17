-- Auto-generated from initial_data.xlsx
-- Run AFTER schema.sql, BEFORE triggers.sql

USE DB;

-- Stadiums
INSERT INTO Stadium VALUES (1, 'Etihad Stadium', 'Manchester', 53400);
INSERT INTO Stadium VALUES (2, 'Ülker Stadyumu', 'Istanbul', 50530);
INSERT INTO Stadium VALUES (3, 'RAMS Park', 'Istanbul', 52280);
INSERT INTO Stadium VALUES (4, 'Tüpraş Stadyumu', 'Istanbul', 42590);
INSERT INTO Stadium VALUES (5, 'Anfield', 'Liverpool', 61276);
INSERT INTO Stadium VALUES (6, 'Mersin Stadyumu', 'Mersin', 25534);
INSERT INTO Stadium VALUES (7, 'Atatürk Olympic Stadium', 'Istanbul', 74753);
INSERT INTO Stadium VALUES (8, 'Gürsel Aksel Stadium', 'Izmir', 20035);
INSERT INTO Stadium VALUES (9, 'Papara Park', 'Trabzon', 40782);
INSERT INTO Stadium VALUES (10, 'Corendon Airlines Park', 'Antalya', 32537);
INSERT INTO Stadium VALUES (11, 'Eryaman Stadium', 'Ankara', 22000);
INSERT INTO Stadium VALUES (12, 'Liberty Stadium', 'Swansea', 20532);

-- Persons: Referees
INSERT INTO Person VALUES (1001, 'Cuneyt', 'Cakir', 'Türkiye', '1976-11-23');
INSERT INTO Referee VALUES (1001, 'FIFA', 20);
INSERT INTO Person VALUES (1002, 'Halil', 'Meler', 'Türkiye', '1986-08-01');
INSERT INTO Referee VALUES (1002, 'FIFA', 10);
INSERT INTO Person VALUES (1003, 'Michael', 'Oliver', 'England', '1985-02-20');
INSERT INTO Referee VALUES (1003, 'UEFA Elite', 15);
INSERT INTO Person VALUES (1004, 'Anthony', 'Taylor', 'England', '1978-10-20');
INSERT INTO Referee VALUES (1004, 'UEFA Elite', 18);
INSERT INTO Person VALUES (1005, 'Szymon', 'Marciniak', 'Poland', '1981-01-07');
INSERT INTO Referee VALUES (1005, 'FIFA', 14);
INSERT INTO Person VALUES (1006, 'Stephanie', 'Frappart', 'France', '1983-12-14');
INSERT INTO Referee VALUES (1006, 'FIFA', 12);
INSERT INTO Person VALUES (1007, 'Ali', 'Palabiyik', 'Türkiye', '1981-08-14');
INSERT INTO Referee VALUES (1007, 'National', 12);

-- Persons: Managers
INSERT INTO Person VALUES (2001, 'Fatih', 'Terim', 'Türkiye', '1953-09-04');
INSERT INTO Manager VALUES (2001, '4-4-2', 'Expert');
INSERT INTO Person VALUES (2002, 'Jorge', 'Jesus', 'Portugal', '1954-07-24');
INSERT INTO Manager VALUES (2002, '4-1-3-2', 'Expert');
INSERT INTO Person VALUES (2003, 'Ismail', 'Kartal', 'Türkiye', '1961-05-25');
INSERT INTO Manager VALUES (2003, '4-2-3-1', 'Advanced');
INSERT INTO Person VALUES (2004, 'Pep', 'Guardiola', 'Spain', '1971-01-18');
INSERT INTO Manager VALUES (2004, '4-3-3', 'Expert');
INSERT INTO Person VALUES (2005, 'Jurgen', 'Klopp', 'Germany', '1967-06-16');
INSERT INTO Manager VALUES (2005, '4-3-3', 'Expert');
INSERT INTO Person VALUES (2006, 'Sergen', 'Yalcin', 'Türkiye', '1972-10-05');
INSERT INTO Manager VALUES (2006, '4-2-3-1', 'Advanced');
INSERT INTO Person VALUES (2007, 'Okan', 'Buruk', 'Türkiye', '1973-10-19');
INSERT INTO Manager VALUES (2007, '4-2-3-1', 'Advanced');
INSERT INTO Person VALUES (2008, 'Jose', 'Mourinho', 'Portugal', '1963-01-26');
INSERT INTO Manager VALUES (2008, '4-2-3-1', 'Expert');
INSERT INTO Person VALUES (2009, 'Volkan', 'Demirel', 'Türkiye', '1981-10-27');
INSERT INTO Manager VALUES (2009, '4-2-3-1', 'Intermediate');
INSERT INTO Person VALUES (2010, 'Anonymus', 'Coach', 'Zimbabve', '2000-01-01');
INSERT INTO Manager VALUES (2010, '4-3-3', 'Intermediate');

-- Persons: Players
INSERT INTO Person VALUES (1, 'Burak', 'Yilmaz', 'Türkiye', '1985-07-15');
INSERT INTO Player VALUES (1, 500000.0, 'Forward', 'Right', 188);
INSERT INTO Person VALUES (2, 'Arda', 'Guler', 'Türkiye', '2005-02-25');
INSERT INTO Player VALUES (2, 30000000.0, 'Midfielder', 'Left', 175);
INSERT INTO Person VALUES (3, 'Gedson', 'Fernandes', 'Portugal', '1999-01-09');
INSERT INTO Player VALUES (3, 15000000.0, 'Midfielder', 'Right', 181);
INSERT INTO Person VALUES (4, 'Fernando', 'Muslera', 'Uruguay', '1986-06-16');
INSERT INTO Player VALUES (4, 1000000.0, 'Goalkeeper', 'Right', 190);
INSERT INTO Person VALUES (5, 'Altay', 'Bayindir', 'Türkiye', '1998-04-14');
INSERT INTO Player VALUES (5, 10000000.0, 'Goalkeeper', 'Right', 198);
INSERT INTO Person VALUES (6, 'Ferdi', 'Kadioglu', 'Türkiye', '1999-10-07');
INSERT INTO Player VALUES (6, 20000000.0, 'Defender', 'Right', 174);
INSERT INTO Person VALUES (7, 'Caglar', 'Soyuncu', 'Türkiye', '1996-05-23');
INSERT INTO Player VALUES (7, 15000000.0, 'Defender', 'Right', 185);
INSERT INTO Person VALUES (8, 'Ozan', 'Kabak', 'Türkiye', '2000-03-25');
INSERT INTO Player VALUES (8, 12000000.0, 'Defender', 'Right', 186);
INSERT INTO Person VALUES (9, 'Salih', 'Ozcan', 'Türkiye', '1998-01-11');
INSERT INTO Player VALUES (9, 13000000.0, 'Midfielder', 'Right', 182);
INSERT INTO Person VALUES (10, 'Hakan', 'Calhanoglu', 'Türkiye', '1994-02-08');
INSERT INTO Player VALUES (10, 35000000.0, 'Midfielder', 'Right', 178);
INSERT INTO Person VALUES (11, 'Orkun', 'Kokcu', 'Türkiye', '2000-12-29');
INSERT INTO Player VALUES (11, 30000000.0, 'Midfielder', 'Right', 175);
INSERT INTO Person VALUES (12, 'Kerem', 'Akturkoglu', 'Türkiye', '1998-10-21');
INSERT INTO Player VALUES (12, 18000000.0, 'Forward', 'Right', 173);
INSERT INTO Person VALUES (13, 'Baris', 'Yilmaz', 'Türkiye', '2000-05-23');
INSERT INTO Player VALUES (13, 15000000.0, 'Forward', 'Right', 186);
INSERT INTO Person VALUES (14, 'Enes', 'Unal', 'Türkiye', '1997-05-10');
INSERT INTO Player VALUES (14, 25000000.0, 'Forward', 'Right', 187);
INSERT INTO Person VALUES (15, 'Cengiz', 'Under', 'Türkiye', '1997-07-14');
INSERT INTO Player VALUES (15, 16000000.0, 'Forward', 'Left', 173);
INSERT INTO Person VALUES (16, 'Abdullah', 'Rüzgar', 'Türkiye', '2003-06-26');
INSERT INTO Player VALUES (16, 185000000.0, 'Forward', 'Both', 183);
INSERT INTO Person VALUES (17, 'Berk', 'Göktaş', 'Türkiye', '2004-01-01');
INSERT INTO Player VALUES (17, 78000000.0, 'Forward', 'Right', 178);
INSERT INTO Person VALUES (18, 'Poyraz', 'Güneşçelik', 'Türkiye', '2003-12-12');
INSERT INTO Player VALUES (18, 123000000.0, 'Midfielder', 'Right', 177);

-- Clubs
INSERT INTO Club VALUES (1, 'Galatasaray SK', 1905, 3, 2007);
INSERT INTO Club VALUES (2, 'Fenerbahçe SK', 1907, 2, 2008);
INSERT INTO Club VALUES (3, 'Beşiktaş JK', 1903, 4, 2006);
INSERT INTO Club VALUES (4, 'Manchester City FC', 1880, 1, 2004);
INSERT INTO Club VALUES (5, 'Liverpool FC', 1892, 5, 2005);
INSERT INTO Club VALUES (6, 'Trabzonspor', 1967, 9, 2001);
INSERT INTO Club VALUES (7, 'Hatayspor', 1967, 6, 2009);
INSERT INTO Club VALUES (8, 'YENIDEN DOGUS', 2025, 12, 2010);
INSERT INTO Club VALUES (9, 'Real Callejon', 2020, NULL, NULL);
INSERT INTO Club VALUES (10, 'ALJANDAL FC', 2020, NULL, NULL);
INSERT INTO Club VALUES (11, 'Galtza CF', 2020, NULL, NULL);
INSERT INTO Club VALUES (12, 'Catania FCA', 2020, NULL, NULL);
INSERT INTO Club VALUES (13, 'FC PPS', 2020, NULL, NULL);
INSERT INTO Club VALUES (14, 'Parco FCI', 2020, NULL, NULL);
INSERT INTO Club VALUES (15, 'Carini FC', 1999, NULL, NULL);
INSERT INTO Club VALUES (16, 'seb degage', 1977, NULL, NULL);

-- Competitions
INSERT INTO Competition VALUES (1, 'Super Lig', '2025/2026', 'Türkiye', 'League');
INSERT INTO Competition VALUES (2, 'Türkiye Kupasi', '2025/2026', 'Türkiye', 'Cup');
INSERT INTO Competition VALUES (3, 'Premier League', '2025/2026', 'England', 'League');
INSERT INTO Competition VALUES (4, 'FA Cup', '2025/2026', 'England', 'Cup');
INSERT INTO Competition VALUES (5, 'UEFA Champions League', '2025/2026', 'International', 'Cup');
INSERT INTO Competition VALUES (6, 'UEFA Europa League', '2025/2026', 'International', 'Cup');
INSERT INTO Competition VALUES (7, 'Super Lig', '2024/2025', 'Türkiye', 'League');
INSERT INTO Competition VALUES (8, 'Premier League', '2024/2025', 'England', 'League');
INSERT INTO Competition VALUES (9, 'Pro Clubs League', '2025/2026', 'International', 'League');
INSERT INTO Competition VALUES (10, 'Pro Clubs Playoffs', '2025/2026', 'International', 'League');

-- Contracts (base)
INSERT INTO Contract VALUES (1, 2, 1, '2024-01-01', '2028-01-01', 50000.0);
INSERT INTO Contract VALUES (2, 2, 2, '2025-06-01', '2026-06-01', 20000.0);
INSERT INTO Contract VALUES (3, 2, 3, '2025-08-01', '2029-08-01', 80000.0);
INSERT INTO Contract VALUES (4, 1, 4, '2025-01-01', '2026-01-01', 10000.0);
INSERT INTO Contract VALUES (5, 5, 1, '2024-07-01', '2028-06-30', 40000.0);
INSERT INTO Contract VALUES (6, 6, 1, '2023-07-01', '2027-06-30', 55000.0);
INSERT INTO Contract VALUES (7, 7, 1, '2024-01-15', '2027-06-30', 60000.0);
INSERT INTO Contract VALUES (8, 8, 1, '2024-08-01', '2028-06-30', 45000.0);
INSERT INTO Contract VALUES (9, 9, 1, '2023-08-01', '2026-06-30', 50000.0);
INSERT INTO Contract VALUES (10, 10, 1, '2022-07-01', '2026-06-30', 90000.0);
INSERT INTO Contract VALUES (11, 10, 3, '2018-07-01', '2022-06-30', 75000.0);
INSERT INTO Contract VALUES (12, 11, 1, '2024-07-01', '2029-06-30', 80000.0);
INSERT INTO Contract VALUES (13, 12, 1, '2021-07-01', '2026-06-30', 65000.0);
INSERT INTO Contract VALUES (14, 13, 1, '2022-07-01', '2027-06-30', 50000.0);
INSERT INTO Contract VALUES (15, 14, 2, '2023-07-01', '2027-06-30', 70000.0);
INSERT INTO Contract VALUES (16, 16, 8, '2026-01-01', '2028-12-12', 150000.0);
INSERT INTO Contract VALUES (17, 17, 8, '2026-01-01', '2028-12-12', 99000.0);
INSERT INTO Contract VALUES (18, 18, 8, '2026-02-01', '2028-12-12', 175000.0);

-- Permanent Contracts
INSERT INTO Permanent_Contract VALUES (1);
INSERT INTO Permanent_Contract VALUES (3);
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

-- Loan Contracts
INSERT INTO Loan_Contract VALUES (2, 1);
INSERT INTO Loan_Contract VALUES (4, NULL); -- intentionally invalid: no parent permanent

-- Transfer Records
INSERT INTO Transfer_Record VALUES (1, 10, 3, 1, '2022-07-01', 35000000.0, 'Purchase');
INSERT INTO Transfer_Record VALUES (2, 4, 3, 1, '2023-08-01', 0.0, 'Free');
INSERT INTO Transfer_Record VALUES (3, 2, 5, 1, '2024-01-01', 20000000.0, 'Purchase');
INSERT INTO Transfer_Record VALUES (4, 5, 2, 1, '2024-07-01', 10000000.0, 'Purchase');
INSERT INTO Transfer_Record VALUES (5, 1, NULL, 4, '2025-01-01', 500000.0, 'Loan');
INSERT INTO Transfer_Record VALUES (6, 2, 1, 2, '2025-06-01', 1500000.0, 'Loan');
INSERT INTO Transfer_Record VALUES (7, 2, 1, 3, '2025-08-01', 30000000.0, 'Purchase');
INSERT INTO Transfer_Record VALUES (8, 6, 2, 1, '2023-07-01', 20000000.0, 'Purchase');
INSERT INTO Transfer_Record VALUES (9, 7, 8, 1, '2024-01-15', 15000000.0, 'Purchase');
INSERT INTO Transfer_Record VALUES (10, 14, 1, 2, '2023-07-01', 25000000.0, 'Purchase');
INSERT INTO Transfer_Record VALUES (11, 16, NULL, 8, '2026-01-01', 0.0, 'Free');
INSERT INTO Transfer_Record VALUES (12, 17, NULL, 8, '2026-02-01', 0.0, 'Free');
INSERT INTO Transfer_Record VALUES (13, 18, NULL, 8, '2026-01-01', 0.0, 'Free');

-- Matches
INSERT INTO `Match` VALUES (1, 1, 1, 2, 1, '2026-04-15 19:00:00', 40000, 2, 1, 1001);
INSERT INTO `Match` VALUES (2, 1, 3, 4, 1, '2026-04-15 20:00:00', NULL, NULL, NULL, 1001);
INSERT INTO `Match` VALUES (3, 1, 1, 3, 1, '2025-10-10 19:00:00', 44000, 3, 0, 1002);
INSERT INTO `Match` VALUES (4, 1, 3, 1, 3, '2025-11-22 20:00:00', 51000, 1, 1, 1001);
INSERT INTO `Match` VALUES (5, 2, 5, 6, 4, '2026-05-01 21:00:00', NULL, NULL, NULL, 1002);
INSERT INTO `Match` VALUES (6, 1, 2, 5, 2, '2026-05-10 18:00:00', 55000, NULL, NULL, 1001);
INSERT INTO `Match` VALUES (7, 1, 6, 7, 5, '2026-05-15 14:00:00', NULL, NULL, NULL, 1002);
INSERT INTO `Match` VALUES (8, 1, 7, 1, 6, '2026-05-15 15:00:00', NULL, NULL, NULL, 1002);
INSERT INTO `Match` VALUES (9, 9, 8, 9, 12, '2026-03-13 15:00:00', 20123, 1, 5, 1003);
INSERT INTO `Match` VALUES (10, 9, 8, 10, 12, '2026-03-13 17:00:00', 19599, 1, 3, 1004);
INSERT INTO `Match` VALUES (11, 9, 8, 11, 12, '2026-03-13 21:00:00', 18000, 4, 5, 1005);
INSERT INTO `Match` VALUES (12, 9, 8, 12, 12, '2026-03-13 23:00:00', 20000, 5, 6, 1003);
INSERT INTO `Match` VALUES (13, 9, 8, 13, 12, '2026-03-14 17:00:00', 22000, 3, 2, 1004);
INSERT INTO `Match` VALUES (14, 10, 8, 14, 12, '2026-03-12 12:00:00', 22400, 7, 3, 1002);
INSERT INTO `Match` VALUES (15, 10, 8, 15, 12, '2026-03-12 14:00:00', 22400, 6, 1, 1006);
INSERT INTO `Match` VALUES (16, 10, 8, 16, 12, '2026-03-10 14:00:00', 21900, 5, 3, 1005);

-- Match Participation
INSERT INTO Match_Participation VALUES (1, 4, 1, 1, 90, 'GK', 0, 0, 0, 0, 7.5);
INSERT INTO Match_Participation VALUES (1, 2, 1, 1, 90, 'CM', 1, 0, 0, 0, 8.2);
INSERT INTO Match_Participation VALUES (1, 3, 1, 1, 90, 'CAM', 0, 1, 1, 0, 7.0);
INSERT INTO Match_Participation VALUES (1, 1, 1, 1, 90, 'ST', 1, 0, 0, 0, 7.8);
INSERT INTO Match_Participation VALUES (1, 14, 2, 1, 90, 'ST', 1, 0, 0, 0, 7.2);
INSERT INTO Match_Participation VALUES (1, 15, 2, 1, 90, 'CF', 0, 1, 0, 0, 6.8);
INSERT INTO Match_Participation VALUES (3, 10, 1, 1, 90, 'CDM', 1, 2, 0, 0, 9.2);
INSERT INTO Match_Participation VALUES (3, 12, 1, 1, 85, 'LW', 2, 0, 0, 0, 8.8);
INSERT INTO Match_Participation VALUES (3, 11, 1, 1, 90, 'RM', 0, 1, 1, 0, 7.5);
INSERT INTO Match_Participation VALUES (3, 5, 1, 1, 90, 'GK', 0, 0, 0, 0, 7.8);
INSERT INTO Match_Participation VALUES (3, 7, 1, 1, 90, 'RB', 0, 0, 1, 0, 7.1);
INSERT INTO Match_Participation VALUES (3, 9, 1, 0, 5, 'ST', 0, 0, 0, 0, 6.0);
INSERT INTO Match_Participation VALUES (3, 16, 3, 1, 90, 'GK', 0, 0, 0, 0, 5.5);
INSERT INTO Match_Participation VALUES (3, 17, 3, 1, 90, 'CM', 0, 0, 1, 0, 6.0);
INSERT INTO Match_Participation VALUES (4, 10, 1, 1, 90, 'CAM', 1, 0, 0, 0, 8.0);
INSERT INTO Match_Participation VALUES (4, 12, 1, 1, 90, 'RW', 0, 1, 0, 0, 7.4);
INSERT INTO Match_Participation VALUES (4, 6, 1, 1, 90, 'CB', 0, 0, 0, 0, 7.0);
INSERT INTO Match_Participation VALUES (4, 16, 3, 1, 90, 'GK', 0, 0, 0, 0, 7.1);
INSERT INTO Match_Participation VALUES (4, 18, 3, 1, 90, 'ST', 1, 0, 0, 0, 7.8);
INSERT INTO Match_Participation VALUES (9, 16, 8, 1, 90, 'ST', 1, 0, 0, 0, 7.2);
INSERT INTO Match_Participation VALUES (9, 17, 8, 1, 90, 'LW', 0, 1, 0, 0, 7.0);
INSERT INTO Match_Participation VALUES (9, 18, 8, 1, 90, 'CAM', 0, 0, 0, 0, 6.7);
INSERT INTO Match_Participation VALUES (10, 16, 8, 1, 90, 'ST', 1, 0, 0, 0, 7.8);
INSERT INTO Match_Participation VALUES (10, 17, 8, 1, 90, 'LW', 0, 0, 1, 0, 6.6);
INSERT INTO Match_Participation VALUES (10, 18, 8, 1, 90, 'CAM', 0, 1, 0, 0, 9.1);
INSERT INTO Match_Participation VALUES (11, 16, 8, 1, 90, 'ST', 1, 0, 0, 0, 7.4);
INSERT INTO Match_Participation VALUES (11, 17, 8, 1, 90, 'LW', 2, 1, 0, 0, 8.8);
INSERT INTO Match_Participation VALUES (11, 18, 8, 1, 90, 'CAM', 1, 1, 1, 0, 9.0);
INSERT INTO Match_Participation VALUES (12, 16, 8, 1, 90, 'ST', 5, 0, 0, 0, 10.0);
INSERT INTO Match_Participation VALUES (12, 17, 8, 1, 90, 'LW', 0, 1, 0, 0, 7.0);
INSERT INTO Match_Participation VALUES (12, 18, 8, 1, 90, 'CAM', 0, 2, 0, 0, 8.6);
INSERT INTO Match_Participation VALUES (13, 16, 8, 1, 90, 'ST', 2, 0, 0, 0, 8.6);
INSERT INTO Match_Participation VALUES (13, 17, 8, 1, 90, 'LW', 1, 2, 0, 0, 8.5);
INSERT INTO Match_Participation VALUES (13, 18, 8, 1, 90, 'CAM', 0, 1, 0, 0, 9.6);
INSERT INTO Match_Participation VALUES (14, 16, 8, 1, 90, 'ST', 5, 0, 0, 0, 10.0);
INSERT INTO Match_Participation VALUES (14, 17, 8, 1, 90, 'LW', 0, 0, 0, 0, 8.9);
INSERT INTO Match_Participation VALUES (14, 18, 8, 1, 90, 'CAM', 2, 2, 0, 0, 10.0);
INSERT INTO Match_Participation VALUES (15, 16, 8, 1, 90, 'ST', 2, 1, 0, 0, 10.0);
INSERT INTO Match_Participation VALUES (15, 17, 8, 1, 90, 'LW', 3, 3, 0, 0, 9.6);
INSERT INTO Match_Participation VALUES (15, 18, 8, 1, 90, 'CAM', 1, 0, 0, 0, 10.0);
INSERT INTO Match_Participation VALUES (16, 16, 8, 1, 90, 'ST', 2, 2, 0, 0, 10.0);
INSERT INTO Match_Participation VALUES (16, 17, 8, 1, 90, 'LW', 2, 1, 0, 0, 9.1);
INSERT INTO Match_Participation VALUES (16, 18, 8, 1, 90, 'CAM', 1, 2, 0, 0, 8.9);