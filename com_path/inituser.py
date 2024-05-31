import sqlite3
import os
from werkzeug.security import generate_password_hash

DATABASE = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database', 'mgp_database.db')

def init_user_table():
    # 连接数据库
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # 创建用户表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        permissions TEXT NOT NULL
    )
    ''')

    # 插入默认用户
    users = [
        ('admin', 'password', 'Crypto,Hedge funds'),
        ('user1', 'user1pass', 'Crypto'),
        ('user2', 'user2pass', 'Hedge funds'),
    ]

    for username, password, permissions in users:
        try:
            password_hash = generate_password_hash(password)
            cursor.execute('INSERT INTO users (username, password_hash, permissions) VALUES (?, ?, ?)', (username, password_hash, permissions))
            print(f"Inserted user -> Username: {username}, Password: {password}, Permissions: {permissions}")
        except sqlite3.IntegrityError:
            print(f"User {username} already exists. Skipping insertion.")

    # 提交更改并关闭连接
    conn.commit()
    conn.close()

# 运行初始化函数
if __name__ == '__main__':
    init_user_table()