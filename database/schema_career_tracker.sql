-- ==========================================================
-- CareerCoach AI - Career Tracker feature schema (ADDITIVE)
-- Adds new tables only. Does NOT modify `users` or `resumes`.
-- Run after the base schema:
--   mysql -u root -p careercoach_ai < database/schema_career_tracker.sql
-- ==========================================================

USE careercoach_ai;

-- Table: user_career_role ---------------------------------------
-- The target role a user is currently tracking against.
CREATE TABLE IF NOT EXISTS user_career_role (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT NOT NULL,
    role_key    VARCHAR(100) NOT NULL,
    role_name   VARCHAR(150) NOT NULL,
    selected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Table: user_quiz_attempts --------------------------------------
-- One row per completed skill assessment. History powers the
-- career-readiness trend over time.
CREATE TABLE IF NOT EXISTS user_quiz_attempts (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT NOT NULL,
    role_key        VARCHAR(100),
    skill_key       VARCHAR(100) NOT NULL,
    skill_name      VARCHAR(150) NOT NULL,
    score            INT NOT NULL,
    total_questions  INT NOT NULL,
    percentage       DECIMAL(5,2) NOT NULL,
    taken_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Table: user_roadmap_progress ------------------------------------
-- Tracks stage-by-stage roadmap completion per user/role/skill.
CREATE TABLE IF NOT EXISTS user_roadmap_progress (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT NOT NULL,
    role_key    VARCHAR(100) NOT NULL,
    stage       VARCHAR(20) NOT NULL,                  -- beginner / intermediate / advanced
    skill_key   VARCHAR(100) NOT NULL,
    status      VARCHAR(20) NOT NULL DEFAULT 'pending', -- pending / in_progress / completed
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uniq_user_role_skill (user_id, role_key, skill_key)
);

-- Table: user_roadmap_cache ----------------------------------------
-- Stores the last AI-generated roadmap per user/role so it does not
-- need to be regenerated on every dashboard visit. Regenerated only
-- on explicit reassessment.
CREATE TABLE IF NOT EXISTS user_roadmap_cache (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    user_id       INT NOT NULL,
    role_key      VARCHAR(100) NOT NULL,
    roadmap_json  LONGTEXT,
    generated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
