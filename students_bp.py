import inspect
from datetime import date, datetime

from flask import (
    Blueprint,
    Response,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from marshmallow import Schema, fields
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename

from extensions import db
from models import Attendance, Grade, Student, Subject, User, UserRole
from scripts.import_export import (
    export_grades_csv,
    export_students_csv,
    export_subjects_csv,
    import_grades_csv,
    import_students_csv,
    import_subjects_csv,
)
from utils.auth import requires_roles

students_bp = Blueprint("students_bp", __name__, url_prefix="/students")

YEAR_GROUP_OPTIONS = (
    "1er Grado",
    "2do Grado",
    "3er Grado",
    "4to Grado",
    "5to Grado",
    "6to Grado",
    "1er Año",
    "2do Año",
    "3er Año",
    "4to Año",
    "5to Año",
)

PASSING_SCORE_20 = 10.0


@students_bp.route("/")
@login_required
def list_students():
    # pagination, search and advanced filter by subject
    q = request.args.get("q", type=str, default=None)
    subject_id = request.args.get("subject_id", type=int)
    page = request.args.get("page", type=int, default=1)
    per_page = 10

    query = Student.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(
                Student.first_name.ilike(like),
                Student.last_name.ilike(like),
                Student.email.ilike(like),
            )
        )

    if subject_id:
        # filter students who have grades for the given subject
        query = query.join(Grade).filter(Grade.subject_id == subject_id)

    query = query.order_by(Student.last_name, Student.first_name)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    subjects = Subject.query.order_by(Subject.name).all()
    return render_template(
        "students/list.html",
        students=pagination.items,
        pagination=pagination,
        q=q,
        subjects=subjects,
        subject_id=subject_id,
    )


@students_bp.route("/new", methods=["GET", "POST"])
@login_required
@requires_roles(UserRole.SUPER_ADMIN)
def student_create():
    subjects = Subject.query.order_by(Subject.name).all()
    year_group_options = YEAR_GROUP_OPTIONS
    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = (request.form.get("email") or "").strip() or None
        login_username = (request.form.get("login_username") or "").strip() or None
        login_password = request.form.get("login_password") or ""
        current_year_group = (
            request.form.get("current_year_group") or ""
        ).strip() or None
        if current_year_group and current_year_group not in year_group_options:
            flash("Año inválido para el estudiante.", "warning")
            return render_template(
                "students/form.html",
                student=None,
                subjects=subjects,
                year_group_options=year_group_options,
            )
        if login_username and not login_password:
            flash("Si defines usuario, debes definir contraseña.", "warning")
            return render_template(
                "students/form.html",
                student=None,
                subjects=subjects,
                year_group_options=year_group_options,
            )
        if login_password and not login_username:
            flash("Si defines contraseña, debes definir usuario.", "warning")
            return render_template(
                "students/form.html",
                student=None,
                subjects=subjects,
                year_group_options=year_group_options,
            )
        if login_username and email and login_username != email:
            flash(
                "Para vincular el perfil, Email y Usuario deben coincidir.", "warning"
            )
            return render_template(
                "students/form.html",
                student=None,
                subjects=subjects,
                year_group_options=year_group_options,
            )
        if login_username and User.query.filter_by(username=login_username).first():
            flash("El usuario de acceso ya existe.", "warning")
            return render_template(
                "students/form.html",
                student=None,
                subjects=subjects,
                year_group_options=year_group_options,
            )
        dob_raw = request.form.get("dob")
        dob = None
        if dob_raw:
            try:
                dob = datetime.strptime(dob_raw, "%Y-%m-%d").date()
            except ValueError:
                flash("Formato de fecha inválido. Use YYYY-MM-DD.", "warning")
                return render_template(
                    "students/form.html",
                    student=None,
                    subjects=subjects,
                    year_group_options=year_group_options,
                )

        cedula = (request.form.get("cedula") or "").strip() or None
        section = (request.form.get("section") or "").strip() or None

        student = Student(
            first_name=first_name,
            last_name=last_name,
            email=email,
            current_year_group=current_year_group,
            dob=dob,
            cedula=cedula,
            section=section,
        )
        db.session.add(student)
        db.session.flush()  # flush to get student.id for photo

        photo = request.files.get("photo")
        if photo and photo.filename:
            from utils.aws import upload_bytes_to_s3

            filename = secure_filename(photo.filename)
            key_name = f"students/{student.id}/photo_{filename}"
            upload_bytes_to_s3(photo.read(), key_name, content_type=photo.content_type)
            student.photo_filename = key_name
        if login_username:
            linked_user = User(
                username=login_username,
                password_hash=generate_password_hash(login_password),
                role=UserRole.STUDENT,
            )
            db.session.add(linked_user)
        db.session.commit()

        # Auto-assign subjects based on current_year_group
        if current_year_group:
            subjects_to_assign = Subject.query.filter_by(
                year_group=current_year_group
            ).all()
            for subj in subjects_to_assign:
                grade = Grade(student_id=student.id, subject_id=subj.id, value=None)
                db.session.add(grade)
            db.session.commit()
        else:
            # Fallback to manually selected subjects (if any)
            selected_subjects = request.form.getlist("subjects")
            if selected_subjects:
                for sid in selected_subjects:
                    try:
                        subject_id = int(sid)
                        grade = Grade(
                            student_id=student.id, subject_id=subject_id, value=None
                        )
                        db.session.add(grade)
                    except ValueError:
                        continue
                db.session.commit()

        flash("Estudiante creado.", "success")
        return redirect(url_for("students_bp.list_students"))
    return render_template(
        "students/form.html",
        student=None,
        subjects=subjects,
        year_group_options=year_group_options,
    )


