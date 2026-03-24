from flask import Blueprint, request, jsonify, abort
from flask_login import login_required, current_user
from extensions import db
from models import Student, Section, AcademicYear, Enrollment, EnrollmentStatus, AcademicYearStatus
from datetime import date
from marshmallow import Schema, fields, ValidationError

enrollment_bp = Blueprint('enrollment_bp', __name__, url_prefix='/enrollment')


class EnrollmentSchema(Schema):
    student_id = fields.Int(required=True)
    section_id = fields.Int(required=True)
    academic_year_id = fields.Int(required=True)


@enrollment_bp.route('/register', methods=['POST'])
@login_required
def register_enrollment():
    payload = request.get_json() or {}
    try:
        data = EnrollmentSchema().load(payload)
    except ValidationError as ve:
        return (jsonify({'error': 'validation error', 'details': ve.messages}), 400)

    student_id = data['student_id']
    section_id = data['section_id']
    academic_year_id = data['academic_year_id']

    # simple role check: only admin or enrollment staff
    role = getattr(current_user, 'role', None)
    if role not in ('admin', 'enrollment'):
        return (jsonify({'error': 'forbidden'}), 403)

    student = db.session.get(Student, student_id)
    if student is None:
        return (jsonify({'error': 'student not found'}), 404)
    section = db.session.get(Section, section_id)
    if section is None:
        return (jsonify({'error': 'section not found'}), 404)
    year = db.session.get(AcademicYear, academic_year_id)
    if year is None:
        return (jsonify({'error': 'academic year not found'}), 404)
    # require academic year to be OPEN
    if year.status != AcademicYearStatus.OPEN:
        return (jsonify({'error': 'academic year not open for registration'}), 400)
    # check capacity: count active enrollments for this section in the given year
    active_count = Enrollment.query.filter_by(section_id=section_id, academic_year_id=academic_year_id, estado=EnrollmentStatus.ACTIVE).count()
    if active_count >= section.capacidad_maxima:
        return (jsonify({'error': 'section full', 'capacity': section.capacidad_maxima}), 400)
    # uniqueness: student cannot have ACTIVE enrollment in another section same year
    existing = Enrollment.query.filter_by(student_id=student_id, academic_year_id=academic_year_id, estado=EnrollmentStatus.ACTIVE).first()
    if existing:
        return (jsonify({'error': 'student already enrolled in this academic year', 'enrollment_id': existing.id}), 400)
    try:
        with db.session.begin():
            en = Enrollment(student_id=student_id, section_id=section_id, academic_year_id=academic_year_id, fecha_inscripcion=date.today(), estado=EnrollmentStatus.ACTIVE)
            db.session.add(en)
        return jsonify({'status': 'ok', 'enrollment_id': en.id}), 201
    except Exception as e:
        db.session.rollback()
        return (jsonify({'error': str(e)}), 500)


@enrollment_bp.route('/section/<int:section_id>/students')
@login_required
def section_students(section_id):
    year_id = request.args.get('year_id', type=int)
    section = db.session.get(Section, section_id)
    if section is None:
        abort(404)
    q = Enrollment.query.filter_by(section_id=section_id, estado=EnrollmentStatus.ACTIVE)
    if year_id:
        q = q.filter_by(academic_year_id=year_id)
    enrolls = q.join(Student).all()
    out = []
    for e in enrolls:
        out.append({'student_id': e.student.id, 'first_name': e.student.first_name, 'last_name': e.student.last_name, 'enrollment_id': e.id, 'fecha_inscripcion': e.fecha_inscripcion.isoformat()})
    return jsonify({'section_id': section_id, 'students': out})


@enrollment_bp.route('/history/student/<int:student_id>')
@login_required
def student_history(student_id):
    s = db.session.get(Student, student_id)
    if s is None:
        abort(404)
    enrolls = Enrollment.query.filter_by(student_id=student_id).join(Section).join(AcademicYear).order_by(AcademicYear.fecha_inicio.desc()).all()
    out = []
    for e in enrolls:
        out.append({'enrollment_id': e.id, 'section': e.section.nombre, 'level': e.section.level.nombre if e.section.level else None, 'academic_year': e.academic_year.nombre, 'estado': e.estado.name, 'fecha_inscripcion': e.fecha_inscripcion.isoformat()})
    return jsonify({'student_id': student_id, 'history': out})
