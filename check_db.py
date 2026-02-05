import sqlite3
import os

db_path = r'd:\Dev\aplicacao_new\backend\catalogo.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, url, tipo FROM provedores")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    conn.close()
else:
    print(f"Database not found at {db_path}")
