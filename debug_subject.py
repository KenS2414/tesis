from app import create_app
from extensions import db
import init_db
from werkzeug.security import generate_password_hash
from models import User, Subject
import os

app = create_app()
os.environ.setdefault('SECRET_KEY','test-secret-crud')
os.environ.setdefault('ADMIN_PASSWORD','adminpass123')
init_db.init_db()
with app.app_context():
    # create admin user
    u=User.query.filter_by(username='admin2@example.com').first()
    if not u:
        u=User(username='admin2@example.com', password_hash=generate_password_hash('adminpass'), role='admin')
        db.session.add(u)
        db.session.commit()
    client=app.test_client()
    resp=client.post('/login', data={'username':'admin2@example.com','password':'adminpass'}, follow_redirects=True)
    print('login code', resp.status_code)
    resp=client.post('/students/subjects/new', data={'name':'History','code':'HIS101'}, follow_redirects=True)
    print('post code', resp.status_code)
    print(resp.get_data(as_text=True))
