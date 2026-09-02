import sys
import os
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Tenta importar do app (precisa do PYTHONPATH configurado)
try:
    from app.database import Base
    from app.models import models
except ImportError:
    print("Erro ao importar modelos. Certifique-se de que o PYTHONPATH está correto.")
    sys.exit(1)

def seed_db(db_path):
    print(f"\nProcessando banco: {db_path}")
    abs_path = os.path.abspath(db_path)
    if not os.path.exists(os.path.dirname(abs_path)):
        print(f"Diretório não existe: {os.path.dirname(abs_path)}")
        return

    engine = create_engine(f"sqlite:///{abs_path}")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Cria tabelas se não existirem
    models.Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 1. Desativar o 'TUBA' antigo (se existir com slug 'tuba')
        tuba_antigo = db.query(models.Provedor).filter(models.Provedor.slug == "tuba").first()
        if tuba_antigo:
            print("Desativando TUBA antigo...")
            tuba_antigo.ativo = False
            tuba_antigo.nome = "TUBA (OBSOLETO)"
        
        # 2. Cadastrar/Atualizar as novas marcas
        marcas = [
            {"nome": "TUBA CABOS", "slug": "tubacabos", "brand_slug": "tubacabos", "url": "https://buscanarede.com.br/tubacabos"},
            {"nome": "SAMPEL", "slug": "sampel", "brand_slug": "sAMPEL", "url": "https://buscanarede.com.br/sAMPEL"},
            {"nome": "TC CHICOTES", "slug": "tcchicotes", "brand_slug": "tcchicotes", "url": "https://buscanarede.com.br/tcchicotes"}
        ]

        for m in marcas:
            db_m = db.query(models.Provedor).filter(models.Provedor.slug == m["slug"]).first()
            mapeamento = json.dumps({"brand_slug": m["brand_slug"]})
            
            if db_m:
                print(f"Atualizando {m['nome']}...")
                db_m.nome = m["nome"]
                db_m.url = m["url"]
                db_m.tipo = "busca_na_rede"
                db_m.mapeamento = mapeamento
                db_m.ativo = True
            else:
                print(f"Criando {m['nome']}...")
                db_m = models.Provedor(
                    nome=m["nome"], slug=m["slug"], url=m["url"],
                    tipo="busca_na_rede", mapeamento=mapeamento, ativo=True
                )
                db.add(db_m)
        
        db.commit()
        print(f"Sucesso para {db_path}")
    except Exception as e:
        print(f"Erro no banco {db_path}: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # Aplica nos dois locais possíveis
    bancos = ["catalogo.db", "backend/catalogo.db"]
    for b in bancos:
        seed_db(b)
