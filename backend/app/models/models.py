from sqlalchemy import Column, Integer, String, Boolean, Text
from app.database import Base


class Provedor(Base):
    __tablename__ = "provedores"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    slug = Column(String, unique=True, index=True)
    url = Column(String)
    tipo = Column(
        String
    )  # graphql, rest, ds, ate, pdf_local, viemar, schadek, iguacu, mte_thomson
    ativo = Column(Boolean, default=True)
    headers = Column(Text, nullable=True)  # JSON stringified
    query = Column(Text, nullable=True)
    login_required = Column(Boolean, default=False)
    username = Column(String, nullable=True)
    password = Column(String, nullable=True)
    url_login = Column(String, nullable=True)
    pasta_pdf = Column(String, nullable=True)  # Para pdf_local
    mapeamento = Column(
        Text, nullable=True
    )  # JSON com mapeamento de campos (REST) ou seletores (Scraper)


class Sigla(Base):
    __tablename__ = "siglas"

    id = Column(Integer, primary_key=True, index=True)
    nome_completo = Column(
        String, index=True
    )  # Removido unique pois pode haver a mesma sigla para campos diferentes
    abreviacao = Column(String)
    campo = Column(String, index=True, default="marca")  # marca, veiculo, modelo, etc.


class PalavraRemover(Base):
    __tablename__ = "palavras_remover"

    id = Column(Integer, primary_key=True, index=True)
    palavra = Column(String, index=True)
    campo = Column(String, index=True)  # marca, modelo, motor, etc.
