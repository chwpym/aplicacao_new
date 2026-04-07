import sqlite3
import json
import os

db_path = r'd:\Dev\aplicacao_new\backend\catalogo.db'
if not os.path.exists(db_path):
    print(f"Erro: Banco de dados não encontrado em {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT id, nome, tipo, url, mapeamento FROM provedores WHERE nome LIKE '%IMA%'")
rows = cursor.fetchall()
params = ['id', 'nome', 'tipo', 'url', 'mapeamento']
result = [dict(zip(params, row)) for row in rows]
print(json.dumps(result, indent=2))
conn.close()