@students_bp.route("/<int:student_id>/edit", methods=["GET", "POST"])
@login_required
@requires_roles(UserRole.SUPER_ADMIN)
def student_edit(student_id):
    student = db.session.get(Student, student_id)
    if student is None:
        flash("El estudiante no existe o fue eliminado.", "warning")
        return redirect(url_for("students_bp.list_students"))
    year_group_options = YEAR_GROUP_OPTIONS
    if request.method == "POST":
        student.first_name = request.form.get("first_name")
        student.last_name = request.form.get("last_name")
        student.email = request.form.get("email")
        current_year_group = (
            request.form.get("current_year_group") or ""
        ).strip() or None

        # If the student already has a year group, it shouldn't be overridden from the form.
        # It can only advance automatically.
        if student.current_year_group:
            current_year_group = student.current_year_group

        if current_year_group and current_year_group not in year_group_options:
            flash("Año inválido para el estudiante.", "warning")
            return render_template(
                "students/form.html",
                student=student,
                year_group_options=year_group_options,
            )

        dob_raw = request.form.get("dob")
        if dob_raw:
            try:
                student.dob = datetime.strptime(dob_raw, "%Y-%m-%d").date()
            except ValueError:
                flash("Formato de fecha inválido. Use YYYY-MM-DD.", "warning")
                return render_template(
                    "students/form.html",
                    student=student,
                    year_group_options=year_group_options,
                )
        else:
            student.dob = None

        old_year_group = student.current_year_group
        student.current_year_group = current_year_group

        # If year group was changed (e.g. from empty to a specific year), auto-assign subjects
        if current_year_group and current_year_group != old_year_group:
            subjects_to_assign = Subject.query.filter_by(
                year_group=current_year_group
            ).all()
            subject_ids = [s.id for s in subjects_to_assign]
            # Bulk fetch existing grades to avoid N+1 query
            existing_subject_ids = {
                g.subject_id
                for g in Grade.query.filter(
                    Grade.student_id == student.id, Grade.subject_id.in_(subject_ids)
                ).all()
            }
            for subj in subjects_to_assign:
                # Check if grade already exists in memory to avoid duplicates
                if subj.id not in existing_subject_ids:
                    grade = Grade(student_id=student.id, subject_id=subj.id, value=None)
                    db.session.add(grade)

        student.cedula = (request.form.get("cedula") or "").strip() or None
        student.section = (request.form.get("section") or "").strip() or None

        photo = request.files.get("photo")
        if photo and photo.filename:
            from utils.aws import upload_bytes_to_s3

            filename = secure_filename(photo.filename)
            key_name = f"students/{student.id}/photo_{filename}"
            upload_bytes_to_s3(photo.read(), key_name, content_type=photo.content_type)
            student.photo_filename = key_name

        db.session.commit()
        flash("Estudiante actualizado.", "success")
        return redirect(url_for("students_bp.list_students"))
    return render_template(
        "students/form.html", student=student, year_group_options=year_group_options
    )


