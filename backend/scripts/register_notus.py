import sys
import os
import json

# Adiciona o diretório raiz ao sys.path para permitir importações do app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.models import Provedor

def register_notus():
    db = SessionLocal()
    try:
        # Verifica se já existe
        existing = db.query(Provedor).filter(Provedor.slug == "notus").first()
        if existing:
            print("Provedor Notus já cadastrado.")
            return

        notus = Provedor(
            nome="NOTUS",
            slug="notus",
            url="https://catalogo.notus.ind.br/",
            tipo="notus",
            ativo=True,
            headers=json.dumps({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"
            }),
            mapeamento=json.dumps({
                "description": "Busca via JSON estático da Notus do Brasil"
            })
        )
        
        db.add(notus)
        db.commit()
        print("Provedor Notus cadastrado com sucesso no banco de dados!")
    except Exception as e:
        print(f"Erro ao cadastrar Notus: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    register_notus()
