import sqlite3
import json

conn = sqlite3.connect('d:\\Dev\\aplicacao_new\\backend\\catalogo.db')
cursor = conn.cursor()

cursor.execute("SELECT id, nome, tipo, url, query, mapeamento FROM provedores WHERE nome LIKE '%Wega%'")
row = cursor.fetchone()

if row:
    id_p, nome, tipo, url, query, mapeamento = row
    print("=== WEGA CONFIG ===")
    print(f"ID: {id_p}")
    print(f"Nome: {nome}")
    print(f"Tipo: {tipo}")
    print(f"URL: {url}")
    print(f"Query: {query}")
    print("\n--- MAPEAMENTO ---")
    try:
        map_json = json.loads(mapeamento)
        print(json.dumps(map_json, indent=2))
    except:
        print(mapeamento)
else:
    print("Provedor Wega não encontrado.")

conn.close()
