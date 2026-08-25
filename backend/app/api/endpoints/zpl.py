from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/zpl", tags=["ZPL"])

class ZPLRequest(BaseModel):
    template: str
    titulo: str = "ORIGINAL AUTO PECAS"
    codigo: str = ""
    codigo_secundario: str = ""
    linha1: str = ""
    linha2: str = ""
    linha3: str = ""
    linha4: str = ""
    linha5: str = ""
    rotacionar: bool = False

def gerar_etiqueta_dupla(req: ZPLRequest) -> str:
    # Ajuste fino para os eixos Y
    zpl = "^XA\n^LH0,0^FS\n^PRA^FS\n^MTD^FS\n^PQ  1^FS\n"
    
    # Eixo X Esq = 040 / 060 / 080
    # Eixo X Dir = 455 / 475 / 495
    # (offset de ~415 na direita)
    
    # LADO ESQUERDO
    zpl += f"^FO060,005,^ABN,010,015^FD{req.titulo}^FS\n"
    zpl += f"^FO040,030,^ACN,010,010^FD{req.codigo}^FS\n"
    zpl += f"^FO280,030,^ACN,010,010^FD{req.codigo_secundario}^FS\n"
    zpl += f"^FO040,060,^ACN,010,010^FD{req.linha1}^FS\n"
    zpl += f"^FO040,080,^ACN,010,010^FD{req.linha2}^FS\n"
    zpl += f"^FO040,115,^ACN,010,010^FD{req.linha3}^FS\n"
    zpl += f"^FO040,135,^ACN,010,010^FD{req.linha4}^FS\n"
    zpl += f"^FO040,155,^ACN,010,010^FD{req.linha5}^FS\n"
    
    # LADO DIREITO
    zpl += f"^FO475,005,^ABN,010,015^FD{req.titulo}^FS\n"
    zpl += f"^FO455,030,^ACN,010,010^FD{req.codigo}^FS\n"
    zpl += f"^FO695,030,^ACN,010,010^FD{req.codigo_secundario}^FS\n"
    zpl += f"^FO455,060,^ACN,010,010^FD{req.linha1}^FS\n"
    zpl += f"^FO455,080,^ACN,010,010^FD{req.linha2}^FS\n"
    zpl += f"^FO455,115,^ACN,010,010^FD{req.linha3}^FS\n"
    zpl += f"^FO455,135,^ACN,010,010^FD{req.linha4}^FS\n"
    zpl += f"^FO455,155,^ACN,010,010^FD{req.linha5}^FS\n"
    
    zpl += "^XZ"
    return zpl

def gerar_etiqueta_rotacionada(req: ZPLRequest) -> str:
    # Exemplo: Rotacionada, como o usuário enviou
    zpl = "^XA\n^PW399\n^LL240\n"
    zpl += f"^FO250,20\n^A0R,80,80\n^FD{req.linha1}^FS\n"
    zpl += f"^FO80,20\n^A0R,80,80\n^FD{req.linha2}^FS\n"
    zpl += "^XZ"
    return zpl

@router.post("/generate")
async def generate_zpl(request: ZPLRequest):
    try:
        if request.rotacionar:
            zpl_code = gerar_etiqueta_rotacionada(request)
        else:
            zpl_code = gerar_etiqueta_dupla(request)
        
        return {"zpl": zpl_code}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
