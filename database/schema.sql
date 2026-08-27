-- ==========================================================
-- CareerCoach AI - MySQL schema
-- Run:  mysql -u root -p < database/schema.sql
-- ==========================================================

CREATE DATABASE IF NOT EXISTS careercoach_ai;
USE careercoach_ai;

-- Table: users -------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id       INT AUTO_INCREMENT PRIMARY KEY,
    name     VARCHAR(100) NOT NULL,
    email    VARCHAR(150) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,           -- stored as a hash
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: resumes ----------------------------------------------
-- Stores the uploaded file name and the extracted resume text.
CREATE TABLE IF NOT EXISTS resumes (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT NOT NULL,
    filename    VARCHAR(255) NOT NULL,
    resume_text LONGTEXT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