@students_bp.route("/<int:student_id>/delete", methods=["POST"])
@login_required
@requires_roles(UserRole.SUPER_ADMIN)
def student_delete(student_id):
    student = db.session.get(Student, student_id)
    if student is None:
        flash("El estudiante no existe o ya fue eliminado.", "warning")
        return redirect(url_for("students_bp.list_students"))
    db.session.delete(student)
    db.session.commit()
    flash("Estudiante eliminado.", "info")
    return redirect(url_for("students_bp.list_students"))


@students_bp.route("/<int:student_id>")
@login_required
def student_detail(student_id):
    student = db.session.get(Student, student_id)
    if student is None:
        abort(404)
    # If the current user is a student, only allow viewing their own profile
    if current_user.role == UserRole.STUDENT:
        linked = current_user.get_student()
        if linked is None or linked.id != student.id:
            return ({"error": "forbidden"}, 403)
        # For students, only show subjects where they have grades (or are enrolled)
        subjects = (
            db.session.query(Subject)
            .join(Grade, Grade.subject_id == Subject.id)
            .filter(Grade.student_id == student.id)
            .order_by(Subject.name)
            .distinct()
            .all()
        )
    else:
        subjects = Subject.query.order_by(Subject.name).all()

    if student.photo_filename and current_app.config.get("S3_BUCKET"):
        from utils.aws import get_presigned_url

        student.photo_filename = get_presigned_url(student.photo_filename)

    grades = (
        Grade.query.filter_by(student_id=student.id)
        .join(Subject)
        .order_by(Subject.year_group, Subject.name)
        .all()
    )
    return render_template(
        "students/detail.html", student=student, subjects=subjects, grades=grades
    )


@students_bp.route("/subjects/new", methods=["GET", "POST"])
@login_required
@requires_roles(UserRole.SUPER_ADMIN)
def new_subject():
    teachers = User.query.filter_by(role=UserRole.TEACHER).order_by(User.username).all()
    year_group_options = YEAR_GROUP_OPTIONS
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        year_group = (request.form.get("year_group") or "").strip() or None
        category = request.form.get("category")
        credits = request.form.get("credits")
        description = request.form.get("description")
        teacher_id = request.form.get("teacher_id")

        if not name:
            flash("Nombre requerido", "warning")
            return render_template(
                "students/subject_form.html",
                teachers=teachers,
                year_group_options=year_group_options,
            )
        if year_group and year_group not in year_group_options:
            flash("Año/Grupo inválido.", "warning")
            return render_template(
                "students/subject_form.html",
                teachers=teachers,
                year_group_options=year_group_options,
            )
        # validate credits if provided
        credits_val = None
        if credits:
            try:
                credits_val = int(credits)
                if credits_val < 0:
                    flash("Credits must be non-negative.", "warning")
                    return render_template(
                        "students/subject_form.html",
                        teachers=teachers,
                        year_group_options=year_group_options,
                    )
            except ValueError:
                flash("Formato de credits inválido.", "warning")
                return render_template(
                    "students/subject_form.html",
                    teachers=teachers,
                    year_group_options=year_group_options,
                )

        # validate teacher_id if provided
        tid = None
        if teacher_id:
            try:
                tid = int(teacher_id)
                # verify teacher exists
                if not db.session.get(User, tid):
                    flash("Profesor no encontrado.", "warning")
                    return render_template(
                        "students/subject_form.html",
                        teachers=teachers,
                        year_group_options=year_group_options,
                    )
            except ValueError:
                flash("ID de profesor inválido.", "warning")
                return render_template(
                    "students/subject_form.html",
                    teachers=teachers,
                    year_group_options=year_group_options,
                )

        s = Subject(
            name=name,
            code=code,
            year_group=year_group,
            category=category,
            credits=credits_val,
            description=description,
            teacher_id=tid,
        )
        db.session.add(s)
        db.session.commit()
        flash("Materia creada.", "success")
        return redirect(url_for("students_bp.list_subjects"))
    return render_template(
        "students/subject_form.html",
        teachers=teachers,
        year_group_options=year_group_options,
    )


