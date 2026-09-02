import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Configurar PYTHONPATH para importar o app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.database import SQLALCHEMY_DATABASE_URL
from app.models import models

def debug_db():
    print(f"CWD atual: {os.getcwd()}")
    print(f"URL do Banco configurada: {SQLALCHEMY_DATABASE_URL}")
    
    # Tenta descobrir o path absoluto que o SQLAlchemy está usando
    if SQLALCHEMY_DATABASE_URL.startswith("sqlite:///"):
        rel_path = SQLALCHEMY_DATABASE_URL.replace("sqlite:///", "")
        abs_path = os.path.abspath(rel_path)
        print(f"Path Absoluto Calculado: {abs_path}")
        
        if os.path.exists(abs_path):
            print(f"O arquivo EXISTE e tem {os.path.getsize(abs_path)} bytes.")
            
            # Listar marcas
            engine = create_engine(SQLALCHEMY_DATABASE_URL)
            Session = sessionmaker(bind=engine)
            db = Session()
            try:
                marcas = [p.nome for p in db.query(models.Provedor).all()]
                print(f"Marcas encontradas ({len(marcas)}): {marcas}")
            except Exception as e:
                print(f"Erro ao ler marcas: {e}")
            finally:
                db.close()
        else:
            print("O arquivo NÃO EXISTE neste path.")

if __name__ == "__main__":
    debug_db()
