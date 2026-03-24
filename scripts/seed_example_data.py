#!/usr/bin/env python
r"""Seed example data into the application's database.
Run with the project's venv python: venv/Scripts/python.exe scripts/seed_example_data.py
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from werkzeug.security import generate_password_hash
from datetime import date
from app import create_app
from extensions import db
from models import User, Student, Subject, Grade, AssessmentCategory, AcademicPeriod, Payment


app = create_app()


def safe_add(obj):
    db.session.add(obj)


with app.app_context():
    print('Seeding example data...')
    # Ensure database tables exist (create_all for local dev)
    db.create_all()
    # Ensure admin user exists with password 'admin'
    admin = User.query.filter_by(username='admin').first()
    if admin is None:
        admin = User(username='admin', password_hash=generate_password_hash('admin'), role='admin')
        safe_add(admin)
        print('Created admin user: admin')
    else:
        admin.password_hash = generate_password_hash('admin')
        admin.role = 'admin'
        print('Updated admin credentials to admin/admin')

    # Create two teachers
    t1 = User.query.filter_by(username='juan.perez@example.com').first()
    if t1 is None:
        t1 = User(username='juan.perez@example.com', password_hash=generate_password_hash('teachpass1'), role='teacher')
        safe_add(t1)
    t2 = User.query.filter_by(username='maria.gomez@example.com').first()
    if t2 is None:
        t2 = User(username='maria.gomez@example.com', password_hash=generate_password_hash('teachpass2'), role='teacher')
        safe_add(t2)

    # Create some students (and linked User records)
    students_info = [
        ('alice@example.com', 'Alice', 'Lopez'),
        ('bob@example.com', 'Bob', 'Martinez'),
        ('carla@example.com', 'Carla', 'Diaz'),
        ('dan@example.com', 'Dan', 'Gomez'),
        ('eve@example.com', 'Eve', 'Ramos'),
    ]
    students = []
    for email, first, last in students_info:
        u = User.query.filter_by(username=email).first()
        if u is None:
            u = User(username=email, password_hash=generate_password_hash('student123'), role='student')
            safe_add(u)
        s = Student.query.filter_by(email=email).first()
        if s is None:
            s = Student(first_name=first, last_name=last, email=email)
            safe_add(s)
        students.append(s)

    # Commit users/students so we have ids
    db.session.commit()

    # Create subjects
    subj_defs = [
        ('Matemáticas', 'MAT101', 'Ciencias', 4, t1.id),
        ('Lengua', 'LEN101', 'Humanidades', 3, t2.id),
        ('Historia', 'HIS101', 'Humanidades', 2, t2.id),
        ('Física', 'FIS101', 'Ciencias', 4, t1.id),
    ]
    subjects = []
    for name, code, category, credits, teacher_id in subj_defs:
        s = Subject.query.filter_by(code=code).first()
        if s is None:
            s = Subject(name=name, code=code, category=category, credits=credits, teacher_id=teacher_id)
            safe_add(s)
        subjects.append(s)

    db.session.commit()

    # Create an academic period
    periodo = AcademicPeriod.query.filter_by(nombre='2026-Q1').first()
    if periodo is None:
        periodo = AcademicPeriod(nombre='2026-Q1', fecha_inicio=date(2026,1,1), fecha_fin=date(2026,6,30), activo=True)
        safe_add(periodo)

    db.session.commit()

    # Create some assessment categories
    cat_exam = AssessmentCategory.query.filter_by(nombre='Exam').first()
    if cat_exam is None:
        cat_exam = AssessmentCategory(nombre='Exam', peso_porcentual=70)
        safe_add(cat_exam)
    cat_home = AssessmentCategory.query.filter_by(nombre='Homework').first()
    if cat_home is None:
        cat_home = AssessmentCategory(nombre='Homework', peso_porcentual=30)
        safe_add(cat_home)

    db.session.commit()

    # Add grades: simple pattern
    from random import uniform, seed
    seed(1)
    all_subjects = Subject.query.all()
    all_students = Student.query.all()
    for subj in all_subjects:
        for st in all_students:
            # two grades per student per subject (exam + homework)
            g1 = Grade(student_id=st.id, subject_id=subj.id, assessment_category_id=cat_exam.id, value=round(uniform(5.0, 9.5), 2), periodo_id=periodo.id, comment='Exam')
            g2 = Grade(student_id=st.id, subject_id=subj.id, assessment_category_id=cat_home.id, value=round(uniform(6.0, 10.0), 2), periodo_id=periodo.id, comment='Homework')
            safe_add(g1)
            safe_add(g2)
    db.session.commit()

    # Add a couple of payments for first students
    for st in all_students[:3]:
        p = Payment(student_id=st.id, amount=100.0, status='pending')
        safe_add(p)
    db.session.commit()

    # Summary
    print('Seed complete:')
    print('Users:', User.query.count())
    print('Students:', Student.query.count())
    print('Subjects:', Subject.query.count())
    print('Grades:', Grade.query.count())
    print('Payments:', Payment.query.count())

    print('\nAdmin credentials: username=admin password=admin')