@students_bp.route("/subjects/<int:subject_id>/edit", methods=["GET", "POST"])
@login_required
@requires_roles(UserRole.SUPER_ADMIN)
def edit_subject(subject_id):
    s = db.session.get(Subject, subject_id)
    if s is None:
        abort(404)
    teachers = User.query.filter_by(role=UserRole.TEACHER).order_by(User.username).all()
    year_group_options = YEAR_GROUP_OPTIONS
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        year_group = (request.form.get("year_group") or "").strip() or None
        category = request.form.get("category")
        credits = request.form.get("credits")
        description = request.form.get("description")
        teacher_id = request.form.get("teacher_id")

        if not name:
            flash("Nombre requerido", "warning")
            return render_template(
                "students/subject_form.html",
                subject=s,
                teachers=teachers,
                year_group_options=year_group_options,
            )
        if year_group and year_group not in year_group_options:
            flash("Año/Grupo inválido.", "warning")
            return render_template(
                "students/subject_form.html",
                subject=s,
                teachers=teachers,
                year_group_options=year_group_options,
            )
        # validate credits if provided
        credits_val = None
        if credits:
            try:
                credits_val = int(credits)
                if credits_val < 0:
                    flash("Credits must be non-negative.", "warning")
                    return render_template(
                        "students/subject_form.html",
                        subject=s,
                        teachers=teachers,
                        year_group_options=year_group_options,
                    )
            except ValueError:
                flash("Formato de credits inválido.", "warning")
                return render_template(
                    "students/subject_form.html",
                    subject=s,
                    teachers=teachers,
                    year_group_options=year_group_options,
                )

        # validate teacher_id if provided
        tid = None
        if teacher_id:
            try:
                tid = int(teacher_id)
                # verify teacher exists
                if not db.session.get(User, tid):
                    flash("Profesor no encontrado.", "warning")
                    return render_template(
                        "students/subject_form.html",
                        subject=s,
                        teachers=teachers,
                        year_group_options=year_group_options,
                    )
            except ValueError:
                flash("ID de profesor inválido.", "warning")
                return render_template(
                    "students/subject_form.html",
                    subject=s,
                    teachers=teachers,
                    year_group_options=year_group_options,
                )

        s.name = name
        s.code = code
        s.year_group = year_group
        s.category = category
        s.credits = credits_val
        s.description = description
        s.teacher_id = tid
        db.session.commit()
        flash("Materia actualizada.", "success")
        return redirect(url_for("students_bp.list_subjects"))
    return render_template(
        "students/subject_form.html",
        subject=s,
        teachers=teachers,
        year_group_options=year_group_options,
    )


@students_bp.route("/subjects")
@login_required
@requires_roles(UserRole.SUPER_ADMIN)
def list_subjects():
    # paginated list of subjects with search and category filter
    q = request.args.get("q", type=str, default=None)
    category = request.args.get("category", type=str, default=None)
    unassigned = request.args.get("unassigned", type=int, default=0)
    page = request.args.get("page", type=int, default=1)
    per_page = request.args.get("per_page", type=int, default=10)

    query = Subject.query
    if q:
        like = f"%{q}%"
        query = query.filter(db.or_(Subject.name.ilike(like), Subject.code.ilike(like)))
    if category:
        query = query.filter(Subject.category == category)
    if unassigned:
        query = query.filter(Subject.teacher_id.is_(None))
    query = query.order_by(Subject.year_group, Subject.name)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    grouped_subjects = []
    groups = {}
    for subject in pagination.items:
        group_name = subject.year_group or "Sin año/grupo"
        groups.setdefault(group_name, []).append(subject)
    grouped_subjects = list(groups.items())
    teacher_load = (
        db.session.query(
            User.id,
            User.username,
            db.func.count(Subject.id).label("subjects_count"),
        )
        .outerjoin(Subject, Subject.teacher_id == User.id)
        .filter(User.role == UserRole.TEACHER)
        .group_by(User.id, User.username)
        .order_by(User.username)
        .all()
    )
    return render_template(
        "students/subjects_list.html",
        subjects=pagination.items,
        grouped_subjects=grouped_subjects,
        pagination=pagination,
        q=q,
        category=category,
        unassigned=unassigned,
        teacher_load=teacher_load,
    )


