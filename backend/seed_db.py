import sqlite3
import json

def seed():
    conn = sqlite3.connect('d:/Dev/aplicacao_new/backend/base_dados.db')
    cursor = conn.cursor()

    # Provedores base
    provedores = [
        (
            'SABÓ', 
            'https://bff.catalogofraga.com.br/gateway/graphql', 
            'graphql', 
            True, 
            json.dumps({"Origin": "https://catalogo.sabo.com.br", "Referer": "https://catalogo.sabo.com.br/"}),
            '''query getProduct($id: ID!, $market: String!) {
  product(id: $id, market: $market) {
    id
    partNumber
    vehicles {
      brand
      name
      model
      engineName
      engineConfiguration
      startYear
      endYear
      note
      only
      restriction
    }
    images {
      imageUrl
    }
  }
}'''
        ),
        (
            'AUTHOMIX', 
            'https://bff.catalogofraga.com.br/gateway/graphql', 
            'graphql', 
            True, 
            json.dumps({"Origin": "https://catalogo.authomix.com.br", "Referer": "https://catalogo.authomix.com.br/"}),
            '''query getProduct($id: ID!, $market: String!) {
  product(id: $id, market: $market) {
    id
    partNumber
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
  }
}'''
        )
    ]

    for p in provedores:
        cursor.execute('''
            INSERT INTO provedores (nome, url, tipo, ativo, headers, query)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', p)

    conn.commit()
    conn.close()
    print("Seed finalizado!")

if __name__ == "__main__":
    seed()
