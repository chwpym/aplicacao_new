import sys
import os
import asyncio
import json

# Adiciona o diretório 'backend' ao sys.path para podermos importar o app
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))
sys.stdout.reconfigure(encoding='utf-8')

from app.database import SessionLocal
from app.models.models import Provedor
from app.providers.provider_factory import get_provider

async def debug_motores():
    db = SessionLocal()
    try:
        provedor_db = db.query(Provedor).filter(Provedor.slug == "jahu").first()
        if not provedor_db:
            print("Provedor JAHU não encontrado!")
            return
            
        provedor = get_provider(provedor_db)
        resultados = await provedor.buscar("153549")
        
        print(f"Total de aplicações retornadas: {len(resultados)}")
        print(f"{'MONTADORA':<12} | {'VEICULO':<15} | {'VERSÃO/MODELO':<18} | {'MOTOR':<10} | {'CONFIG MOTOR':<12}")
        print("-" * 75)
        for app in resultados:
            montadora = app.get("veiculo", "")
            veiculo = app.get("modelo", "")
            versao = app.get("versao", "")
            motor = app.get("motor", "")
            config = app.get("configuracao_motor", "")
            print(f"{montadora:<12} | {veiculo:<15} | {versao:<18} | {motor:<10} | {config:<12}")
            
    except Exception as e:
        print(f"Erro: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(debug_motores())
