import pytest
from models import User, Subject, UserRole
from extensions import db

def test_create_subject_with_teacher(client, admin_client, teacher_user):
    """Test creating a subject with a teacher assigned."""
    # Login as admin
    # admin_client fixture already logs in? Let's check conftest.
    # Yes: resp = client.post("/login", ...); assert resp.status_code ...; return client

    # Post new subject data
    data = {
        "name": "Physics 101",
        "code": "PHYS101",
        "category": "Science",
        "credits": "4",
        "description": "Intro to Physics",
        "teacher_id": str(teacher_user.id)
    }

    resp = admin_client.post("/students/subjects/new", data=data, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Materia creada" in resp.data

    # Verify in DB
    subj = Subject.query.filter_by(code="PHYS101").first()
    assert subj is not None
    assert subj.teacher_id == teacher_user.id

def test_edit_subject_assign_teacher(client, admin_client, teacher_user, sample_subjects):
    """Test assigning a teacher to an existing subject."""
    subj = sample_subjects[0]
    assert subj.teacher_id is None

    data = {
        "name": subj.name,
        "code": subj.code,
        "category": "General",
        "credits": "3",
        "description": "Updated subject",
        "teacher_id": str(teacher_user.id)
    }

    resp = admin_client.post(f"/students/subjects/{subj.id}/edit", data=data, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Materia actualizada" in resp.data

    # Verify
    db_subj = db.session.get(Subject, subj.id)
    assert db_subj.teacher_id == teacher_user.id

def test_edit_subject_remove_teacher(client, admin_client, teacher_user, sample_subjects):
    """Test removing a teacher from a subject."""
    subj = sample_subjects[0]
    subj.teacher_id = teacher_user.id
    db.session.commit()

    # Post with empty teacher_id (assuming the select sends empty string for "Sin asignar")
    data = {
        "name": subj.name,
        "code": subj.code,
        "category": "General",
        "credits": "3",
        "description": "Updated subject",
        "teacher_id": ""
    }

    resp = admin_client.post(f"/students/subjects/{subj.id}/edit", data=data, follow_redirects=True)
    assert resp.status_code == 200

    # Verify
    db_subj = db.session.get(Subject, subj.id)
    assert db_subj.teacher_id is None

def test_create_subject_invalid_teacher(client, admin_client):
    """Test creating a subject with a non-existent teacher ID."""
    data = {
        "name": "Chemistry 101",
        "code": "CHEM101",
        "teacher_id": "99999"  # Non-existent ID
    }

    resp = admin_client.post("/students/subjects/new", data=data, follow_redirects=True)
    assert resp.status_code == 200
    # Flash message check might be tricky if it depends on session/template rendering,
    # but follow_redirects=True renders the target page.
    assert b"Profesor no encontrado" in resp.data

    # Verify not created
    subj = Subject.query.filter_by(code="CHEM101").first()
    assert subj is None
