import sqlite3
import json
import os


def seed_cofap():
    db_path = r"d:\Dev\aplicacao_new\backend\catalogo.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Parâmetros otimizados
    nome = "COFAP (Fraga)"
    tipo = "cofap"
    url = "https://bff.catalogofraga.com.br/gateway/graphql"
    headers = {
        "Origin": "https://cofap.catalogofraga.com.br",
        "Referer": "https://cofap.catalogofraga.com.br/",
    }

    query = """query getProduct($id: String!, $market: MarketType!) {
  product(id: $id, market: $market) {
    id
    partNumber
    crossReferences {
      brand { name }
      partNumber
    }
    vehicles {
      brand
      name
      model
      engineName
      engineConfiguration
      startYear
      endYear
      note
    }
    images {
      imageUrl
    }
  }
}"""

    mapeamento = {
        "marca": "brand",
        "veiculo": "name",
        "motor": "engineName",
        "ano_inicio": "startYear",
        "imagem": "images",
    }

    # Credenciais anteriores (ajustar se necessário)
    username = "original.garantialins@gmail.com"
    password = (
        " Or!ginal1080"  # Mantendo o espaço conforme visto no banco anteriormente
    )

    try:
        # Verifica se já existe (slug ou nome similar) para evitar duplicatas acidentais
        cursor.execute("SELECT id FROM provedores WHERE nome = ?", (nome,))
        if cursor.fetchone():
            print(f"Provider '{nome}' already exists.")
            return

        cursor.execute(
            """
            INSERT INTO provedores 
            (nome, slug, url, tipo, ativo, headers, query, login_required, username, password, mapeamento)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                nome,
                "cofap-fraga",
                url,
                tipo,
                True,
                json.dumps(headers, indent=2),
                query,
                True,
                username,
                password,
                json.dumps(mapeamento, indent=2),
            ),
        )

        conn.commit()
        print(f"Provider '{nome}' successfully restored with ID: {cursor.lastrowid}")

    except Exception as e:
        print(f"Error seeding COFAP: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    seed_cofap()
