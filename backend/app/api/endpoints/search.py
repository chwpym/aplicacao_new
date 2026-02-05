from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services import search_service
from app.models import schemas
from typing import List

router = APIRouter(prefix="/search", tags=["Busca"])


@router.get("/{id_peca}", response_model=List[schemas.SearchResult])
async def buscar_peca(
    id_peca: str,
    provedores: str = None,
    agrupar: bool = True,
    db: Session = Depends(get_db),
):
    """
    Busca aplicações de uma peça em todos os provedores ativos (ou selecionados).
    """
    try:
        provedor_ids = [int(i) for i in provedores.split(",")] if provedores else None
        resultados = await search_service.buscar_em_todos(
            id_peca, db, provedor_ids, agrupar=agrupar
        )
        return resultados
    except Exception as e:
        print(f"ERRO NA BUSCA: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test", response_model=List[schemas.SearchResult])
async def testar_provedor(request: schemas.TestSearchRequest):
    """
    Testa uma configuração de provedor volátil (sem salvar no banco).
    """
    try:
        from app.providers import provider_factory

        # Simula um objeto de model para a factory
        class VolatileConfig:
            def __init__(self, d):
                self.id = 0
                self.nome = d.nome
                self.url = d.url
                self.tipo = d.tipo
                self.query = d.query
                self.headers = d.headers
                self.login_required = d.login_required
                self.username = d.username
                self.password = d.password
                self.mapeamento = d.mapeamento

        config_obj = VolatileConfig(request.config)
        provider = provider_factory.get_provider(config_obj)

        if not provider:
            raise HTTPException(
                status_code=400, detail="Tipo de provedor inválido ou não suportado."
            )

        resultados = await provider.buscar(request.id_peca)
        return resultados
    except Exception as e:
        print(f"ERRO NO TESTE: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/proxy/image")
async def proxy_image(url: str):
    """
    Proxy para download de imagens para evitar bloqueios de CORS no frontend.
    """
    try:
        import httpx
        from fastapi.responses import Response

        async with httpx.AsyncClient(timeout=10.0) as client:
            # Algumas URLs podem vir com ponto final por erro de digitação/parsing, removemos
            clean_url = url.strip().rstrip(".")

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = await client.get(
                clean_url, headers=headers, follow_redirects=True
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Falha ao buscar imagem externa",
                )

            return Response(
                content=response.content,
                media_type=response.headers.get("Content-Type", "image/jpeg"),
            )
    except Exception as e:
        print(f"Erro no proxy de imagem: {e}")
        raise HTTPException(status_code=500, detail=str(e))
