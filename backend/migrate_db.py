"""给现有 SQLite 数据库加 annotated_path 列"""
import sqlite3, os

db_path = os.path.join(os.path.dirname(__file__), 'backend', 'data.db')
conn = sqlite3.connect(db_path)
try:
    conn.execute('ALTER TABLE detect_records ADD COLUMN annotated_path VARCHAR(500)')
    conn.commit()
    print('迁移成功：已添加 annotated_path 列')
except sqlite3.OperationalError as e:
    if 'duplicate column' in str(e) or 'already exists' in str(e):
        print('列已存在，无需迁移')
    else:
        print(f'迁移失败: {e}')
finally:
    conn.close()
