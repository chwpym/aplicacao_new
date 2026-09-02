import sys
import os
import json

# Adiciona o diretório raiz ao sys.path para permitir importações do app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.models import Provedor

def register_autafastar():
    db = SessionLocal()
    try:
        # Verifica se já existe
        existing = db.query(Provedor).filter(Provedor.slug == "autafastar").first()
        if existing:
            print("Provedor Autafastar já cadastrado. Atualizando dados...")
            existing.nome = "AUTAFASTAR"
            existing.tipo = "autafastar"
            existing.url = "https://www.autafastar.com.br/"
            db.commit()
            print("Provedor Autafastar atualizado com sucesso!")
            return

        autafastar = Provedor(
            nome="AUTAFASTAR",
            slug="autafastar",
            url="https://www.autafastar.com.br/",
            tipo="autafastar",
            ativo=True,
            headers=json.dumps({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"
            }),
            mapeamento=json.dumps({
                "description": "Busca via Web Scraping no catálogo Autafastar com Hydration de Referências e Ficha Técnica"
            })
        )
        
        db.add(autafastar)
        db.commit()
        print("Provedor Autafastar cadastrado com sucesso no banco de dados!")
    except Exception as e:
        print(f"Erro ao cadastrar Autafastar: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    register_autafastar()
