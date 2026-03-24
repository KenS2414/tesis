from datetime import datetime, timezone, date
from enum import Enum as PyEnum
from sqlalchemy import func
from decimal import Decimal
from flask_login import UserMixin
from werkzeug.security import check_password_hash
from extensions import db


class UserRole:
    ADMIN = 'admin'
    SUPER_ADMIN = 'super_admin'
    TEACHER = 'teacher'
    STUDENT = 'student'
    USER = 'user'
    TREASURY = 'treasury'
    ENROLLMENT = 'enrollment'

    @classmethod
    def all_roles(cls):
        return (
            cls.ADMIN,
            cls.SUPER_ADMIN,
            cls.TEACHER,
            cls.STUDENT,
            cls.USER,
            cls.TREASURY,
            cls.ENROLLMENT,
        )


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False, default=UserRole.USER)

    def set_role(self, new_role):
        """Set user role after validating against allowed roles."""
        if new_role not in UserRole.all_roles():
            raise ValueError(f"Invalid role: {new_role}")
        self.role = new_role

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_student(self):
        """Return the Student record associated with this user (by email/username)."""
        return Student.query.filter_by(email=self.username).first()


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(120), nullable=False)
    last_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(200), unique=False, nullable=True)
    current_year_group = db.Column(db.String(100), nullable=True)
    dob = db.Column(db.Date, nullable=True)
    cedula = db.Column(db.String(8), nullable=True)
    section = db.Column(db.String(1), nullable=True)
    photo_filename = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Student {self.id} {self.first_name} {self.last_name}>"

    def weighted_average(self, subject_id, periodo_id=None):
        """Compute weighted average for this student in a given subject.

        For each AssessmentCategory, compute the average of the student's grades
        in that category (optionally filtered by periodo), then apply the
        category weights (`peso_porcentual`). Returns a float between 0 and 10
        or None if no grades available.
        """
        from sqlalchemy import func
        # query averages per category
        q = (
            db.session.query(
                AssessmentCategory.id,
                AssessmentCategory.peso_porcentual,
                func.avg(Grade.value).label('avg_score'),
            )
            .join(Grade, Grade.assessment_category_id == AssessmentCategory.id)
            .filter(Grade.student_id == self.id, Grade.subject_id == subject_id)
            .group_by(AssessmentCategory.id)
        )
        if periodo_id:
            q = q.filter(Grade.periodo_id == periodo_id)
        rows = q.all()
        if not rows:
            return None
        total_weight = 0
        weighted_sum = 0
        for _id, peso, avg_score in rows:
            if avg_score is None:
                continue
            w = float(peso) if peso is not None else 0.0
            total_weight += w
            # avg_score expected in 0-10
            weighted_sum += float(avg_score) * w
        if total_weight == 0:
            return None
        return weighted_sum / total_weight


class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(50), nullable=True)
    year_group = db.Column(db.String(100), nullable=True)
    category = db.Column(db.String(100), nullable=True)
    credits = db.Column(db.Integer, nullable=True)
    description = db.Column(db.Text, nullable=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    teacher = db.relationship('User', backref=db.backref('subjects', lazy=True))

    def __repr__(self):
        return f"<Subject {self.id} {self.name}>"


class Grade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey("subject.id"), nullable=False)
    assessment_category_id = db.Column(db.Integer, db.ForeignKey("assessment_category.id"), nullable=True)
    value = db.Column(db.Numeric(4, 2), nullable=True)  # expected 0.00 - 10.00
    comment = db.Column(db.String(400), nullable=True)
    periodo_id = db.Column(db.Integer, db.ForeignKey("academic_period.id"), nullable=True)
    term = db.Column(db.String(50), nullable=True)
    fecha_registro = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    student = db.relationship("Student", backref=db.backref("grades", lazy=True))
    subject = db.relationship("Subject", backref=db.backref("grades", lazy=True))
    assessment_category = db.relationship("AssessmentCategory", backref=db.backref("grades", lazy=True))
    periodo = db.relationship("AcademicPeriod", backref=db.backref("grades", lazy=True))

    def __repr__(self):
        return f"<Grade {self.id} student={self.student_id} subject={self.subject_id} value={self.value}>"

    @property
    def score(self):
        return self.value

    @score.setter
    def score(self, v):
        self.value = v


