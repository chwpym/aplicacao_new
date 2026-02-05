import sqlite3
import os

dbs = ['base_dados.db', 'catalogo.db']
for db_name in dbs:
    full_path = f"d:/Dev/aplicacao_new/backend/{db_name}"
    if os.path.exists(full_path):
        try:
            conn = sqlite3.connect(full_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"DB: {db_name} | Tabelas: {tables}")
            conn.close()
        except Exception as e:
            print(f"Erro ao ler {db_name}: {e}")
    else:
        print(f"Arquivo {db_name} não encontrado.")