@students_bp.route("/subjects/<int:subject_id>")
@login_required
def subject_detail(subject_id):
    subj = db.session.get(Subject, subject_id)
    if subj is None:
        abort(404)
    # Student view: only their own grades for this subject
    if current_user.role == UserRole.STUDENT:
        linked = current_user.get_student()
        if linked is None:
            flash("No tienes perfil de estudiante vinculado.", "warning")
            return redirect(url_for("students_bp.list_subjects"))
        grades = Grade.query.filter_by(student_id=linked.id, subject_id=subj.id).all()
        return render_template(
            "students/subject_detail.html", subject=subj, student=linked, grades=grades
        )

    # Teacher/Admin view: show students with grades for this subject
    if (
        current_user.role == UserRole.TEACHER
        and subj.teacher_id
        and subj.teacher_id != current_user.id
    ):
        return ({"error": "forbidden: not teacher of this subject"}, 403)

    students = (
        db.session.query(Student)
        .join(Grade, Grade.student_id == Student.id)
        .filter(Grade.subject_id == subj.id)
        .group_by(Student.id)
        .order_by(Student.last_name, Student.first_name)
        .all()
    )
    data = []
    for s in students:
        g = Grade.query.filter_by(student_id=s.id, subject_id=subj.id).all()
        avg = s.weighted_average(subj.id)
        data.append({"student": s, "grades": g, "average": avg})
    return render_template("students/subject_detail.html", subject=subj, data=data)


@students_bp.route("/subjects/<int:subject_id>/delete", methods=["POST"])
@login_required
@requires_roles(UserRole.SUPER_ADMIN)
def delete_subject(subject_id):
    s = db.session.get(Subject, subject_id)
    if s is None:
        abort(404)
    try:
        db.session.delete(s)
        db.session.commit()
        flash("Materia eliminada.", "info")
    except Exception as e:
        db.session.rollback()
        flash(f"Error eliminando materia: {e}", "danger")
    return redirect(url_for("students_bp.list_subjects"))


@students_bp.route("/users/<int:user_id>/role", methods=["POST"])
@login_required
@requires_roles(UserRole.SUPER_ADMIN)
def set_user_role(user_id):
    u = db.session.get(User, user_id)
    if u is None:
        abort(404)
    role = request.form.get("role")
    if not role:
        flash("Role requerido.", "warning")
        return redirect(url_for("students_bp.list_students"))
    try:
        u.set_role(role)
        db.session.commit()
        flash("Role actualizado.", "success")
    except ValueError as e:
        db.session.rollback()
        flash(str(e), "warning")
    except Exception as e:
        db.session.rollback()
        flash(f"Error actualizando role: {e}", "danger")
    return redirect(url_for("students_bp.list_students"))


@students_bp.route("/users")
@login_required
@requires_roles(UserRole.SUPER_ADMIN)
def list_users():
    users = User.query.order_by(User.username).all()
    return render_template("students/users_list.html", users=users)


@students_bp.route("/users/new-staff", methods=["GET", "POST"])
@login_required
@requires_roles(UserRole.SUPER_ADMIN)
def create_staff_user():
    roles = [UserRole.TEACHER, UserRole.ADMIN, UserRole.ENROLLMENT, UserRole.TREASURY]
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        role = request.form.get("role") or UserRole.TEACHER

        if not username or not password:
            flash("Usuario y contraseña son obligatorios.", "warning")
            return render_template("students/staff_form.html", roles=roles)

        if role not in roles:
            flash("Rol inválido.", "warning")
            return render_template("students/staff_form.html", roles=roles)

        if User.query.filter_by(username=username).first():
            flash("El usuario ya existe.", "warning")
            return render_template("students/staff_form.html", roles=roles)

        staff_user = User(
            username=username,
            password_hash=generate_password_hash(password),
            role=role,
        )
        db.session.add(staff_user)
        db.session.commit()
        flash(f"Perfil de {role} creado correctamente.", "success")
        return redirect(url_for("students_bp.list_users"))

    return render_template("students/staff_form.html", roles=roles)


