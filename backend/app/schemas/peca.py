from pydantic import BaseModel, Field
from typing import Optional, List

class PecaSchema(BaseModel):
    """
    Contrato de dados padronizado para representar uma aplicação de peça.
    Utilizado para validar a saída de todos os provedores de catálogo.
    """
    marca: str = Field(..., description="Marca da peça ou fabricante")
    veiculo: str = Field(..., description="Montadora (ex: FIAT, TOYOTA)")
    modelo: str = Field(..., description="Nome do veículo")
    versao: Optional[str] = Field(None, description="Versão específica ou motorização")
    motor: Optional[str] = Field(None, description="Cilindrada e válvulas (ex: 1.0 8V)")
    configuracao_motor: Optional[str] = Field(None, description="Detalhes técnicos do motor")
    combustivel: Optional[str] = Field(None, description="Tipo de combustível")
    ano_inicio: Optional[str] = Field(None, description="Ano inicial de aplicação")
    ano_fim: Optional[str] = Field(None, description="Ano final (vazio se em produção)")
    observacao: Optional[str] = Field(None, description="Observações gerais")
    posicao: Optional[str] = Field(None, description="Local de instalação (ex: Dianteiro)")
    lado: Optional[str] = Field(None, description="Lado (ex: Esquerdo)")
    direcao: Optional[str] = Field(None, description="Tipo de direção")
    sistema_freio: Optional[str] = Field(None, description="Fabricante ou tipo de freio")
    restricao: Optional[str] = Field(None, description="Restrições de aplicação")
    apenas: Optional[str] = Field(None, description="Destaque de aplicação exclusiva")
    imagem: Optional[str] = Field(None, description="URL da imagem principal")
    imagens: List[str] = Field(default_factory=list, description="Lista de URLs de imagens")
    referencias: Optional[str] = Field(None, description="String crua de referências OE/Similares")
    ficha_tecnica: Optional[dict] = Field(None, description="Atributos técnicos detalhados")
    provider_id: Optional[int] = Field(None, description="ID do provedor no banco")
    provedor: Optional[str] = Field(None, description="Nome do provedor")
    codigo: Optional[str] = Field(None, description="Código original da peça no catálogo")

    class Config:
        from_attributes = True
        extra = "allow" # Permite campos extras sem quebrar o sistema (flexibilidade SaaS)
