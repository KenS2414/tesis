import time
import os
from decimal import Decimal
from app import create_app
from extensions import db
from models import Student, StudentAccount, Invoice, FeeCategory, Scholarship, User
from werkzeug.security import generate_password_hash

def setup_data(app):
    with app.app_context():
        db.create_all()
        # Create categories
        fee = FeeCategory(nombre='Matricula', monto_base=Decimal('50.00'))
        db.session.add(fee)

        # Create an admin user to bypass auth
        if not User.query.filter_by(username='admin_test').first():
            admin_user = User(
                username='admin_test',
                password_hash=generate_password_hash('password'),
                role='admin'
            )
            db.session.add(admin_user)

        # Create 1000 students
        print("Creating students...")
        students = []
        for i in range(1000):
            st = Student(
                cedula=f'V-{100000+i}'[:8],
                first_name=f'Student{i}',
                last_name=f'Test{i}',
                current_year_group=f'1er Año'
            )
            students.append(st)
        db.session.bulk_save_objects(students)
        db.session.commit()

        print(f"Created {Student.query.count()} students")
        db.session.remove()

def run_benchmark():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    # use in memory sqlite for simplicity of benchmark if possible,
    # but the app uses postgres. Let's try sqlite for benchmarking if it works
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    setup_data(app)

    with app.app_context():
        # Login the user by using test_client context
        with app.test_client() as client:
            client.post('/login', data={'username': 'admin_test', 'password': 'password'})

            print("Running benchmark...")
            start_time = time.time()

            # Use testing client to make the actual request
            response = client.post('/finance/invoice/generate-monthly?limit=1000&offset=0')

            end_time = time.time()

            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                print(f"Response: {response.get_json()}")
            else:
                print(f"Error Response: {response.data}")

            duration = end_time - start_time
            print(f"Time taken: {duration:.4f} seconds")

if __name__ == '__main__':
    run_benchmark()
