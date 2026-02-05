from fastapi import APIRouter, Depends, HTTPException
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
