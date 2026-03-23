from app.database import engine, Base
from app.models.models import Provedor, Sigla, PalavraRemover

def init_db():
    print("Criando tabelas...")
    Base.metadata.create_all(bind=engine)
    print("Tabelas criadas com sucesso!")

if __name__ == "__main__":
    init_db()
