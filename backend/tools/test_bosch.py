import asyncio
from app.providers.bosch_provider import BoschProvider


async def test_bosch():
    config = {
        "id": 999,
        "nome": "BOSCH TEST",
        "url": "https://am.boschaftermarket.com/",
        "tipo": "bosch",
        "mapeamento": "{}",
    }

    provider = BoschProvider(config)

    print("Buscando 0986BB0096 na Bosch...")
    resultados = await provider.buscar("0986BB0096")

    print(f"Encontrados {len(resultados)} resultados.")
    for r in resultados[:5]:
        print(
            f"- {r['marca']} | {r['veiculo']} {r['modelo']} | {r['motor']} ({r['ano_inicio']} - {r['ano_fim']})"
        )
        print(f"  Refs: {r.get('referencias', '')[:100]}...")
        print(f"  Img: {len(r.get('imagens', []))} imagens")
        print("---")


if __name__ == "__main__":
    asyncio.run(test_bosch())
