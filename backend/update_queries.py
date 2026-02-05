import sqlite3

conn = sqlite3.connect('d:/Dev/aplicacao_new/backend/catalogo.db')
cursor = conn.cursor()

new_query = '''query getProduct($id: String!, $market: MarketType!) {
  product(id: $id, market: $market) {
    id
    partNumber
    crossReferences {
      brand {
        name
      }
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
      only
      restriction
    }
    images {
      imageUrl
    }
  }
}'''

cursor.execute("UPDATE provedores SET query = ? WHERE tipo = 'graphql'", (new_query,))
conn.commit()
conn.close()
print("Query GraphQL atualizada com sucesso para todos os provedores Fraga.")
