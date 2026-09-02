import sqlite3
import json

conn = sqlite3.connect('d:\\Dev\\aplicacao_new\\backend\\catalogo.db')
cursor = conn.connect().cursor() if hasattr(conn, 'connect') else conn.cursor()

cursor.execute("SELECT nome, mapeamento FROM provedores WHERE id = 34")
row = cursor.fetchone()

if row:
    print(f"Provedor: {row[0]}")
    print("Mapeamento atual:")
    print(json.dumps(json.loads(row[1]), indent=4, ensure_ascii=False))
else:
    print("Wega não encontrado.")

conn.close()
