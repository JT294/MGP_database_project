import os
import pandas as pd
from sqlalchemy import create_engine
from concurrent.futures import ThreadPoolExecutor
import threading

# 创建数据库连接锁
db_lock = threading.Lock()

def read_file(file_path):
    # 尝试使用不同的编码读取文件
    encodings = ['utf-8', 'latin1', 'ISO-8859-1']
    for encoding in encodings:
        try:
            if file_path.endswith('.csv'):
                return pd.read_csv(file_path, encoding=encoding)
            elif file_path.endswith('.xlsx'):
                return pd.read_excel(file_path)
        except (UnicodeDecodeError, pd.errors.ParserError):
            continue
    raise UnicodeDecodeError(f"Cannot decode file: {file_path}")

def process_folder(folder_path, db_path, folder_name):
    engine = create_engine(f'sqlite:///{db_path}', connect_args={'timeout': 30})

    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith('.csv') or file.endswith('.xlsx'):
                try:
                    df = read_file(file_path)
                except (UnicodeDecodeError, pd.errors.ParserError):
                    print(f"Failed to decode or parse file: {file_path}")
                    continue

                # 将大整数转换为字符串
                for col in df.select_dtypes(include=['int']):
                    if (df[col].max() > 9223372036854775807) or (df[col].min() < -9223372036854775808):
                        df[col] = df[col].astype(str)

                table_name = f'{folder_name}_{os.path.splitext(file)[0]}'

                try:
                    with db_lock:
                        df.to_sql(table_name, engine, if_exists='replace', index=False)
                        print(f'Stored {file_path} to table {table_name}')
                except Exception as e:
                    print(f"Failed to store file {file_path} to database: {e}")

def main(base_folder_path, db_path):
    subfolders = [f.path for f in os.scandir(base_folder_path) if f.is_dir()]

    with ThreadPoolExecutor() as executor:
        futures = []
        for subfolder in subfolders:
            folder_name = os.path.basename(subfolder)
            futures.append(executor.submit(process_folder, subfolder, db_path, folder_name))

        for future in futures:
            future.result()

if __name__ == "__main__":
    base_folder_path = 'Categorized Investor Data'  
    db_path = 'database\mgp_database.db'  
    
    main(base_folder_path, db_path)