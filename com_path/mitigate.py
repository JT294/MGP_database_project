import os
import sqlite3
import mysql.connector

# SQLite数据库路径
sqlite_db =  os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database', 'mgp_database.db')
# MySQL数据库连接配置
mysql_config = {
    'host': 'JT294.mysql.pythonanywhere-services.com',
    'user': 'JT294',
    'password': '225',
    'database': 'JT294$mgp_database'
}

# 连接SQLite数据库
sqlite_conn = sqlite3.connect(sqlite_db)
sqlite_cursor = sqlite_conn.cursor()

# 连接MySQL数据库
mysql_conn = mysql.connector.connect(**mysql_config)
mysql_cursor = mysql_conn.cursor()

# 获取SQLite数据库中的所有表
sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = sqlite_cursor.fetchall()

for table in tables:
    table_name = table[0]
    # 获取表的结构
    sqlite_cursor.execute(f"PRAGMA table_info({table_name});")
    columns = sqlite_cursor.fetchall()

    # 创建MySQL表
    column_defs = ", ".join([f"{col[1]} {col[2]}" for col in columns])
    create_table_query = f"CREATE TABLE {table_name} ({column_defs});"
    try:
        mysql_cursor.execute(create_table_query)
    except mysql.connector.errors.ProgrammingError:
        print(f"Table {table_name} already exists in MySQL, skipping creation.")
    
    # 获取SQLite表中的所有数据
    sqlite_cursor.execute(f"SELECT * FROM {table_name};")
    rows = sqlite_cursor.fetchall()

    # 插入数据到MySQL表
    column_names = ", ".join([col[1] for col in columns])
    placeholders = ", ".join(["%s" for _ in columns])
    insert_query = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders});"
    
    for row in rows:
        mysql_cursor.execute(insert_query, row)
    mysql_conn.commit()

# 关闭数据库连接
sqlite_conn.close()
mysql_conn.close()
