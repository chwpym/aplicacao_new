import asyncio
import sys
import os
import json

# Adiciona o diretório raiz ao sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.providers.notus_provider import NotusProvider


async def test_notus():
    config = {"id": 999, "nome": "NOTUS TEST", "tipo": "notus"}

    provider = NotusProvider(config)

    print("--- Testando Busca por Código Notus (NT-7061.523) ---")
    resultados = await provider.buscar("NT-7067.534")

    print(f"Total de resultados: {len(resultados)}")

    if resultados:
        for res in resultados[:2]:  # Mostra os 2 primeiros
            print(f"\nCódigo: {res['codigo']}")
            print(f"Montadora: {res['veiculo']}")
            print(f"Veículo: {res['modelo']}")
            print(f"Ano: {res['ano_inicio']} - {res['ano_fim']}")
            print(f"Imagem: {res['imagem']}")
            print(f"Observação: {res['observacao']}")
            print(f"Referências: {res['referencias']}")
            print("Ficha Técnica:")
            for k, v in res["ficha_tecnica"].items():
                print(f"  {k}: {v}")

    print("\n--- Testando Busca por Código OEM (5X0121253A) ---")
    resultados = await provider.buscar("5X0121253A")
    print(f"Total de resultados OEM: {len(resultados)}")
    if resultados:
        print(f"Primeiro resultado OEM: {resultados[0]['codigo']} - {resultados[0]['veiculo']} {resultados[0]['modelo']}")

    print("\n--- Testando Busca por Código Visconde (12253) ---")
    resultados = await provider.buscar("12253")
    print(f"Total de resultados 12253: {len(resultados)}")
    if resultados:
        res = resultados[0]
        print(f"Primeiro resultado 12253: {res['codigo']} - {res['veiculo']} {res['modelo']}")
        print(f"Referências: {res['referencias']}")


if __name__ == "__main__":
    asyncio.run(test_notus())
