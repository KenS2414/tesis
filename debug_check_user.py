from app import create_app
from models import User
from werkzeug.security import check_password_hash

app = create_app()

with app.app_context():
    u = User.query.filter_by(username='admin2@example.com').first()
    print('User exists?', bool(u))
    if u:
        print('Stored hash:', u.password_hash[:60] if u.password_hash else None)
        print('Password matches adminpass?', check_password_hash(u.password_hash, 'adminpass'))
    else:
        print('No user found')
