import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from app.database import SessionLocal
from app.models.models import Provedor

def run():
    db = SessionLocal()
    
    # 1. Definir query padrão do Fraga GraphQL
    query_padrao = """query getProduct($id: String!, $market: MarketType!) {
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

    # 2. Provedores a adicionar
    novos_provedores = [
        {
            "nome": "COBREQ",
            "slug": "cobreq",
            "url": "https://bff.catalogofraga.com.br/gateway/graphql",
            "tipo": "graphql",
            "ativo": True,
            "login_required": False,
            "headers": json.dumps({
                "origin": "https://catalogo.cobreq.com.br",
                "referer": "https://catalogo.cobreq.com.br/"
            }),
            "query": query_padrao,
            "mapeamento": "{}"
        },
        {
            "nome": "MONROE AXIOS",
            "slug": "axios",
            "url": "https://bff.catalogofraga.com.br/gateway/graphql",
            "tipo": "graphql",
            "ativo": True,
            "login_required": False,
            "headers": json.dumps({
                "origin": "https://axios.catalogofraga.com.br",
                "referer": "https://axios.catalogofraga.com.br/"
            }),
            "query": query_padrao,
            "mapeamento": "{}"
        }
    ]

    try:
        for info in novos_provedores:
            p_existente = db.query(Provedor).filter(Provedor.nome == info["nome"]).first()
            if p_existente:
                print(f"Provedor {info['nome']} já existe. Atualizando dados...")
                p_existente.url = info["url"]
                p_existente.tipo = info["tipo"]
                p_existente.ativo = info["ativo"]
                p_existente.headers = info["headers"]
                p_existente.query = info["query"]
                p_existente.slug = info["slug"]
            else:
                print(f"Criando novo provedor: {info['nome']}")
                novo_p = Provedor(
                    nome=info["nome"],
                    slug=info["slug"],
                    url=info["url"],
                    tipo=info["tipo"],
                    ativo=info["ativo"],
                    login_required=info["login_required"],
                    headers=info["headers"],
                    query=info["query"],
                    mapeamento=info["mapeamento"]
                )
                db.add(novo_p)
        db.commit()
        print("Provedores inseridos/atualizados com sucesso!")
        
        # Listar provedores atualizados
        provedores = db.query(Provedor).all()
        print("\n=== Lista Atualizada de Provedores ===")
        for p in sorted(provedores, key=lambda x: x.id):
            nome = p.nome or ""
            slug = p.slug or ""
            tipo = p.tipo or ""
            ativo = p.ativo if p.ativo is not None else False
            print(f"ID: {p.id:<3} | Nome: {nome:<25} | Slug: {slug:<12} | Tipo: {tipo:<10} | Ativo: {str(ativo)}")
            
    except Exception as e:
        db.rollback()
        print(f"Erro ao inserir provedores: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run()
