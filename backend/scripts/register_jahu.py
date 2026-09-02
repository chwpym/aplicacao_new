import sys
import os
import json

# Adiciona o diretório raiz ao sys.path para permitir importações do app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.models import Provedor

def registrar_jahu():
    """
    Cadastra o provedor JAHU no banco de dados local 'catalogo.db'.
    Isso possibilita que o factory de provedores (provider_factory.py) instancie
    o provedor correto ao receber buscas do usuário.
    """
    db = SessionLocal()
    try:
        # Verifica se o provedor já existe pelo slug único
        existing = db.query(Provedor).filter(Provedor.slug == "jahu").first()
        if existing:
            print("Provedor JAHU já está cadastrado no banco de dados.")
            return

        # Instancia o novo provedor
        jahu = Provedor(
            nome="JAHU",
            slug="jahu",
            url="https://b2b.jahu.com.br/",
            tipo="jahu",
            ativo=True,
            headers=json.dumps({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
            }),
            mapeamento=json.dumps({
                "description": "Busca direta via API pública do e-commerce B2B da Jahu Borrachas"
            })
        )
        
        # Adiciona e comita no banco SQLite
        db.add(jahu)
        db.commit()
        print("Provedor JAHU cadastrado com sucesso no banco de dados!")
    except Exception as e:
        print(f"Erro ao cadastrar JAHU: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    registrar_jahu()
