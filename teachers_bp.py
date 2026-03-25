from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, abort
from flask_login import login_required
from flask_login import current_user
from extensions import db
from models import Student, Subject, Grade, UserRole
from models import AssessmentCategory, AcademicPeriod
from datetime import datetime
from utils.auth import requires_roles
from flask import Response
from utils.pdf_reports import generate_gradebook_pdf
from scripts.import_export import export_gradebook_csv

teachers_bp = Blueprint('teachers_bp', __name__, url_prefix='/teacher')

YEAR_GROUP_OPTIONS = (
    '1er Grado',
    '2do Grado',
    '3er Grado',
    '4to Grado',
    '5to Grado',
    '6to Grado',
    '1er Año',
    '2do Año',
    '3er Año',
    '4to Año',
    '5to Año',
)

PASSING_SCORE_20 = 10.0

from models import Attendance, AttendanceStatus

@teachers_bp.route('/attendance/bulk', methods=['POST'])
@login_required
@requires_roles(UserRole.TEACHER, UserRole.ADMIN, UserRole.SUPER_ADMIN)
def attendance_bulk():
    payload = request.get_json() or {}
    subject_id = payload.get('subject_id')
    rec_date_str = payload.get('date')
    records = payload.get('records')

    if not subject_id or not records:
        return ({'error': 'subject_id and records are required'}, 400)

    subj = db.session.get(Subject, subject_id)
    if not subj:
        return ({'error': 'subject not found'}, 404)

    if rec_date_str:
        try:
            rec_date = datetime.strptime(rec_date_str, '%Y-%m-%d').date()
        except ValueError:
            return ({'error': 'invalid date format, must be YYYY-MM-DD'}, 400)
    else:
        from datetime import date
        rec_date = date.today()

    try:
        for rec in records:
            student_id = rec.get('student_id')
            status_str = rec.get('status')
            remarks = rec.get('remarks')

            if not student_id or not status_str:
                continue

            try:
                status_enum = AttendanceStatus[status_str.upper()]
            except KeyError:
                continue

            att = Attendance.query.filter_by(
                student_id=student_id,
                subject_id=subject_id,
                date=rec_date
            ).first()

            if att:
                att.status = status_enum
                att.remarks = remarks
                att.recorded_by = current_user.id
            else:
                att = Attendance(
                    student_id=student_id,
                    subject_id=subject_id,
                    date=rec_date,
                    status=status_enum,
                    remarks=remarks,
                    recorded_by=current_user.id
                )
                db.session.add(att)

        db.session.commit()
        return ({'status': 'success'}, 200)

    except Exception as e:
        db.session.rollback()
        return ({'error': str(e)}, 500)


def _is_passing_average(avg_value):
    if avg_value is None:
        return False
    value = float(avg_value)
    return value >= PASSING_SCORE_20

def _promote_student_if_ready(student):
    current_year = getattr(student, 'current_year_group', None)
    if not current_year or current_year not in YEAR_GROUP_OPTIONS:
        return None
    current_idx = YEAR_GROUP_OPTIONS.index(current_year)
    if current_idx >= len(YEAR_GROUP_OPTIONS) - 1:
        return None

    subjects_for_year = Subject.query.filter_by(year_group=current_year).all()
    if not subjects_for_year:
        return None

    for subject in subjects_for_year:
        avg = student.weighted_average(subject.id)
        if not _is_passing_average(avg):
            return None

    next_year = YEAR_GROUP_OPTIONS[current_idx + 1]
    student.current_year_group = next_year
    db.session.commit()
    return next_year

@teachers_bp.route('/student/<int:student_id>/subject/<int:subject_id>/grades', methods=['GET', 'POST'])
@login_required
@requires_roles(UserRole.TEACHER, UserRole.ADMIN, UserRole.SUPER_ADMIN)
def edit_4_grades(student_id, subject_id):
    student = db.session.get(Student, student_id)
    subj = db.session.get(Subject, subject_id)
    if not student or not subj:
        abort(404)

    grades = Grade.query.filter_by(student_id=student_id, subject_id=subject_id).all()
    # Mapear grades existentes por término ('Nota 1', 'Nota 2', 'Nota 3', 'Nota 4')
    grades_map = {g.term: g for g in grades if g.term}

    TERMS = ['Nota 1', 'Nota 2', 'Nota 3', 'Nota 4']

    if request.method == 'POST':
        try:
            with db.session.begin_nested():
                for term in TERMS:
                    score_str = request.form.get(f'score_{term}')
                    comment = request.form.get(f'comment_{term}')

                    score_val = None
                    if score_str:
                        try:
                            score_val = float(score_str)
                            if score_val < 0 or score_val > 20:
                                raise ValueError(f"La nota '{term}' debe estar entre 0 y 20.")
                        except ValueError as ve:
                            flash(str(ve), "warning")
                            return redirect(url_for('teachers_bp.edit_4_grades', student_id=student_id, subject_id=subject_id))

                    if term in grades_map:
                        g = grades_map[term]
                        g.score = score_val
                        g.comment = comment
                    else:
                        g = Grade(student_id=student.id, subject_id=subj.id, term=term, score=score_val, comment=comment)
                        db.session.add(g)

            db.session.commit()
            flash('Notas actualizadas exitosamente.', 'success')

            promoted_to = _promote_student_if_ready(student)
            if promoted_to:
                flash(f'Estudiante promovido automáticamente a {promoted_to}.', 'success')

        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar notas: {e}', 'danger')

        return redirect(url_for('students_bp.student_detail', student_id=student.id))

    return render_template('students/grade_form.html', student=student, subject=subj, grades_map=grades_map, terms=TERMS)


