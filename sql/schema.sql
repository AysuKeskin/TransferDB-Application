-- TransferDB Full Schema
-- Run: mysql -u root < sql/schema.sql

DROP DATABASE IF EXISTS DB;
CREATE DATABASE DB;
USE DB;

-- -------------------------------------------------------
-- Person (superclass)
-- -------------------------------------------------------
CREATE TABLE Person (
    person_id INT,
    name VARCHAR(50) NOT NULL,
    surname VARCHAR(50) NOT NULL,
    nationality VARCHAR(50) NOT NULL,
    date_of_birth DATE NOT NULL,
    PRIMARY KEY (person_id)
);

-- -------------------------------------------------------
-- Player (subclass of Person)
-- -------------------------------------------------------
CREATE TABLE Player (
    person_id INT,
    market_value DECIMAL(15,2) NOT NULL,
    main_position VARCHAR(20) NOT NULL,
    strong_foot VARCHAR(10) NOT NULL,
    height INT NOT NULL,
    PRIMARY KEY (person_id),
    FOREIGN KEY (person_id) REFERENCES Person(person_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CHECK (market_value > 0),
    CHECK (height > 0),
    CHECK (strong_foot IN ('Right', 'Left', 'Both')),
    CHECK (main_position IN ('Goalkeeper', 'Defender', 'Midfielder', 'Forward'))
);

-- -------------------------------------------------------
-- Manager (subclass of Person)
-- -------------------------------------------------------
CREATE TABLE Manager (
    person_id INT,
    preferred_formation VARCHAR(20) NOT NULL,
    experience_level VARCHAR(20) NOT NULL,
    PRIMARY KEY (person_id),
    FOREIGN KEY (person_id) REFERENCES Person(person_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- -------------------------------------------------------
-- Referee (subclass of Person)
-- -------------------------------------------------------
CREATE TABLE Referee (
    person_id INT,
    license_level VARCHAR(20) NOT NULL,
    years_of_experience INT NOT NULL,
    PRIMARY KEY (person_id),
    FOREIGN KEY (person_id) REFERENCES Person(person_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CHECK (years_of_experience >= 0)
);

-- -------------------------------------------------------
-- Stadium
-- -------------------------------------------------------
CREATE TABLE Stadium (
    stadium_id INT,
    stadium_name VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL,
    capacity INT NOT NULL,
    PRIMARY KEY (stadium_id),
    UNIQUE (stadium_name, city),
    CHECK (capacity > 0)
);

-- -------------------------------------------------------
-- Club
-- Note: manager_id is nullable because a club can
--       temporarily be without a manager.
-- -------------------------------------------------------
CREATE TABLE Club (
    club_id INT,
    club_name VARCHAR(100) NOT NULL UNIQUE,
    foundation_year INT NOT NULL,
    stadium_id INT NOT NULL,
    manager_id INT UNIQUE,
    PRIMARY KEY (club_id),
    FOREIGN KEY (stadium_id) REFERENCES Stadium(stadium_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (manager_id) REFERENCES Manager(person_id)
        ON DELETE SET NULL ON UPDATE CASCADE
);

-- -------------------------------------------------------
-- Competition
-- -------------------------------------------------------
CREATE TABLE Competition (
    competition_id INT,
    name VARCHAR(100) NOT NULL,
    season VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    competition_type VARCHAR(100) NOT NULL,
    PRIMARY KEY (competition_id),
    UNIQUE (name, season),
    CHECK (competition_type IN ('League', 'Cup', 'International'))
);

-- -------------------------------------------------------
-- Match
-- Note: attendance, home_goals, away_goals are nullable
--       because scheduled matches don't have results yet.
-- -------------------------------------------------------
CREATE TABLE `Match` (
    match_id INT,
    competition_id INT NOT NULL,
    home_club_id INT NOT NULL,
    away_club_id INT NOT NULL,
    stadium_id INT NOT NULL,
    match_datetime DATETIME NOT NULL,
    attendance INT NULL,
    home_goals INT NULL,
    away_goals INT NULL,
    referee_id INT NOT NULL,
    PRIMARY KEY (match_id),
    FOREIGN KEY (competition_id)
        REFERENCES Competition(competition_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (referee_id)
        REFERENCES Referee(person_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (home_club_id)
        REFERENCES Club(club_id)
        ON DELETE RESTRICT,
    FOREIGN KEY (away_club_id)
        REFERENCES Club(club_id)
        ON DELETE RESTRICT,
    FOREIGN KEY (stadium_id)
        REFERENCES Stadium(stadium_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CHECK (home_club_id != away_club_id),
    CHECK (attendance >= 0),
    CHECK (home_goals >= 0),
    CHECK (away_goals >= 0)
);

-- -------------------------------------------------------
-- Contract
-- -------------------------------------------------------
CREATE TABLE Contract (
    contract_id INT,
    player_id INT NOT NULL,
    club_id INT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    weekly_wage DECIMAL(15,2) NOT NULL,
    PRIMARY KEY (contract_id),
    FOREIGN KEY (player_id) REFERENCES Player(person_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (club_id) REFERENCES Club(club_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CHECK (end_date > start_date),
    CHECK (weekly_wage > 0)
);

-- -------------------------------------------------------
-- Permanent Contract (subclass of Contract)
-- -------------------------------------------------------
CREATE TABLE Permanent_Contract (
    contract_id INT,
    PRIMARY KEY (contract_id),
    FOREIGN KEY (contract_id) REFERENCES Contract(contract_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- -------------------------------------------------------
-- Loan Contract (subclass of Contract)
-- -------------------------------------------------------
CREATE TABLE Loan_Contract (
    contract_id INT,
    permanent_contract_id INT NOT NULL,
    PRIMARY KEY (contract_id),
    FOREIGN KEY (contract_id)
        REFERENCES Contract(contract_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (permanent_contract_id)
        REFERENCES Permanent_Contract(contract_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- -------------------------------------------------------
-- Transfer Record
-- -------------------------------------------------------
CREATE TABLE Transfer_Record (
    transfer_id INT,
    player_id INT NOT NULL,
    from_club_id INT NOT NULL,
    to_club_id INT NOT NULL,
    transfer_date DATE NOT NULL,
    transfer_fee DECIMAL(15,2) NOT NULL,
    transfer_type VARCHAR(10) NOT NULL,
    PRIMARY KEY (transfer_id),
    FOREIGN KEY (player_id) REFERENCES Player(person_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (from_club_id) REFERENCES Club(club_id)
        ON DELETE RESTRICT,
    FOREIGN KEY (to_club_id) REFERENCES Club(club_id)
        ON DELETE RESTRICT,
    CHECK (from_club_id != to_club_id),
    CHECK (transfer_type IN ('Free', 'Purchase', 'Loan')),
    CHECK (
        (transfer_type = 'Free' AND transfer_fee = 0)
        OR
        (transfer_type IN ('Purchase', 'Loan') AND transfer_fee > 0)
    )
);

-- -------------------------------------------------------
-- Match Participation (junction table)
-- -------------------------------------------------------
CREATE TABLE Match_Participation (
    match_id INT,
    player_id INT NOT NULL,
    club_id INT NOT NULL,
    is_starter BOOLEAN NOT NULL,
    minutes_played INT NOT NULL,
    position_in_match VARCHAR(255) NOT NULL,
    goals INT NOT NULL DEFAULT 0,
    assists INT NOT NULL DEFAULT 0,
    yellow_cards INT NOT NULL DEFAULT 0,
    red_cards INT NOT NULL DEFAULT 0,
    rating DECIMAL(3,1) NOT NULL,
    PRIMARY KEY (match_id, player_id),
    FOREIGN KEY (match_id) REFERENCES `Match`(match_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (player_id) REFERENCES Player(person_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (club_id) REFERENCES Club(club_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CHECK (minutes_played BETWEEN 0 AND 120),
    CHECK (goals >= 0),
    CHECK (assists >= 0),
    CHECK (yellow_cards IN (0, 1, 2)),
    CHECK (red_cards IN (0, 1)),
    CHECK (rating BETWEEN 1.0 AND 10.0)
);

-- -------------------------------------------------------
-- User (application-level authentication)
-- -------------------------------------------------------
CREATE TABLE User (
    username VARCHAR(50) PRIMARY KEY,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('db_manager','player','manager','referee') NOT NULL,
    person_id INT NULL,
    FOREIGN KEY (person_id) REFERENCES Person(person_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);
