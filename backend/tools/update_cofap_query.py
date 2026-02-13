import sqlite3
import json


def update_cofap_query():
    db_path = r"backend\catalogo.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Query otimizada baseada no JSON fornecido pelo usuário
    query = """query getProduct($id: String!, $market: MarketType!) {
  product(id: $id, market: $market) {
    id
    partNumber
    images {
      imageUrl
      category
    }
    crossReferences {
      brand { name }
      partNumber
    }
    specifications {
      description
      value
    }
    vehicles {
      brand
      name
      startYear
      endYear
      note
      only
      restriction
    }
  }
}"""

    # Atualiza apenas o provedor COFAP (ID 38 ou pelo slug)
    cursor.execute(
        """
        UPDATE provedores 
        SET query = ? 
        WHERE slug = 'cofap-fraga'
    """,
        (query,),
    )

    conn.commit()
    print("COFAP query updated successfully.")
    conn.close()


if __name__ == "__main__":
    update_cofap_query()
