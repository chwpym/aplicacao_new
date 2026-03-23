import sqlite3
import json
import os


def check_cofap():
    db_path = r"d:\Dev\aplicacao_new\backend\catalogo.db"
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT * FROM provedores WHERE tipo = 'cofap' OR nome LIKE '%COFAP%'"
        )
        rows = cursor.fetchall()

        # Get column names
        cursor.execute("PRAGMA table_info(provedores)")
        cols = [c[1] for c in cursor.fetchall()]

        if not rows:
            print("No COFAP provider found in database.")
            return

        for row in rows:
            data = dict(zip(cols, row))
            print("-" * 50)
            print(f"Provider ID: {data['id']}")
            print(f"Name: {data['nome']}")
            print(f"Type: {data['tipo']}")
            print(f"URL: {data['url']}")
            print(f"Headers: {data['headers']}")
            print(
                f"Query: {data['query'][:100]}..." if data["query"] else "Query: None"
            )
            print(f"Mapping: {data['mapeamento']}")
            print(f"Ativo: {data['ativo']}")
            print("-" * 50)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    check_cofap()
