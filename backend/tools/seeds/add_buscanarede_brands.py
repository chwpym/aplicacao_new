import sys
import os
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import models

# Adiciona o diretório raiz ao path para poder importar o app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# Força o banco de dados oficial na pasta backend
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "catalogo.db"))
engine = create_engine(f"sqlite:///{DB_PATH}")
SessionLocalAlt = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def seed():
    # Garante que as tabelas existam no banco correto
    models.Base.metadata.create_all(bind=engine)
    
    db = SessionLocalAlt()



    try:
        marcas = [
            {
                "nome": "TUBA CABOS",
                "slug": "tubacabos",
                "url": "https://buscanarede.com.br/tubacabos",
                "brand_slug": "tubacabos"
            },
            {
                "nome": "SAMPEL",
                "slug": "sampel",
                "url": "https://buscanarede.com.br/sAMPEL",
                "brand_slug": "sAMPEL"
            },
            {
                "nome": "TC CHICOTES",
                "slug": "tcchicotes",
                "url": "https://buscanarede.com.br/tcchicotes",
                "brand_slug": "tcchicotes"
            }
        ]

        for marca in marcas:
            # Verifica se já existe
            db_provedor = db.query(models.Provedor).filter(models.Provedor.slug == marca["slug"]).first()
            
            mapeamento = json.dumps({"brand_slug": marca["brand_slug"]})
            
            if db_provedor:
                print(f"Atualizando {marca['nome']}...")
                db_provedor.nome = marca["nome"]
                db_provedor.url = marca["url"]
                db_provedor.tipo = "busca_na_rede"
                db_provedor.mapeamento = mapeamento
            else:
                print(f"Criando {marca['nome']}...")
                db_provedor = models.Provedor(
                    nome=marca["nome"],
                    slug=marca["slug"],
                    url=marca["url"],
                    tipo="busca_na_rede",
                    mapeamento=mapeamento,
                    ativo=True
                )
                db.add(db_provedor)
        
        db.commit()
        print("Marcas Busca na Rede cadastradas com sucesso!")
        
    except Exception as e:
        print(f"Erro ao cadastrar marcas: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
