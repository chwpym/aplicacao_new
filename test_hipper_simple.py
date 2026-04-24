import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.providers.hipperfreios_provider import HipperFreiosProvider

async def test():
    config = {"id": 44, "nome": "HIPPER FREIOS", "url": "https://www.hipperfreios.com.br"}
    provider = HipperFreiosProvider(config)
    print("Buscando HF08B...")
    results = await provider.buscar("HF08B")
    print(f"Resultados encontrados: {len(results)}")
    if results:
        print("Primeiro resultado:")
        print(f"Marca: {results[0].get('marca')}")
        print(f"Marca Peca: {results[0].get('marca_peca')}")
        print(f"Montadora: {results[0].get('marca_veiculo')}")
        print(f"Veiculo: {results[0].get('veiculo')}")
        print(f"Ficha Tecnica: {results[0].get('ficha_tecnica')}")

if __name__ == "__main__":
    asyncio.run(test())
