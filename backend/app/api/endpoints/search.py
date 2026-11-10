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
        from fastapi.responses import Response
        from app.services.image_service import image_service

        clean_url = url.strip().rstrip(".")
        content, _, original_content_type = await image_service.download_image(clean_url)

        if not content:
            raise HTTPException(
                status_code=404,
                detail="Falha ao buscar imagem externa",
            )

        # Preserva o Content-Type original do fabricante se for válido
        media_type = original_content_type if (original_content_type and original_content_type.startswith("image/")) else "image/jpeg"

        return Response(content=content, media_type=media_type)
    except HTTPException:
        raise
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
        content, _, _ = await image_service.download_image(url)
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
        import asyncio
        from app.services.image_service import image_service
        from app.models import models
        from fastapi.responses import StreamingResponse
        
        config = db.query(models.ConfiguracaoImagem).first()
        if not config:
            config = models.ConfiguracaoImagem()

        zip_buffer = io.BytesIO()
        ssl_warning_occurred = False
        images_added = 0
        semaphore = asyncio.Semaphore(5)
        results_lock = asyncio.Lock()
        
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED, False) as zip_file:
            async def download_one(idx: int, url: str):
                nonlocal ssl_warning_occurred, images_added
                async with semaphore:
                    content, ssl_warn, _ = await image_service.download_image(url)
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
                        async with results_lock:
                            zip_file.writestr(filename, processed_bytes)
                            images_added += 1

            await asyncio.gather(*[download_one(idx, url) for idx, url in enumerate(urls)])
            
        if images_added == 0:
            raise HTTPException(
                status_code=422,
                detail="Nenhuma imagem pôde ser baixada. O servidor do fabricante pode estar temporariamente fora do ar ou bloqueando conexões externas."
            )
        
        zip_buffer.seek(0)
        
        headers = {
            "Content-Disposition": "attachment; filename=imagens.zip",
            "Access-Control-Expose-Headers": "X-SSL-Warning, X-Images-Total, X-Images-Downloaded",
            "X-SSL-Warning": "true" if ssl_warning_occurred else "false",
            "X-Images-Total": str(len(urls)),
            "X-Images-Downloaded": str(images_added)
        }
        return StreamingResponse(zip_buffer, media_type="application/zip", headers=headers)
    except HTTPException:
        raise
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


