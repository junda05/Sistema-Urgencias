-- Urgentix - Emergency Department Visualization System
-- Database schema. Creates an empty, ready-to-use database.
--
-- Setup:
--   1. mysql -u root -p < schema.sql
--   2. Create the MySQL accounts the application authenticates against
--      (see "Application accounts" at the end of this file).
--
-- The exam catalogs are left empty here on purpose: the application imports
-- them from the source spreadsheets the first time someone logs in, and skips
-- the import on every later start. See README.md.

DROP DATABASE IF EXISTS urgentix;
CREATE DATABASE urgentix CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE urgentix;

-- ---------------------------------------------------------------------------
-- Users
-- Authentication is delegated to the MySQL server: each application user is a
-- MySQL account. This table stores the profile and role metadata for them.
-- ---------------------------------------------------------------------------
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    role_admin BOOLEAN DEFAULT FALSE,
    role_doctor BOOLEAN DEFAULT FALSE,
    role_visitor BOOLEAN DEFAULT FALSE,
    status VARCHAR(20) DEFAULT 'active',
    registration_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_access DATETIME NULL,
    INDEX idx_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------------
-- Patients
-- One row per patient currently tracked in the emergency department.
-- Each care stage (admission consult, labs, imaging, specialist consult,
-- reassessment) stores both its current status and the timestamp of every
-- status transition, which is what the metrics module reports on.
--
-- Column order is significant: several queries select these columns
-- explicitly and read the results positionally.
-- ---------------------------------------------------------------------------
CREATE TABLE patients (
    name VARCHAR(255),
    document_id VARCHAR(20),
    triage VARCHAR(20),
    triage_timestamp DATETIME,
    admission_consult VARCHAR(255),
    labs VARCHAR(255),
    imaging VARCHAR(255),
    specialist_consult VARCHAR(255),
    reassessment VARCHAR(255),
    pending_tasks TEXT,
    disposition VARCHAR(20),
    location VARCHAR(50),
    admission DATETIME,
    id INT AUTO_INCREMENT PRIMARY KEY,
    observation_timestamp DATETIME,

    admission_consult_not_done_timestamp DATETIME
        COMMENT 'Moment the admission consult was set to Not completed',
    admission_consult_done_timestamp DATETIME
        COMMENT 'Moment the admission consult was set to Completed',

    labs_not_done_timestamp DATETIME
        COMMENT 'Moment labs were set to Not started',
    labs_requested_timestamp DATETIME
        COMMENT 'Moment labs were set to Awaiting results',
    labs_complete_timestamp DATETIME
        COMMENT 'Moment labs were set to Results complete',

    imaging_not_done_timestamp DATETIME
        COMMENT 'Moment imaging was set to Not started',
    imaging_requested_timestamp DATETIME
        COMMENT 'Moment imaging was set to Awaiting results',
    imaging_complete_timestamp DATETIME
        COMMENT 'Moment imaging was set to Results complete',

    specialist_consult_not_opened_timestamp DATETIME
        COMMENT 'Moment the specialist consult was set to Not opened',
    specialist_consult_opened_timestamp DATETIME
        COMMENT 'Moment the specialist consult was set to Open',
    specialist_consult_done_timestamp DATETIME
        COMMENT 'Moment the specialist consult was set to Completed',

    reassessment_not_done_timestamp DATETIME
        COMMENT 'Moment the reassessment was set to Not completed',
    reassessment_done_timestamp DATETIME
        COMMENT 'Moment the reassessment was set to Completed',

    discharge_timestamp DATETIME
        COMMENT 'Moment the disposition was set to Discharged',

    INDEX idx_document_id (document_id),
    INDEX idx_admission (admission)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------------
-- Patient metrics
-- Elapsed times per care stage, in minutes, computed for historical analysis
-- and report generation.
-- ---------------------------------------------------------------------------
CREATE TABLE patient_metrics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    calculation_date DATETIME DEFAULT CURRENT_TIMESTAMP,

    triage_time INT COMMENT 'Minutes from admission to triage',
    triage_level VARCHAR(1) COMMENT 'Triage level (1-5)',
    admission_consult_time INT COMMENT 'Minutes from Not completed to Completed',
    labs_request_time INT COMMENT 'Minutes from Not started to Awaiting results',
    labs_results_time INT COMMENT 'Minutes from Awaiting results to Results complete',
    labs_total_time INT COMMENT 'Minutes from Not started to Results complete',
    imaging_request_time INT COMMENT 'Minutes from Not started to Awaiting results',
    imaging_results_time INT COMMENT 'Minutes from Awaiting results to Results complete',
    imaging_total_time INT COMMENT 'Minutes from Not started to Results complete',
    specialist_consult_opening_time INT COMMENT 'Minutes from Not opened to Open',
    specialist_consult_completion_time INT COMMENT 'Minutes from Open to Completed',
    specialist_consult_total_time INT COMMENT 'Minutes from Not opened to Completed',
    reassessment_time INT COMMENT 'Minutes from Not completed to Completed',
    total_care_time INT COMMENT 'Minutes from admission to discharge',

    area VARCHAR(50) COMMENT 'Care area',

    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    INDEX idx_metrics_patient_id (patient_id),
    INDEX idx_metrics_calculation_date (calculation_date),
    INDEX idx_metrics_triage_level (triage_level),
    INDEX idx_metrics_area (area)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------------
-- Exam catalogs
-- Reference data: the lab tests and imaging studies that can be ordered.
-- Populated from exam_catalog.sql.
-- ---------------------------------------------------------------------------
CREATE TABLE lab_catalog (
    id INT AUTO_INCREMENT PRIMARY KEY,
    lab_code VARCHAR(50) NOT NULL UNIQUE,
    lab_name VARCHAR(500) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE imaging_catalog (
    id INT AUTO_INCREMENT PRIMARY KEY,
    imaging_code VARCHAR(50) NOT NULL UNIQUE,
    imaging_name VARCHAR(500) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------------
-- Exams ordered per patient
-- ---------------------------------------------------------------------------
CREATE TABLE patient_labs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    lab_code VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'Not started',
    request_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    INDEX idx_patient_labs_patient_id (patient_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE patient_imaging (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    imaging_code VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'Not started',
    request_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    INDEX idx_patient_imaging_patient_id (patient_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------------
-- Audit trail
-- Every action performed through the application, for traceability.
-- ---------------------------------------------------------------------------
CREATE TABLE audit_trail (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    user_id INT,
    role VARCHAR(50) NOT NULL,
    action VARCHAR(100) NOT NULL,
    timestamp DATETIME NOT NULL,
    affected_patient VARCHAR(255) DEFAULT NULL,
    change_details TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_audit_username (username),
    INDEX idx_audit_timestamp (timestamp),
    INDEX idx_audit_patient (affected_patient),
    INDEX idx_audit_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Audit trail with role names resolved for display.
CREATE OR REPLACE VIEW audit_trail_view AS
SELECT
    id,
    username,
    CASE
        WHEN role = 'admin' THEN 'Administrator'
        WHEN role = 'doctor' THEN 'Doctor'
        WHEN role = 'visitor' THEN 'Visitor'
        ELSE role
    END AS role,
    action,
    timestamp,
    affected_patient,
    change_details
FROM audit_trail
ORDER BY timestamp DESC;

-- ---------------------------------------------------------------------------
-- Application accounts
--
-- The application authenticates users against the MySQL server itself, so each
-- application user needs a MySQL account plus a matching row in `users`.
-- Create the first administrator with the credentials set in config.ini, e.g.:
--
--   CREATE USER 'emergency_admin'@'%' IDENTIFIED BY '<your-password>';
--   GRANT ALL PRIVILEGES ON urgentix.* TO 'emergency_admin'@'%' WITH GRANT OPTION;
--   FLUSH PRIVILEGES;
--
--   INSERT INTO users (username, full_name, role_admin)
--   VALUES ('emergency_admin', 'System Administrator', TRUE);
--
-- Further users are created from the application's admin interface.
-- ---------------------------------------------------------------------------
