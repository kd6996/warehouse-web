from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_required, current_user
from werkzeug.security import generate_password_hash
from models import db, User, Product, Transaction
from auth import auth_bp
from datetime import datetime, timedelta
from sqlalchemy import inspect
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'replace_this_secret!'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
app.register_blueprint(auth_bp, url_prefix='/auth')

login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(uid):
    return User.query.get(int(uid))

with app.app_context():
    db.create_all()

    # ✅ Kiểm tra nếu chưa có cột location thì tự thêm
    inspector = inspect(db.engine)
    columns = [col["name"] for col in inspector.get_columns("product")]
    if "location" not in columns:
        try:
            db.session.execute('ALTER TABLE product ADD COLUMN location VARCHAR(120);')
            db.session.commit()
        except Exception:
            db.session.rollback()

    # ✅ Tạo user mặc định
    if not User.query.filter_by(username='admin').first():
        db.session.add(User(username='admin', password_hash=generate_password_hash('123456'), role='admin'))
    if not User.query.filter_by(username='staff').first():
        db.session.add(User(username='staff', password_hash=generate_password_hash('123456'), role='staff'))
    db.session.commit()

@app.route('/')
@login_required
def index():
    q = request.args.get('q', '')
    prods = Product.query.filter(
        (Product.code.contains(q)) |
        (Product.name.contains(q)) |
        (Product.location.contains(q))
    ).all()
    return render_template('index.html', products=prods, q=q)

@app.route('/add', methods=['POST'])
@login_required
def add():
    code = request.form['code']
    name = request.form['name']
    location = request.form['location']
    if Product.query.filter_by(code=code).first():
        flash('Mã SP đã tồn tại')
    else:
        db.session.add(Product(code=code, name=name, location=location))
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/edit/<int:id>', methods=['POST'])
@login_required
def edit(id):
    if current_user.role != 'admin':
        flash("Bạn không có quyền chỉnh sửa sản phẩm.")
        return redirect(url_for('index'))
    p = Product.query.get_or_404(id)
    p.code = request.form['code']
    p.name = request.form['name']
    p.location = request.form['location']
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
@login_required
def delete(id):
    if current_user.role != 'admin':
        flash("Bạn không có quyền xoá sản phẩm.")
        return redirect(url_for('index'))
    db.session.delete(Product.query.get_or_404(id))
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/import/<int:id>', methods=['POST'])
@login_required
def imp(id):
    p = Product.query.get_or_404(id)
    x = int(request.form['qty'])
    p.quantity += x
    db.session.add(Transaction(product_id=id, type='import', qty=x))
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/export/<int:id>', methods=['POST'])
@login_required
def exp(id):
    p = Product.query.get_or_404(id)
    x = int(request.form['qty'])
    if p.quantity >= x:
        p.quantity -= x
        db.session.add(Transaction(product_id=id, type='export', qty=x))
        db.session.commit()
    else:
        flash('Không đủ hàng')
    return redirect(url_for('index'))

@app.route('/history')
@login_required
def history():
    logs = Transaction.query.order_by(Transaction.time.desc()).limit(100).all()
    return render_template('history.html', logs=logs)

@app.route('/history/import')
@login_required
def history_import():
    logs = Transaction.query.filter_by(type='import').order_by(Transaction.time.desc()).all()
    return render_template('history.html', logs=logs, filter_type="import")

@app.route('/history/export')
@login_required
def history_export():
    logs = Transaction.query.filter_by(type='export').order_by(Transaction.time.desc()).all()
    return render_template('history.html', logs=logs, filter_type="export")

if __name__ == '__main__':
    app.run(debug=True)

