import sqlite3
import os

db_path = r'd:\Dev\aplicacao_new\backend\catalogo.db'

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Searching for 'rho' in all columns of 'provedores':")
    cursor.execute("SELECT * FROM provedores")
    columns = [description[0] for description in cursor.description]
    rows = cursor.fetchall()
    
    found = False
    for row in rows:
        row_str = str(row).lower()
        if 'rho' in row_str:
            print(f"Found in row: {row}")
            found = True
            
    if not found:
        print("No mention of 'rho' found in the database.")
    
    conn.close()
