import sqlite3
import os

# Caminho absoluto para o banco
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # backend/scripts/util
# Subir 2 níveis para chegar na pasta 'backend'
BACKEND_DIR = os.path.dirname(os.path.dirname(BASE_DIR)) 
DB_PATH = os.path.join(BACKEND_DIR, "catalogo.db")

print(f"Conectando em: {DB_PATH}")

def add_multiqualita():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Verifica se já existe
    cursor.execute("SELECT id FROM provedores WHERE tipo = 'multiqualita'")
    if cursor.fetchone():
        print("Provedor Multiqualita já existe.")
        conn.close()
        return

    # Insere o provedor
    cursor.execute("""
        INSERT INTO provedores (nome, url, tipo, ativo, headers, mapeamento, login_required)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        "MULTIQUALITÀ", 
        "https://multiqualita.com.br/", 
        "multiqualita", 
        1, 
        "{}", 
        "{}", 
        0
    ))
    
    conn.commit()
    print("Provedor Multiqualita adicionado com sucesso!")
    conn.close()

if __name__ == "__main__":
    add_multiqualita()
