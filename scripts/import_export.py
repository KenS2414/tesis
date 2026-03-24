import csv
from io import StringIO
from datetime import datetime
from extensions import db
from models import Student, Subject, Grade


def import_students_csv(stream):
    """Import students from a CSV file-like `stream`.
    Expects headers: first_name,last_name,email,dob (dob optional, YYYY-MM-DD)
    Creates or updates by email.
    Returns number of records processed.
    """
    reader = csv.DictReader(StringIO(stream.read().decode('utf-8')))
    count = 0
    for row in reader:
        email = row.get('email')
        first_name = row.get('first_name')
        last_name = row.get('last_name')
        dob_raw = row.get('dob')
        dob = None
        if dob_raw:
            try:
                dob = datetime.strptime(dob_raw, '%Y-%m-%d').date()
            except Exception:
                dob = None
        if not first_name or not last_name:
            continue
        if email:
            existing = Student.query.filter_by(email=email).first()
        else:
            existing = None
        if existing:
            existing.first_name = first_name
            existing.last_name = last_name
            existing.dob = dob
        else:
            s = Student(first_name=first_name, last_name=last_name, email=email, dob=dob)
            db.session.add(s)
        count += 1
    db.session.commit()
    return count


def import_subjects_csv(stream):
    reader = csv.DictReader(StringIO(stream.read().decode('utf-8')))
    count = 0
    for row in reader:
        name = row.get('name')
        code = row.get('code')
        category = row.get('category')
        credits_raw = row.get('credits')
        description = row.get('description')
        credits = None
        if credits_raw:
            try:
                credits = int(credits_raw)
            except Exception:
                credits = None
        if not name:
            continue
        existing = Subject.query.filter_by(code=code).first() if code else None
        if existing:
            existing.name = name
            existing.category = category
            existing.credits = credits
            existing.description = description
        else:
            s = Subject(name=name, code=code, category=category, credits=credits, description=description)
            db.session.add(s)
        count += 1
    db.session.commit()
    return count


def import_grades_csv(stream):
    reader = csv.DictReader(StringIO(stream.read().decode('utf-8')))
    count = 0
    for row in reader:
        student_email = row.get('student_email')
        subject_code = row.get('subject_code')
        score_raw = row.get('score')
        comment = row.get('comment')
        term = row.get('term')
        if not student_email or not subject_code:
            continue
        student = Student.query.filter_by(email=student_email).first()
        subject = Subject.query.filter_by(code=subject_code).first()
        if not student or not subject:
            continue
        try:
            score = float(score_raw) if score_raw else None
        except Exception:
            score = None
        g = Grade(student_id=student.id, subject_id=subject.id, score=score, comment=comment, term=term)
        db.session.add(g)
        count += 1
    db.session.commit()
    return count


def export_students_csv():
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['first_name', 'last_name', 'email', 'dob'])
    for s in Student.query.order_by(Student.last_name, Student.first_name).all():
        dob = s.dob.isoformat() if s.dob else ''
        writer.writerow([s.first_name, s.last_name, s.email or '', dob])
    return output.getvalue().encode('utf-8')


def export_subjects_csv():
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['name', 'code', 'category', 'credits', 'description'])
    for s in Subject.query.order_by(Subject.name).all():
        writer.writerow([s.name, s.code or '', s.category or '', s.credits or '', s.description or ''])
    return output.getvalue().encode('utf-8')


def export_grades_csv():
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['student_email', 'subject_code', 'score', 'comment', 'term'])
    for g in Grade.query.join(Student).join(Subject).all():
        writer.writerow([g.student.email or '', g.subject.code or '', g.score if g.score is not None else '', g.comment or '', g.term or ''])
    return output.getvalue().encode('utf-8')


def export_gradebook_csv(subject_id):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['student_id', 'first_name', 'last_name', 'email', 'score', 'comment', 'term'])
    grades = Grade.query.filter_by(subject_id=subject_id).join(Student).order_by(Student.last_name, Student.first_name).all()
    for g in grades:
        writer.writerow([
            g.student.id,
            g.student.first_name,
            g.student.last_name,
            g.student.email or '',
            g.score if g.score is not None else '',
            g.comment or '',
            g.term or '',
        ])
    return output.getvalue().encode('utf-8')
