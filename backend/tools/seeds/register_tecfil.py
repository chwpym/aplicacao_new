import sqlite3
import json

db_path = "backend/catalogo.db"


def register_tecfil():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if already exists
    cursor.execute("SELECT id FROM provedores WHERE nome = 'TECFIL'")
    res = cursor.fetchone()
    if res:
        print("TECFIL já está registrado no banco de dados!")
    else:
        cursor.execute(
            """
            INSERT INTO provedores (nome, url, tipo, ativo) 
            VALUES (?, ?, ?, ?)
        """,
            (
                "TECFIL",
                "https://tecfil-catalago.gruposofape.com.br/CatalogoTecfil",
                "tecfil",
                1,
            ),
        )

        conn.commit()
        print("TECFIL registrado com sucesso no banco de dados!")

    conn.close()


if __name__ == "__main__":
    register_tecfil()
