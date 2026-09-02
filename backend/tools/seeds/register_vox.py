import sqlite3

db_path = "backend/catalogo.db"


def register_vox():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if already exists
    cursor.execute("SELECT id FROM provedores WHERE nome = 'VOX'")
    res = cursor.fetchone()
    if res:
        print("VOX já está registrado no banco de dados!")
    else:
        cursor.execute(
            """
            INSERT INTO provedores (nome, url, tipo, ativo) 
            VALUES (?, ?, ?, ?)
        """,
            (
                "VOX",
                "https://www.filtrosvox.com.br/VoxCatalogo",
                "vox",
                1,
            ),
        )

        conn.commit()
        print("VOX registrado com sucesso no banco de dados!")

    conn.close()


if __name__ == "__main__":
    register_vox()
