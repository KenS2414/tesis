import os
import glob

def replace_in_file(filepath, old, new):
    with open(filepath, 'r') as f:
        content = f.read()
    if old in content:
        with open(filepath, 'w') as f:
            f.write(content.replace(old, new))

for filepath in glob.glob('templates/**/*.html', recursive=True):
    replace_in_file(filepath, "students_bp.add_grade", "teachers_bp.add_grade")
    replace_in_file(filepath, "students_bp.teacher_subjects", "teachers_bp.teacher_subjects")
    replace_in_file(filepath, "students_bp.edit_grade", "teachers_bp.edit_grade")
    replace_in_file(filepath, "students_bp.delete_grade", "teachers_bp.delete_grade")
    replace_in_file(filepath, "students_bp.report_gradebook", "teachers_bp.report_gradebook")
    replace_in_file(filepath, "students_bp.gradebook_bulk_update", "teachers_bp.gradebook_bulk_update")
    replace_in_file(filepath, "students_bp.export_gradebook", "teachers_bp.export_gradebook")

for filepath in glob.glob('templates/**/*.html', recursive=True):
    replace_in_file(filepath, "students_bp.create_grade", "teachers_bp.create_grade")
    replace_in_file(filepath, "students_bp.subject_report", "teachers_bp.subject_report")
