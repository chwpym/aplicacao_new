from pydantic import BaseModel
from typing import Optional, List


# --- Provedores ---
class ProvedorBase(BaseModel):
    nome: str
    url: str
    tipo: str
    ativo: bool = True
    headers: Optional[str] = None
    query: Optional[str] = None
    login_required: Optional[bool] = False
    username: Optional[str] = None
    password: Optional[str] = None
    url_login: Optional[str] = None
    pasta_pdf: Optional[str] = None
    mapeamento: Optional[str] = None


class ProvedorCreate(ProvedorBase):
    pass


class Provedor(ProvedorBase):
    id: int

    class Config:
        from_attributes = True


# --- Siglas ---
class SiglaBase(BaseModel):
    nome_completo: str
    abreviacao: str
    campo: str = "marca"


class SiglaCreate(SiglaBase):
    pass


class Sigla(SiglaBase):
    id: int

    class Config:
        from_attributes = True


# --- Palavras Remover ---
class PalavraRemoverBase(BaseModel):
    palavra: str
    campo: str


class PalavraRemoverCreate(PalavraRemoverBase):
    pass


class PalavraRemover(PalavraRemoverBase):
    id: int

    class Config:
        from_attributes = True


# --- Busca ---
class SearchResult(BaseModel):
    marca: str
    veiculo: str
    modelo: str
    versao: Optional[str] = None
    motor: str
    configuracao_motor: Optional[str]
    sistema_freio: Optional[str] = None
    combustivel: Optional[str] = None
    ano_inicio: Optional[str] = None
    ano_fim: Optional[str] = None
    observacao: Optional[str] = None
    apenas: Optional[str] = None
    restricao: Optional[str] = None
    posicao: Optional[str] = None
    lado: Optional[str] = None
    direcao: Optional[str] = None
    imagem: Optional[str] = None
    imagens: Optional[List[str]] = []
    referencias: Optional[str] = None
    ficha_tecnica: Optional[dict] = None
    metadados: Optional[dict] = None
    provider_id: Optional[int] = None
    provedor: Optional[str] = None
    codigo: Optional[str] = None
    raw_response: Optional[str] = None


class TestSearchRequest(BaseModel):
    id_peca: str
    config: ProvedorBase