@teachers_bp.route('/reports/gradebook')
@login_required
@requires_roles(UserRole.TEACHER, UserRole.ADMIN)
def report_gradebook():
    subject_id = request.args.get('subject_id', type=int)
    if not subject_id:
        flash('subject_id required', 'warning')
        return redirect(url_for('students_bp.list_students'))
    subj = db.session.get(Subject, subject_id)
    if subj is None:
        abort(404)
    grades = Grade.query.filter_by(subject_id=subj.id).join(Student).order_by(Student.last_name, Student.first_name).all()
    # prepare tuples of (student, grade)
    rows = [(g.student, g) for g in grades]
    pdf_bytes = generate_gradebook_pdf(subj, rows)
    return Response(pdf_bytes, mimetype='application/pdf', headers={"Content-Disposition": f"attachment; filename=gradebook_{subj.id}.pdf"})


@teachers_bp.route('/grades', methods=['POST'])
@login_required
@requires_roles(UserRole.TEACHER, UserRole.ADMIN)
def create_grade():
    """Create a grade via JSON payload. Expected JSON keys:
    student_id, subject_id, assessment_category_id (optional), value (0-20), periodo_id (optional), comment
    """
    data = request.get_json() or {}
    sid = data.get('student_id')
    subject_id = data.get('subject_id')
    category_id = data.get('assessment_category_id')
    periodo_id = data.get('periodo_id')
    comment = data.get('comment')
    val = data.get('value')
    if not sid or not subject_id:
        return ({'error': 'student_id and subject_id required'}, 400)
    student = db.session.get(Student, sid)
    if student is None:
        return ({'error': 'student not found'}, 404)
    subject = db.session.get(Subject, subject_id)
    if subject is None:
        return ({'error': 'subject not found'}, 404)
    # only allow teacher of subject or admin
    if current_user.role != UserRole.ADMIN and subject.teacher_id and subject.teacher_id != current_user.id:
        return ({'error': 'forbidden: not teacher of this subject'}, 403)
    # validate value 0-20
    if val is not None:
        try:
            v = float(val)
        except Exception:
            return ({'error': 'invalid value'}, 400)
        if v < 0 or v > 20:
            return ({'error': 'value must be between 0 and 20'}, 400)
    else:
        v = None
    # validate category and periodo existence when provided
    if category_id:
        cat = db.session.get(AssessmentCategory, category_id)
        if cat is None:
            return ({'error': 'assessment category not found'}, 404)
    if periodo_id:
        per = db.session.get(AcademicPeriod, periodo_id)
        if per is None:
            return ({'error': 'period not found'}, 404)
    g = Grade(student_id=student.id, subject_id=subject.id, assessment_category_id=category_id, value=v, periodo_id=periodo_id, comment=comment)
    try:
        db.session.add(g)
        db.session.commit()
        promoted_to = _promote_student_if_ready(student)
        return ({'status': 'ok', 'grade_id': g.id, 'promoted_to': promoted_to}, 201)
    except Exception as e:
        db.session.rollback()
        return ({'error': str(e)}, 500)


@teachers_bp.route('/grades/subject/<int:subject_id>/report')
@login_required
@requires_roles(UserRole.TEACHER, UserRole.ADMIN)
def subject_report(subject_id):
    subj = db.session.get(Subject, subject_id)
    if subj is None:
        abort(404)
    # only teacher of subject or admin
    if current_user.role != UserRole.ADMIN and subj.teacher_id and subj.teacher_id != current_user.id:
        return ({'error': 'forbidden: not teacher of this subject'}, 403)
    # For each student in subject, compute weighted_average (uses AssessmentCategory weights)
    students = (
        db.session.query(Student)
        .join(Grade)
        .filter(Grade.subject_id == subj.id)
        .group_by(Student.id)
        .all()
    )
    report = {'subject_id': subj.id, 'subject_name': subj.name, 'total': len(students), 'passed': 0, 'failed': 0, 'details': []}
    PASSING_SCORE = 10.0
    for st in students:
        avg = st.weighted_average(subj.id)
        passed = False
        if avg is not None:
            passed = float(avg) >= PASSING_SCORE
        if passed:
            report['passed'] += 1
        else:
            report['failed'] += 1
        report['details'].append({'student_id': st.id, 'student_name': f"{st.first_name} {st.last_name}", 'average': avg, 'passed': passed})
    return report


