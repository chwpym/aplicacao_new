import sys
import os

# Alinha o path
sys.path.append(r"d:\Dev\aplicacao_new\backend")

from app.database import SessionLocal
from app.models import models, schemas

print("--- TESTANDO CARREGAMENTO DE PROVEDORES ---")
db = SessionLocal()

try:
    provedores = db.query(models.Provedor).all()
    print(f"Total de provedores no DB: {len(provedores)}")
    
    # Tenta serializar para o schema do FastAPI
    for p in provedores:
        print(f"\nProvedor: [{p.id}] {p.nome} (Ativo: {p.ativo})")
        # Força o load do mapeamento
        print(f"Mapeamento: {p.mapeamento}")
        # Testa validação Pydantic
        schemas.Provedor.from_orm(p)
        print("Pydantic Ok")


        
except Exception as e:
    print("\n🚨 ERRO ENCONTRADO:")
    print(e)
    import traceback
    traceback.print_exc()

db.close()
print("\nFim do teste.")
