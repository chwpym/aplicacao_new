import sqlite3
db_path = r'd:\Dev\aplicacao_new\backend\catalogo.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
sql = """
UPDATE provedores 
SET tipo = 'ima', 
    url = 'https://search-api.wedigi.house/api/ima/filters/items/search', 
    mapeamento = '{}', 
    headers = '{}' 
WHERE id = 22
"""
cursor.execute(sql)
conn.commit()
print(f"IMA (ID 22) atualizado. Rows affected: {cursor.rowcount}")
conn.close()
