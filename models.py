from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='staff')

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(100))
    quantity = db.Column(db.Integer, default=0)
    location = db.Column(db.String(120), default='')  # 👈 dòng này rất quan trọng


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    type = db.Column(db.String(20))  # 'import' or 'export'
    qty = db.Column(db.Integer)
    time = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship('Product')

