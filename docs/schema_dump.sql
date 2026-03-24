-- Schema-only SQL dump for resis (Postgres-compatible)
-- DROP and CREATE statements to reproduce the database schema

DROP TABLE IF EXISTS payment CASCADE;
DROP TABLE IF EXISTS grade CASCADE;
DROP TABLE IF EXISTS subject CASCADE;
DROP TABLE IF EXISTS student CASCADE;
DROP TABLE IF EXISTS "user" CASCADE;

-- Recreate tables
\n-- Users
CREATE TABLE "user" (
    id SERIAL PRIMARY KEY,
    username VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(200) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'user'
);

-- Students
CREATE TABLE student (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(120) NOT NULL,
    last_name VARCHAR(120) NOT NULL,
    email VARCHAR(200),
    dob DATE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now()
);

-- Subjects
CREATE TABLE subject (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    code VARCHAR(50)
);

-- Grades
CREATE TABLE grade (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL,
    subject_id INTEGER NOT NULL,
    score NUMERIC(5,2),
    comment VARCHAR(400),
    term VARCHAR(50),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    CONSTRAINT fk_grade_student FOREIGN KEY(student_id) REFERENCES student(id) ON DELETE CASCADE,
    CONSTRAINT fk_grade_subject FOREIGN KEY(subject_id) REFERENCES subject(id) ON DELETE CASCADE
);

-- Payments
CREATE TABLE payment (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL,
    amount NUMERIC(10,2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    proof_filename VARCHAR(300),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    CONSTRAINT fk_payment_student FOREIGN KEY(student_id) REFERENCES student(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_student_email ON student(email);
CREATE INDEX IF NOT EXISTS idx_subject_name ON subject(name);