class AcademicPeriod(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    activo = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"<AcademicPeriod {self.id} {self.nombre}>"


class AssessmentCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    peso_porcentual = db.Column(db.Numeric(5, 2), nullable=False, default=0)

    def __repr__(self):
        return f"<AssessmentCategory {self.id} {self.nombre} {self.peso_porcentual}%>"


class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending")
    proof_filename = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    student = db.relationship("Student", backref=db.backref("payments", lazy=True))

    def __repr__(self):
        return f"<Payment {self.id} {self.amount} {self.status}>"


class AttendanceStatus(PyEnum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    LATE = "LATE"
    EXCUSED = "EXCUSED"


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey("subject.id"), nullable=False)
    date = db.Column(db.Date, nullable=False, default=lambda: date.today())
    status = db.Column(db.Enum(AttendanceStatus), nullable=False)
    remarks = db.Column(db.String(400), nullable=True)
    recorded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    student = db.relationship("Student", backref=db.backref("attendances", lazy=True))
    subject = db.relationship("Subject", backref=db.backref("attendances", lazy=True))
    recorder = db.relationship('User', backref=db.backref('recorded_attendances', lazy=True))

    __table_args__ = (
        db.UniqueConstraint('student_id', 'subject_id', 'date', name='uix_attendance_student_subject_date'),
    )

    def __repr__(self):
        return f"<Attendance {self.id} student={self.student_id} subject={self.subject_id} date={self.date} status={self.status}>"


def calculate_attendance_percentage(student_id, subject_id):
    """Return presence percentage (0-100) for a student in a subject, or None if no records."""
    total = db.session.query(func.count(Attendance.id)).filter(Attendance.student_id == student_id, Attendance.subject_id == subject_id).scalar()
    if not total or total == 0:
        return None
    present = db.session.query(func.count(Attendance.id)).filter(Attendance.student_id == student_id, Attendance.subject_id == subject_id, Attendance.status == AttendanceStatus.PRESENT).scalar()
    try:
        pct = float(present) / float(total) * 100.0
    except Exception:
        return None
    return pct


# ---------------- Finance models ----------------
class FeeCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    monto_base = db.Column(db.Numeric(12, 2), nullable=False)

    def __repr__(self):
        return f"<FeeCategory {self.id} {self.nombre} {self.monto_base}>"


class StudentAccount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    balance_total = db.Column(db.Numeric(12, 2), nullable=False, default=0)

    student = db.relationship('Student', backref=db.backref('account', uselist=False))

    def __repr__(self):
        return f"<StudentAccount {self.id} student={self.student_id} balance={self.balance_total}>"


class InvoiceStatus(PyEnum):
    PENDING = 'PENDING'
    PAID = 'PAID'
    OVERDUE = 'OVERDUE'


class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    monto_total = db.Column(db.Numeric(12, 2), nullable=False)
    fecha_emision = db.Column(db.Date, nullable=False)
    fecha_vencimiento = db.Column(db.Date, nullable=True)
    status = db.Column(db.Enum(InvoiceStatus), nullable=False, default=InvoiceStatus.PENDING)

    student = db.relationship('Student', backref=db.backref('invoices', lazy=True))

    def __repr__(self):
        return f"<Invoice {self.id} student={self.student_id} total={self.monto_total} status={self.status}>"


class PaymentRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    monto_pagado = db.Column(db.Numeric(12, 2), nullable=False)
    fecha_pago = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    metodo_pago = db.Column(db.String(50), nullable=False)
    comprobante_url = db.Column(db.String(500), nullable=True)

    invoice = db.relationship('Invoice', backref=db.backref('payments', lazy=True))

    def __repr__(self):
        return f"<PaymentRecord {self.id} invoice={self.invoice_id} amount={self.monto_pagado}>"


class Scholarship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    porcentaje_descuento = db.Column(db.Numeric(5, 2), nullable=False)
    activa = db.Column(db.Boolean, nullable=False, default=True)

    student = db.relationship('Student', backref=db.backref('scholarships', lazy=True))

    def __repr__(self):
        return f"<Scholarship {self.id} student={self.student_id} {self.porcentaje_descuento}% active={self.activa}>"


# ---------------- Enrollment models ----------------
class AcademicYearStatus(PyEnum):
    OPEN = 'OPEN'
    CLOSED = 'CLOSED'
    ARCHIVED = 'ARCHIVED'


class AcademicYear(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    status = db.Column(db.Enum(AcademicYearStatus), nullable=False, default=AcademicYearStatus.OPEN)

    def __repr__(self):
        return f"<AcademicYear {self.id} {self.nombre} {self.status}>"


class Level(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    nivel_educativo = db.Column(db.String(100), nullable=False)  # e.g. Primaria, Secundaria

    def __repr__(self):
        return f"<Level {self.id} {self.nombre} {self.nivel_educativo}>"


class Section(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    level_id = db.Column(db.Integer, db.ForeignKey('level.id'), nullable=False)
    nombre = db.Column(db.String(10), nullable=False)
    capacidad_maxima = db.Column(db.Integer, nullable=False, default=30)
    aula_fisica = db.Column(db.String(200), nullable=True)

    level = db.relationship('Level', backref=db.backref('sections', lazy=True))

    def __repr__(self):
        return f"<Section {self.id} {self.nombre} level={self.level_id} cap={self.capacidad_maxima}>"

    @property
    def students(self):
        # returns list of Student objects with ACTIVE enrollments in this section
        return [en.student for en in getattr(self, 'enrollments', []) if en.estado == EnrollmentStatus.ACTIVE]


class EnrollmentStatus(PyEnum):
    ACTIVE = 'ACTIVE'
    WITHDRAWN = 'WITHDRAWN'


class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)
    academic_year_id = db.Column(db.Integer, db.ForeignKey('academic_year.id'), nullable=False)
    fecha_inscripcion = db.Column(db.Date, nullable=False, default=lambda: date.today())
    estado = db.Column(db.Enum(EnrollmentStatus), nullable=False, default=EnrollmentStatus.ACTIVE)

    student = db.relationship('Student', backref=db.backref('enrollments', lazy=True))
    section = db.relationship('Section', backref=db.backref('enrollments', lazy=True))
    academic_year = db.relationship('AcademicYear', backref=db.backref('enrollments', lazy=True))

    __table_args__ = (
        db.UniqueConstraint('student_id', 'academic_year_id', 'estado', name='uix_student_year_estado'),
    )

    def __repr__(self):
        return f"<Enrollment {self.id} student={self.student_id} section={self.section_id} year={self.academic_year_id} estado={self.estado}>"
