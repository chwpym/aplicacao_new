import sqlite3
import json

conn = sqlite3.connect('d:\\Dev\\aplicacao_new\\backend\\catalogo.db')
cursor = conn.cursor()

# Busca mapeamento atual
cursor.execute("SELECT mapeamento FROM provedores WHERE id = 34")
row = cursor.fetchone()

if row:
    mapeamento_str = row[0]
    map_config = json.loads(mapeamento_str)
    
    # Atualiza o image_pattern
    map_config["image_pattern"] = "https://www.wegamotors.com/assets/images/{id}.jpg"
    
    nuevo_mapeamento = json.dumps(map_config, ensure_ascii=False)
    
    cursor.execute("UPDATE provedores SET mapeamento = ? WHERE id = 34", (nuevo_mapeamento,))
    conn.commit()
    print("Mapeamento da Wega atualizado com sucesso!")
else:
    print("Mapeamento da Wega não encontrado.")

conn.close()
