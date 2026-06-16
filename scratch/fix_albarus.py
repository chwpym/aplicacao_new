import sqlite3

def main():
    db_path = "d:/Dev/aplicacao_new/backend/catalogo.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Corrige a URL (removendo o espaço inicial) e o JSON do header (adicionando as aspas em "referer" e padronizando as chaves)
    corrected_url = "https://bff.catalogofraga.com.br/gateway/graphql"
    corrected_headers = '{\n  "Origin": "https://albarus.catalogofraga.com.br",\n  "Referer": "https://albarus.catalogofraga.com.br/"\n}'
    
    cursor.execute(
        "UPDATE provedores SET url = ?, headers = ? WHERE id = 62",
        (corrected_url, corrected_headers)
    )
    
    conn.commit()
    conn.close()
    print("Sucesso: Provedor ALBARUS (ID 62) corrigido no SQLite local!")

if __name__ == "__main__":
    main()
