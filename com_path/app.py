import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, g
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 为了会话管理需要设置密钥
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database', 'mgp_database.db')

class User(UserMixin):
    def __init__(self, id, username, password_hash, permissions):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.permissions = permissions

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return User(id=user[0], username=user[1], password_hash=user[2], permissions=user[3])
    return None

def get_db():
    db = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user[2], password):
            user_obj = User(id=user[0], username=user[1], password_hash=user[2], permissions=user[3])
            login_user(user_obj)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'users';")
    tables = cursor.fetchall()
    prefixes = {}
    for (table,) in tables:
        prefix = table.split('_')[0]
        if prefix not in prefixes:
            prefixes[prefix] = []
        prefixes[prefix].append(table)
    
    # 根据用户权限过滤表
    user_prefixes = current_user.permissions.split(',')
    filtered_prefixes = {prefix: tables for prefix, tables in prefixes.items() if prefix in user_prefixes}
    
    return render_template('index.html', prefixes=filtered_prefixes)

@app.route('/files/<prefix>')
@login_required
def files(prefix):
    if prefix not in current_user.permissions.split(','):
        flash('You do not have access to this prefix', 'danger')
        return redirect(url_for('index'))
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ? AND name != 'users';", (prefix + '%',))
    tables = cursor.fetchall()
    return render_template('files.html', prefix=prefix, tables=tables)

@app.route('/table/<table_name>')
@login_required
def table(table_name):
    if table_name.split('_')[0] not in current_user.permissions.split(','):
        flash('You do not have access to this table', 'danger')
        return redirect(url_for('index'))
    
    db = get_db()
    cursor = db.cursor()
    query = f"SELECT * FROM `{table_name}`"
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.execute(f"PRAGMA table_info(`{table_name}`);")
    columns = [info[1] for info in cursor.fetchall()]
    return render_template('table.html', table_name=table_name, columns=columns, rows=rows)

if __name__ == '__main__':
    # 初始化数据库
    def init_db():
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            permissions TEXT NOT NULL
        )
        ''')
        # 插入默认用户
        try:
            default_username = 'admin'
            default_password = 'password'
            default_permissions = 'prefix1,prefix2'
            password_hash = generate_password_hash(default_password)
            cursor.execute('INSERT INTO users (username, password_hash, permissions) VALUES (?, ?, ?)', (default_username, password_hash, default_permissions))
            print(f"Default credentials -> Username: {default_username}, Password: {default_password}, Permissions: {default_permissions}")
        except sqlite3.IntegrityError:
            pass
        conn.commit()
        conn.close()

    init_db()

    app.run(debug=True)