@teachers_bp.route('/subjects')
@login_required
@requires_roles(UserRole.TEACHER)
def teacher_subjects():
    # list subjects assigned to current teacher and their students
    subjects = Subject.query.filter_by(teacher_id=current_user.id).order_by(Subject.year_group, Subject.name).all()
    data = []
    for s in subjects:
        # Get all students enrolled in this year group, AND students who might already have a grade
        students = (
            db.session.query(Student)
            .outerjoin(Grade, db.and_(Grade.student_id == Student.id, Grade.subject_id == s.id))
            .filter(db.or_(Student.current_year_group == s.year_group, Grade.subject_id == s.id))
            .group_by(Student.id)
            .order_by(Student.section, Student.last_name, Student.first_name)
            .all()
        )

        # Build student data with their current grade for the subject
        # Pre-fetch all grades for the subject in one query to avoid N+1 inside loop
        grades = Grade.query.filter_by(subject_id=s.id).all()
        grade_by_student_id = {g.student_id: g for g in grades}

        student_data = []
        for student in students:
            grade = grade_by_student_id.get(student.id)
            student_data.append({
                'student': student,
                'grade': grade
            })

        data.append({'subject': s, 'students': student_data})
    return render_template('students/teacher_subjects.html', data=data)


@teachers_bp.route('/gradebook/<int:subject_id>/bulk_update', methods=['POST'])
@login_required
@requires_roles(UserRole.TEACHER, UserRole.ADMIN)
def gradebook_bulk_update(subject_id):
    # Expects JSON: {"grades": [{"student_id":.., "score":.., "comment":.., "term":..}, ...]}
    subj = db.session.get(Subject, subject_id)
    if subj is None:
        abort(404)
    payload = request.get_json()
    if not payload or 'grades' not in payload:
        return ("Missing grades payload", 400)
    items = payload['grades']
    try:
        # use nested transaction to avoid conflicts with any outer test transactions
        with db.session.begin_nested():
            student_ids = [it.get('student_id') for it in items if it.get('student_id')]

            # Bulk fetch students
            students = Student.query.filter(Student.id.in_(student_ids)).all()
            student_map = {s.id: s for s in students}

            # Bulk fetch grades
            grades = Grade.query.filter(Grade.student_id.in_(student_ids), Grade.subject_id == subj.id).all()

            # Create a dictionary for quick lookup of existing grades by (student_id, term)
            grade_map = {}
            for g in grades:
                grade_map[(g.student_id, g.term)] = g

            updated_student_ids = set()
            new_grades = []

            for it in items:
                sid = it.get('student_id')
                score = it.get('score')
                comment = it.get('comment')
                term = it.get('term')

                if not sid:
                    raise ValueError('student_id required')

                if sid not in student_map:
                    raise ValueError(f'student {sid} not found')

                try:
                    score_val = None if score is None else float(score)
                except Exception:
                    raise ValueError('invalid score')

                # Check for existing grade
                g = grade_map.get((sid, term))

                if g:
                    g.score = score_val
                    g.comment = comment
                    g.term = term
                else:
                    g = Grade(student_id=sid, subject_id=subj.id, score=score_val, comment=comment, term=term)
                    new_grades.append(g)
                    # Add to map in case there are duplicates in payload
                    grade_map[(sid, term)] = g

                updated_student_ids.add(sid)

            if new_grades:
                db.session.bulk_save_objects(new_grades)

        promoted = []
        for sid in updated_student_ids:
            st = student_map.get(sid)
            if st is None:
                continue
            next_year = _promote_student_if_ready(st)
            if next_year:
                promoted.append({'student_id': sid, 'promoted_to': next_year})

        return ({'status': 'ok', 'updated': len(items), 'promoted': promoted}, 200)
    except Exception as e:
        db.session.rollback()
        return ({'status': 'error', 'error': str(e)}, 400)


@teachers_bp.route('/gradebook/<int:subject_id>.csv')
@login_required
@requires_roles(UserRole.TEACHER, UserRole.ADMIN)
def export_gradebook(subject_id):
    subj = db.session.get(Subject, subject_id)
    if subj is None:
        abort(404)
    data = export_gradebook_csv(subj.id)
    fname = f'gradebook_{subj.id}.csv'
    # Force exact Content-Type without charset to satisfy strict tests
    return Response(data, headers={"Content-Disposition": f"attachment; filename={fname}", "Content-Type": "text/csv"})
