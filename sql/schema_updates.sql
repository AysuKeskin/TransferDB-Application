-- Schema updates / migration helper.
-- Only needed if you already have an older version of the DB.
-- If starting fresh with schema.sql, this file is NOT needed.
--
-- Usage: mysql -u root DB < sql/schema_updates.sql

USE DB;

-- -------------------------------------------------------
-- 1. Make attendance, home_goals, away_goals nullable
-- -------------------------------------------------------
ALTER TABLE `Match`
    MODIFY COLUMN attendance  INT NULL,
    MODIFY COLUMN home_goals  INT NULL,
    MODIFY COLUMN away_goals  INT NULL;

-- -------------------------------------------------------
-- 2. Drop status column if it exists
-- -------------------------------------------------------
DROP PROCEDURE IF EXISTS drop_status_column;
DELIMITER //
CREATE PROCEDURE drop_status_column()
BEGIN
    IF EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME   = 'Match'
          AND COLUMN_NAME  = 'status'
    ) THEN
        ALTER TABLE `Match` DROP COLUMN status;
    END IF;
END//
DELIMITER ;
CALL drop_status_column();
DROP PROCEDURE IF EXISTS drop_status_column;

-- -------------------------------------------------------
-- 3. Make Club.manager_id nullable
-- -------------------------------------------------------
ALTER TABLE Club
    MODIFY COLUMN manager_id INT NULL;

-- -------------------------------------------------------
-- 4. User table (only if not exists)
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS User (
    username      VARCHAR(50)  PRIMARY KEY,
    password_hash VARCHAR(255) NOT NULL,
    role          ENUM('db_manager','player','manager','referee') NOT NULL,
    person_id     INT          NULL,
    FOREIGN KEY (person_id) REFERENCES Person(person_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);
