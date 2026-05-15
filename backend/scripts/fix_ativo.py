import sqlite3
conn = sqlite3.connect('catalogo.db')
c = conn.cursor()
c.execute("UPDATE provedores SET ativo = 1 WHERE ativo IS NULL")
print(f"Atualizados: {c.rowcount}")
conn.commit()
conn.close()
