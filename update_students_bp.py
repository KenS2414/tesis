import re

with open('students_bp.py', 'r') as f:
    content = f.read()

# Remove unused models: AcademicPeriod, AssessmentCategory
# "from models import AssessmentCategory, AcademicPeriod  # AssessmentCategory is used for DB validation"
content = re.sub(r'from models import AssessmentCategory, AcademicPeriod.*?\n', '', content)

# Also remove export_gradebook_csv import from scripts.import_export
content = content.replace('    export_gradebook_csv,\n', '')

# Remove helper functions
content = re.sub(r'def _is_passing_average.*?return value >= PASSING_SCORE_20\n\n\n', '', content, flags=re.DOTALL)
content = re.sub(r'def _promote_student_if_ready.*?return next_year\n\n\n', '', content, flags=re.DOTALL)

# Remove routes
content = re.sub(r'@students_bp\.route\(\'/<int:student_id>/add-grade\', methods=\[\'POST\'\]\).*?return redirect\(url_for\(\'students_bp\.student_detail\', student_id=student\.id\)\)\n\n\n', '', content, flags=re.DOTALL)
content = re.sub(r'@students_bp\.route\(\'/grades/<int:grade_id>/edit\', methods=\[\'GET\', \'POST\'\]\).*?return render_template\(\'students/grade_form\.html\', grade=g\)\n\n\n', '', content, flags=re.DOTALL)
content = re.sub(r'@students_bp\.route\(\'/grades/<int:grade_id>/delete\', methods=\[\'POST\'\]\).*?return redirect\(url_for\(\'students_bp\.student_detail\', student_id=sid\)\)\n\n\n', '', content, flags=re.DOTALL)
content = re.sub(r'@students_bp\.route\(\'/reports/gradebook\'\).*?headers={"Content-Disposition": f"attachment; filename=gradebook_{subj\.id}\.pdf"}\)\n\n\n', '', content, flags=re.DOTALL)
content = re.sub(r'@students_bp\.route\(\'/grades\', methods=\[\'POST\'\]\).*?return \(\{\'error\': str\(e\)\}, 500\)\n\n\n', '', content, flags=re.DOTALL)
content = re.sub(r'@students_bp\.route\(\'/grades/subject/<int:subject_id>/report\'\).*?return report\n\n\n', '', content, flags=re.DOTALL)
content = re.sub(r'@students_bp\.route\(\'/teacher/subjects\'\).*?return render_template\(\'students/teacher_subjects\.html\', data=data\)\n\n\n', '', content, flags=re.DOTALL)
content = re.sub(r'@students_bp\.route\(\'/gradebook/<int:subject_id>/bulk_update\', methods=\[\'POST\'\]\).*?return \(\{\'status\': \'error\', \'error\': str\(e\)\}, 400\)\n\n\n', '', content, flags=re.DOTALL)
content = re.sub(r'@students_bp\.route\(\'/gradebook/<int:subject_id>\.csv\'\).*?headers={"Content-Disposition": f"attachment; filename={fname}", "Content-Type": "text/csv"}\)\n\n\n', '', content, flags=re.DOTALL)

with open('students_bp.py', 'w') as f:
    f.write(content)
