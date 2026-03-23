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
    
    # Atualiza mapeamento de colunas para usar os campos corretos que o usuário mostrou
    map_config["mapeamento"] = {
         "marca": "Montadora",
         "veiculo": "Modelo",
         "modelo": "Descrição do Modelo",
         "motor": "Motor",
         "configuracao_motor": "Pos_Montagem",
         "ano_inicio": "Ano"
    }
    
    # Se o mapeamento ja estiver no root (como vimos no inspect), apenas atualiza as chaves
    map_config["marca"] = "Montadora"
    map_config["veiculo"] = "Modelo"
    map_config["modelo"] = "Descrição do Modelo"
    map_config["motor"] = "Motor"
    map_config["configuracao_motor"] = "Pos_Montagem"
    map_config["ano_inicio"] = "Ano"
    map_config["ano_fim"] = "Ano" # Wega tem só uma coluna Ano
    
    nuevo_mapeamento = json.dumps(map_config, ensure_ascii=False)
    
    cursor.execute("UPDATE provedores SET mapeamento = ? WHERE id = 34", (nuevo_mapeamento,))
    conn.commit()
    print("Mapeamento de colunas da Wega atualizado com sucesso!")
else:
    print("Mapeamento da Wega não encontrado.")

conn.close()
