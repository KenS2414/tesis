import os
from app import create_app
from extensions import db
from models import User, Student, Subject, Grade
from werkzeug.security import generate_password_hash, check_password_hash
import init_db

app = create_app()

# Clean DB file
DB_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), 'app.db'))
try:
    os.remove(DB_FILE)
except Exception:
    pass

os.environ.setdefault('SECRET_KEY','test-secret-crud')
os.environ.setdefault('ADMIN_PASSWORD','adminpass123')

init_db.init_db()

with app.app_context():
    print('Existing users:', User.query.all())
    # create admin2 and teacher2
    def create_user(username, password, role='user'):
        u = User.query.filter_by(username=username).first()
        if u:
            u.password_hash = generate_password_hash(password)
            u.role = role
        else:
            u = User(username=username, password_hash=generate_password_hash(password), role=role)
            db.session.add(u)
        db.session.commit()
        return u

    admin = create_user('admin2@example.com', 'adminpass', role='admin')
    teacher = create_user('teacher2@example.com', 'teachpass', role='teacher')
    print('After create, users:', User.query.all())

    client = app.test_client()
    resp = client.post('/login', data={'username':'admin2@example.com','password':'adminpass'}, follow_redirects=True)
    print('login response code', resp.status_code)
    print('login response body:', resp.get_data(as_text=True)[:200])
    # attempt to create subject
    resp2 = client.post('/students/subjects/new', data={'name':'History','code':'HIS101'}, follow_redirects=True)
    print('subject post code', resp2.status_code)
    print('subject post body start:', resp2.get_data(as_text=True)[:200])
    print('Subjects in DB:', Subject.query.all())
