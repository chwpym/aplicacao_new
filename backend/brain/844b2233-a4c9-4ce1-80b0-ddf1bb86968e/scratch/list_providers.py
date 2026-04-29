import sqlite3
import os

db_path = r'd:\Dev\aplicacao_new\backend\catalogo.db'

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Listing all providers:")
    cursor.execute("SELECT id, nome, tipo, slug FROM provedores")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    
    conn.close()
