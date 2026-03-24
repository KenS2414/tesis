from werkzeug.security import generate_password_hash


def test_create_subject_with_extended_fields(super_admin_client, app):
    from extensions import db
    from models import Subject

    client = super_admin_client
    data = {
        'name': 'Física Moderna',
        'code': 'PHY201',
        'year_group': '5to Año',
        'category': 'Física',
        'credits': '5',
        'description': 'Curso avanzado de física moderna',
    }
    resp = client.post('/students/subjects/new', data=data, follow_redirects=True)
    assert resp.status_code in (200, 302)

    s = Subject.query.filter_by(code='PHY201').first()
    assert s is not None
    assert s.name == 'Física Moderna'
    assert s.year_group == '5to Año'
    assert s.category == 'Física'
    assert s.credits == 5
    assert 'moderna' in (s.description or '').lower()


def test_create_subject_redirects_to_subjects_list(super_admin_client, app):
    resp = super_admin_client.post(
        '/students/subjects/new',
        data={
            'name': 'Arte',
            'code': 'ART101',
            'year_group': '2do Año',
        },
        follow_redirects=False,
    )

    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/students/subjects')


def test_edit_subject_extended_fields(super_admin_client, app, sample_subjects):
    from extensions import db
    from models import Subject

    subj = sample_subjects[0]
    client = super_admin_client
    data = {
        'name': 'Matemáticas Avanzadas',
        'code': 'MATH201',
        'year_group': '4to Año',
        'category': 'Matemáticas',
        'credits': '6',
        'description': 'Nivel avanzado',
    }
    resp = client.post(f'/students/subjects/{subj.id}/edit', data=data, follow_redirects=True)
    assert resp.status_code in (200, 302)

    s = db.session.get(Subject, subj.id)
    assert s.name == 'Matemáticas Avanzadas'
    assert s.code == 'MATH201'
    assert s.year_group == '4to Año'
    assert s.category == 'Matemáticas'
    assert s.credits == 6


def test_edit_subject_redirects_to_subjects_list(super_admin_client, app, sample_subjects):
    subj = sample_subjects[0]

    resp = super_admin_client.post(
        f'/students/subjects/{subj.id}/edit',
        data={
            'name': subj.name,
            'code': subj.code,
            'year_group': '1er Año',
        },
        follow_redirects=False,
    )

    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/students/subjects')


def test_list_subjects_search_and_filter(super_admin_client, app):
    from extensions import db
    from models import Subject

    # create subjects with categories
    s1 = Subject(name='Biología', code='BIO101', category='Ciencias')
    s2 = Subject(name='Química', code='CHEM101', category='Ciencias')
    s3 = Subject(name='Filosofía', code='PHIL101', category='Humanidades')
    db.session.add_all([s1, s2, s3])
    db.session.commit()

    client = super_admin_client
    # filter by category
    resp = client.get('/students/subjects?category=Ciencias')
    assert resp.status_code == 200
    body = resp.data.decode('utf-8')
    assert 'Biología' in body
    assert 'Química' in body
    assert 'Filosofía' not in body

    # search by q
    resp2 = client.get('/students/subjects?q=Filosofía')
    assert resp2.status_code == 200
    assert 'Filosofía' in resp2.data.decode('utf-8')


def test_list_subjects_unassigned_filter_and_teacher_load(super_admin_client, app):
    from extensions import db
    from models import Subject, User

    teacher = User(
        username='teacher.report@example.com',
        password_hash=generate_password_hash('pass123'),
        role='teacher',
    )
    db.session.add(teacher)
    db.session.flush()

    assigned = Subject(name='Geometría', code='MATH301', year_group='3er Año', teacher_id=teacher.id)
    unassigned = Subject(name='Música', code='MUS101', year_group='1er Año')
    db.session.add_all([assigned, unassigned])
    db.session.commit()

    resp = super_admin_client.get('/students/subjects?unassigned=1')
    assert resp.status_code == 200
    body = resp.data.decode('utf-8')

    assert 'Música' in body
    assert 'Geometría' not in body
    assert 'Carga docente' in body
    assert 'teacher.report@example.com' in body
    assert '>1<' in body


def test_list_subjects_grouped_by_year_group(super_admin_client, app):
    from extensions import db
    from models import Subject

    db.session.add_all([
        Subject(name='Castellano', code='CAS101', year_group='1er Año'),
        Subject(name='Biología', code='BIO201', year_group='2do Año'),
    ])
    db.session.commit()

    resp = super_admin_client.get('/students/subjects')
    assert resp.status_code == 200
    body = resp.data.decode('utf-8')

    assert '1er Año' in body
    assert '2do Año' in body
    assert 'Castellano' in body
    assert 'Biología' in body
