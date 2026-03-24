#!/usr/bin/env python
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app
from extensions import db
from models import User

app = create_app()

with app.app_context():
    users = User.query.order_by(User.id).all()
    for u in users:
        print(u.id, u.username, u.role)
