from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import models, schemas
from typing import List

router = APIRouter(prefix="/config", tags=["Configuração"])

# --- CRUD Provedores ---
@router.get("/provedores", response_model=List[schemas.Provedor])
def get_provedores(db: Session = Depends(get_db)):
    return db.query(models.Provedor).all()

@router.post("/provedores", response_model=schemas.Provedor)
def create_provedor(provedor: schemas.ProvedorCreate, db: Session = Depends(get_db)):
    db_provedor = models.Provedor(**provedor.dict())
    db.add(db_provedor)
    db.commit()
    db.refresh(db_provedor)
    return db_provedor

@router.delete("/provedores/{provedor_id}")
def delete_provedor(provedor_id: int, db: Session = Depends(get_db)):
    db_provedor = db.query(models.Provedor).filter(models.Provedor.id == provedor_id).first()
    if not db_provedor:
        raise HTTPException(status_code=404, detail="Provedor não encontrado")
    db.delete(db_provedor)
    db.commit()
    return {"message": "Provedor excluído"}

@router.put("/provedores/{provedor_id}", response_model=schemas.Provedor)
def update_provedor(provedor_id: int, provedor: schemas.ProvedorCreate, db: Session = Depends(get_db)):
    db_provedor = db.query(models.Provedor).filter(models.Provedor.id == provedor_id).first()
    if not db_provedor:
        raise HTTPException(status_code=404, detail="Provedor não encontrado")
    
    for key, value in provedor.dict().items():
        setattr(db_provedor, key, value)
    
    db.commit()
    db.refresh(db_provedor)
    return db_provedor

# --- CRUD Siglas ---
@router.get("/siglas", response_model=List[schemas.Sigla])
def get_siglas(db: Session = Depends(get_db)):
    return db.query(models.Sigla).all()

@router.post("/siglas", response_model=schemas.Sigla)
def create_sigla(sigla: schemas.SiglaCreate, db: Session = Depends(get_db)):
    db_sigla = models.Sigla(**sigla.dict())
    db.add(db_sigla)
    db.commit()
    db.refresh(db_sigla)
    return db_sigla

@router.delete("/siglas/{sigla_id}")
def delete_sigla(sigla_id: int, db: Session = Depends(get_db)):
    db_sigla = db.query(models.Sigla).filter(models.Sigla.id == sigla_id).first()
    if not db_sigla:
        raise HTTPException(status_code=404, detail="Sigla não encontrada")
    db.delete(db_sigla)
    db.commit()
    return {"message": "Sigla excluída"}

# --- CRUD Palavras ---
@router.get("/palavras", response_model=List[schemas.PalavraRemover])
def get_palavras(db: Session = Depends(get_db)):
    return db.query(models.PalavraRemover).all()

@router.post("/palavras", response_model=schemas.PalavraRemover)
def create_palavra(palavra: schemas.PalavraRemoverCreate, db: Session = Depends(get_db)):
    db_palavra = models.PalavraRemover(**palavra.dict())
    db.add(db_palavra)
    db.commit()
    db.refresh(db_palavra)
    return db_palavra

@router.delete("/palavras/{palavra_id}")
def delete_palavra(palavra_id: int, db: Session = Depends(get_db)):
    db_palavra = db.query(models.PalavraRemover).filter(models.PalavraRemover.id == palavra_id).first()
    if not db_palavra:
        raise HTTPException(status_code=404, detail="Palavra não encontrada")
    db.delete(db_palavra)
    db.commit()
    return {"message": "Palavra excluída"}

@router.get("/automakers")
def get_automakers():
    from app.services.automaker_service import automaker_service
    return {
        "status": "ok", 
        "count": len(automaker_service._model_to_brand),
        "last_update": getattr(automaker_service, "_last_update", "N/A"),
        "catalog": automaker_service._catalog, # Retorna o dicionário completo {Marca: [Modelos]}
        "brands": automaker_service._brands
    }

@router.post("/fipe/sync")
async def sync_fipe(background_tasks: BackgroundTasks):
    try:
        from scripts.sync_fipe_catalog import sync_catalog
        from app.services.automaker_service import automaker_service
        
        async def run_sync_and_reload():
            await sync_catalog()
            automaker_service.reload()
            
        background_tasks.add_task(run_sync_and_reload)
        return {"status": "success", "message": "Sincronização FIPE iniciada em segundo plano."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao iniciar sincronização: {str(e)}")

@router.post("/automakers/model")
def add_custom_model(data: dict):
    brand = data.get("brand")
    model = data.get("model")
    if not brand or not model:
        raise HTTPException(status_code=400, detail="Marca e modelo são obrigatórios")
    
    from app.services.automaker_service import automaker_service
    if automaker_service.add_model_manual(brand, model):
        return {"status": "success", "message": f"Modelo {model} adicionado à {brand}"}
    raise HTTPException(status_code=500, detail="Erro ao salvar modelo")

@router.delete("/automakers/model")
def remove_custom_model(brand: str, model: str):
    from app.services.automaker_service import automaker_service
    if automaker_service.remove_model_manual(brand, model):
        return {"status": "success", "message": f"Modelo {model} removido de {brand}"}
    raise HTTPException(status_code=500, detail="Erro ao remover modelo")

# --- Backup ---
@router.post("/backup/export")
def export_backup():
    try:
        from scripts.export_system_state import export_state
        backup_path = export_state()
        return {"status": "success", "message": f"Backup realizado em: {backup_path}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao realizar backup: {str(e)}")


# --- Preferências Globais ---
@router.get("/preferencias/{chave}")
def get_preferencia(chave: str, db: Session = Depends(get_db)):
    config = db.query(models.Configuracao).filter(models.Configuracao.chave == chave).first()
    if not config:
        return {"chave": chave, "valor": None}
    return {"chave": chave, "valor": config.valor}

@router.post("/preferencias")
def save_preferencia(data: dict, db: Session = Depends(get_db)):
    chave = data.get("chave")
    valor = data.get("valor")
    if not chave:
        raise HTTPException(status_code=400, detail="Chave é obrigatória")
    
    config = db.query(models.Configuracao).filter(models.Configuracao.chave == chave).first()
    if config:
        config.valor = valor
    else:
        config = models.Configuracao(chave=chave, valor=valor)
        db.add(config)
    
    db.commit()
    return {"status": "success", "message": "Preferência salva"}

