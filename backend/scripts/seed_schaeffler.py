import sqlite3
import os

# Caminho para o banco de dados
DB_PATH = os.path.join(os.getcwd(), 'catalogo.db')

def seed():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    marcas = [
        ('LUK', 'schaeffler', 'https://vehiclelifetimesolutions.schaeffler.com.br/pt-br/catalog'),
        ('FAG', 'schaeffler', 'https://vehiclelifetimesolutions.schaeffler.com.br/pt-br/catalog'),
        ('INA', 'schaeffler', 'https://vehiclelifetimesolutions.schaeffler.com.br/pt-br/catalog')
    ]

    for nome, tipo, url in marcas:
        # Verifica se já existe
        cursor.execute("SELECT id FROM provedores WHERE nome = ?", (nome,))
        if cursor.fetchone():
            print(f"Provedor {nome} já existe. Atualizando tipo...")
            cursor.execute("UPDATE provedores SET tipo = ?, url = ? WHERE nome = ?", (tipo, url, nome))
        else:
            print(f"Inserindo provedor {nome}...")
            cursor.execute("INSERT INTO provedores (nome, tipo, url, query, headers, login_required, ativo) VALUES (?, ?, ?, ?, ?, ?, ?)",
                         (nome, tipo, url, '', '{}', 0, 1))

    conn.commit()
    conn.close()
    print("Seed concluído com sucesso!")

if __name__ == "__main__":
    seed()
