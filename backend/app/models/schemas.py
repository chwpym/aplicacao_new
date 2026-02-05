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
        orm_mode = True

# --- Busca ---
class SearchResult(BaseModel):
    marca: str
    veiculo: str
    modelo: str
    motor: str
    configuracao_motor: Optional[str]
    sistema_freio: Optional[str]
    ano_inicio: Optional[str]
    ano_fim: Optional[str]
    observacao: Optional[str]
    apenas: Optional[str] = None
    restricao: Optional[str] = None
    posicao: Optional[str] = None
    lado: Optional[str] = None
    direcao: Optional[str] = None
    imagem: Optional[str]
    imagens: Optional[List[str]] = []
    referencias: Optional[str] # Números originais/similares
    raw_response: Optional[str] = None # Para depuração no Playground

class TestSearchRequest(BaseModel):
    id_peca: str
    config: ProvedorBase
