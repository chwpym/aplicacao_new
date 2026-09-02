from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services import search_service
from app.models import schemas
from typing import List

router = APIRouter(prefix="/search", tags=["Busca"])


@router.get("/proxy/image")
async def proxy_image(url: str):
    """
    Proxy para download de imagens para evitar bloqueios de CORS no frontend.
    """
    try:
        import httpx
        from fastapi.responses import Response

        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
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


@router.get("/download/image")
async def download_image(url: str, db: Session = Depends(get_db)):
    """
    Download processado de imagem (Aplicação do Pillow sob demanda).
    """
    try:
        from app.services.image_service import image_service
        # Baixa original
        content, _ = await image_service.download_image(url)
        if not content:
            raise HTTPException(status_code=404, detail="Falha ao baixar imagem do fornecedor")
        
        # Pega config
        from app.models import models
        config = db.query(models.ConfiguracaoImagem).first()
        if not config:
            config = models.ConfiguracaoImagem() # fallbacks
            
        # Processa
        processed_bytes, media_type = image_service.process_image(
            image_bytes=content,
            formato_saida=config.formato_saida,
            qualidade=config.qualidade,
            max_width=config.max_width,
            max_height=config.max_height,
            min_width=config.min_width,
            min_height=config.min_height,
            manter_proporcao=config.manter_proporcao,
            cor_fundo_jpg=config.cor_fundo_jpg
        )
        
        from fastapi.responses import Response
        # Retorna os bytes com nome sugerido no header
        headers = {
            "Content-Disposition": f"attachment; filename=imagem.{config.formato_saida.lower() if config.formato_saida != 'ORIGINAL' else 'jpg'}"
        }
        return Response(content=processed_bytes, media_type=media_type, headers=headers)
    except Exception as e:
        print(f"Erro no download processado: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/download/zip")
async def download_images_zip(
    urls: List[str],
    db: Session = Depends(get_db)
):
    """
    Download processado de múltiplas imagens em formato ZIP com limite de lote.
    """
    if len(urls) > 50:
        raise HTTPException(status_code=400, detail="Limite de lote excedido: Selecione no máximo 50 imagens por vez.")
        
    try:
        import io
        import zipfile
        from app.services.image_service import image_service
        from app.models import models
        from fastapi.responses import StreamingResponse
        
        config = db.query(models.ConfiguracaoImagem).first()
        if not config:
            config = models.ConfiguracaoImagem()

        zip_buffer = io.BytesIO()
        ssl_warning_occurred = False
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED, False) as zip_file:
            for idx, url in enumerate(urls):
                content, ssl_warn = await image_service.download_image(url)
                if ssl_warn:
                    ssl_warning_occurred = True
                if content:
                    processed_bytes, media_type = image_service.process_image(
                        image_bytes=content,
                        formato_saida=config.formato_saida,
                        qualidade=config.qualidade,
                        max_width=config.max_width,
                        max_height=config.max_height,
                        min_width=config.min_width,
                        min_height=config.min_height,
                        manter_proporcao=config.manter_proporcao,
                        cor_fundo_jpg=config.cor_fundo_jpg
                    )
                    ext = "jpg"
                    if config.formato_saida != "ORIGINAL":
                        ext = config.formato_saida.lower()
                    else:
                        if "png" in media_type: ext = "png"
                        elif "webp" in media_type: ext = "webp"
                        
                    filename = f"imagem_{idx+1}.{ext}"
                    zip_file.writestr(filename, processed_bytes)
        
        zip_buffer.seek(0)
        
        headers = {
            "Content-Disposition": "attachment; filename=imagens.zip",
            "Access-Control-Expose-Headers": "X-SSL-Warning",
            "X-SSL-Warning": "true" if ssl_warning_occurred else "false"
        }
        return StreamingResponse(zip_buffer, media_type="application/zip", headers=headers)
    except Exception as e:
        print(f"Erro no download zip: {e}")
        raise HTTPException(status_code=500, detail=str(e))




@router.get("/{id_peca:path}", response_model=List[schemas.SearchResult])
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
@router.get("/details/peca", response_model=dict)
async def buscar_detalhes_peca(
    codigo: str,
    provedor_id: int,
    db: Session = Depends(get_db),
):
    """
    Busca detalhes técnicos específicos de uma peça em um provedor.
    """
    try:
        detalhes = await search_service.buscar_detalhes(db, provedor_id, codigo)
        if not detalhes:
            return {"ficha_tecnica": {}, "imagens": []}
        return detalhes
    except Exception as e:
        print(f"ERRO NOS DETALHES: {e}")
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


