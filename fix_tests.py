import os
import glob
import re

def replace_in_file(filepath, old, new):
    with open(filepath, 'r') as f:
        content = f.read()
    if old in content:
        with open(filepath, 'w') as f:
            f.write(content.replace(old, new))

for filepath in glob.glob('tests/**/*.py', recursive=True):
    # Some basic replacements for the tests
    # Add grade
    replace_in_file(filepath, "client.post(f'/students/{student.id}/add-grade'", "client.post(f'/teacher/{student.id}/add-grade'")
    replace_in_file(filepath, "client.post(f\"/students/{stu.id}/add-grade\"", "client.post(f\"/teacher/{stu.id}/add-grade\"")
    replace_in_file(filepath, "client.post(f'/students/{stu.id}/add-grade'", "client.post(f'/teacher/{stu.id}/add-grade'")
    replace_in_file(filepath, "super_admin_client.post(\n        f'/students/{student.id}/add-grade'", "super_admin_client.post(\n        f'/teacher/{student.id}/add-grade'")

    # Edit/Delete grade
    replace_in_file(filepath, "client.post(f'/students/grades/{g.id}/edit'", "client.post(f'/teacher/grades/{g.id}/edit'")
    replace_in_file(filepath, "client.post(f'/students/grades/{g.id}/delete'", "client.post(f'/teacher/grades/{g.id}/delete'")

    # Gradebook bulk update
    replace_in_file(filepath, "client.post(f'/students/gradebook/{s1.id}/bulk_update'", "client.post(f'/teacher/gradebook/{s1.id}/bulk_update'")

    # Export gradebook
    replace_in_file(filepath, "client.get(f'/students/gradebook/{s1.id}.csv'", "client.get(f'/teacher/gradebook/{s1.id}.csv'")
    replace_in_file(filepath, "client.get(f'/students/reports/gradebook?subject_id={s.id}'", "client.get(f'/teacher/reports/gradebook?subject_id={s.id}'")

    # API grade
    replace_in_file(filepath, "client.post('/students/grades'", "client.post('/teacher/grades'")

    # Teacher subjects
    replace_in_file(filepath, "client.get('/students/teacher/subjects'", "client.get('/teacher/subjects'")
    replace_in_file(filepath, "teacher_client.get(\"/students/teacher/subjects\")", "teacher_client.get(\"/teacher/subjects\")")

# More replacements needed for the tests
for filepath in glob.glob('tests/**/*.py', recursive=True):
    replace_in_file(filepath, "client.post(f'/students/grades/{grade.id}/edit'", "client.post(f'/teacher/grades/{grade.id}/edit'")
    replace_in_file(filepath, "client.post(f'/students/gradebook/{subj.id}/bulk_update'", "client.post(f'/teacher/gradebook/{subj.id}/bulk_update'")
    replace_in_file(filepath, "client.get(f\"/students/reports/gradebook?subject_id={s.id}\")", "client.get(f\"/teacher/reports/gradebook?subject_id={s.id}\")")
    replace_in_file(filepath, "f\"/students/grades/{grade.id}/edit\"", "f\"/teacher/grades/{grade.id}/edit\"")

for filepath in glob.glob('tests/**/*.py', recursive=True):
    replace_in_file(filepath, "client.post(f'/students/grades/{grade.id}/delete'", "client.post(f'/teacher/grades/{grade.id}/delete'")
    replace_in_file(filepath, "client.get(f'/students/gradebook/{subj.id}.csv'", "client.get(f'/teacher/gradebook/{subj.id}.csv'")

for filepath in glob.glob('tests/**/*.py', recursive=True):
    replace_in_file(filepath, "client.post(f\"/students/grades/{grade.id}/delete\"", "client.post(f\"/teacher/grades/{grade.id}/delete\"")
