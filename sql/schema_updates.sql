-- Schema updates / migration helper.
-- Only needed if you already have an older version of the DB.
-- If starting fresh with schema.sql, this file is NOT needed.
--
-- Usage: mysql -u root DB < sql/schema_updates.sql

USE DB;

-- -------------------------------------------------------
-- 1. Add status column to Match (only if not exists)
-- -------------------------------------------------------
DROP PROCEDURE IF EXISTS add_status_column;
DELIMITER //
CREATE PROCEDURE add_status_column()
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME   = 'Match'
          AND COLUMN_NAME  = 'status'
    ) THEN
        ALTER TABLE `Match`
            ADD COLUMN status ENUM('Scheduled', 'Completed') NOT NULL DEFAULT 'Scheduled';
    END IF;
END//
DELIMITER ;
CALL add_status_column();
DROP PROCEDURE IF EXISTS add_status_column;

-- -------------------------------------------------------
-- 2. Make attendance, home_goals, away_goals nullable
-- -------------------------------------------------------
ALTER TABLE `Match`
    MODIFY COLUMN attendance  INT NULL,
    MODIFY COLUMN home_goals  INT NULL,
    MODIFY COLUMN away_goals  INT NULL;

-- Mark existing rows with score data as Completed
UPDATE `Match`
SET status = 'Completed'
WHERE status = 'Scheduled'
  AND attendance IS NOT NULL
  AND home_goals IS NOT NULL
  AND away_goals IS NOT NULL;

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