@students_bp.route("/grades/student/<int:student_id>")
@login_required
def student_grades(student_id):
    s = db.session.get(Student, student_id)
    if s is None:
        abort(404)
    # group by subject and periodo
    out = {}
    grades = Grade.query.filter_by(student_id=s.id).join(Subject).all()
    for g in grades:
        subj = g.subject
        periodo = g.periodo.nombre if g.periodo else "unknown"
        key = f"{subj.id}:{periodo}"
        if key not in out:
            out[key] = {
                "subject_id": subj.id,
                "subject_name": subj.name,
                "periodo": periodo,
                "grades": [],
            }
        out[key]["grades"].append(
            {
                "grade_id": g.id,
                "assessment_category": (
                    g.assessment_category.nombre if g.assessment_category else None
                ),
                "value": float(g.value) if g.value is not None else None,
                "comment": g.comment,
                "fecha_registro": (
                    g.fecha_registro.isoformat() if g.fecha_registro else None
                ),
            }
        )
    return out


@students_bp.route("/import", methods=["POST"])
@login_required
@requires_roles(UserRole.SUPER_ADMIN)
def import_csv():
    # expects file in 'file' and type in 'type' (students|subjects|grades)
    f = request.files.get("file")
    if not f or not f.filename:
        flash("Fichero requerido.", "warning")
        return redirect(url_for("students_bp.list_students"))
    typ = request.form.get("type", "students")
    try:
        if typ == "students":
            count = import_students_csv(f.stream)
        elif typ == "subjects":
            count = import_subjects_csv(f.stream)
        elif typ == "grades":
            count = import_grades_csv(f.stream)
        else:
            flash("Tipo inválido.", "warning")
            return redirect(url_for("students_bp.list_students"))
        flash(f"Importados {count} registros ({typ}).", "success")
    except Exception as e:
        flash(f"Error importando CSV: {e}", "danger")
    return redirect(url_for("students_bp.list_students"))


@students_bp.route("/export.csv")
@login_required
@requires_roles(UserRole.SUPER_ADMIN)
def export_csv():
    typ = request.args.get("type", "students")
    if typ == "students":
        data = export_students_csv()
        fname = "students.csv"
    elif typ == "subjects":
        data = export_subjects_csv()
        fname = "subjects.csv"
    elif typ == "grades":
        data = export_grades_csv()
        fname = "grades.csv"
    else:
        flash("Tipo inválido.", "warning")
        return redirect(url_for("students_bp.list_students"))
    # Force exact Content-Type without charset to satisfy strict tests
    return Response(
        data,
        headers={
            "Content-Disposition": f"attachment; filename={fname}",
            "Content-Type": "text/csv",
        },
    )


# ---------------- Attendance endpoints ----------------


class AttendanceSchema(Schema):
    id = fields.Int(dump_only=True)
    student_id = fields.Int(required=True)
    subject_id = fields.Int(required=True)

    @staticmethod
    def _date_field_with_default(default_callable):
        sig = inspect.signature(fields.Date.__init__)
        if "missing" in sig.parameters:
            return fields.Date(missing=default_callable)
        if "load_default" in sig.parameters:
            return fields.Date(load_default=default_callable)
        return fields.Date()

    date = _date_field_with_default(date.today)
    status = fields.Str(required=True)
    remarks = fields.Str(allow_none=True)
    recorded_by = fields.Int(dump_only=True)


@students_bp.route("/attendance/student/<int:student_id>")
@login_required
def attendance_student(student_id):
    s = db.session.get(Student, student_id)
    if s is None:
        abort(404)
    q = (
        Attendance.query.filter_by(student_id=student_id)
        .order_by(Attendance.date.desc())
        .all()
    )
    schema = AttendanceSchema(many=True)
    out = schema.dump(q)
    return {"student_id": student_id, "attendance": out}
