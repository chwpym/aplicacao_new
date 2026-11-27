from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base, SessionLocal
from app.models import models
from app.db_seed import auto_seed_db

# Cria as tabelas no banco de dados
models.Base.metadata.create_all(bind=engine)

# Auto-seed caso o banco esteja vazio (garante dados em ambientes efêmeros como Render)
try:
    with SessionLocal() as db:
        auto_seed_db(db)
except Exception as e:
    print(f"[SEED] Aviso: erro ao executar auto-seed: {e}")

app = FastAPI(title="API Gerenciador de Peças", version="1.0.0")

# Configuração do CORS para permitir o frontend React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Em produção, defina as origens permitidas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "API de Catálogo de Peças online"}

@app.get("/api/health")
async def health_check():
    from app.services.status_service import status_service
    return await status_service.get_system_status()

from app.api.endpoints import search, config, zpl
app.include_router(search.router)
app.include_router(config.router)
app.include_router(zpl.router)
