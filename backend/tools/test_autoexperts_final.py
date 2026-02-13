import asyncio
import json
from app.providers.autoexperts_provider import AutoExpertsProvider


async def test_integrated_autoexperts():
    # Simulando config que viria do DB
    config = {
        "nome": "AutoExperts",
        "url": "https://api.autoexperts.parts/autexp/bff/v1/catalog/products",
        "tipo": "autoexperts",
        "headers": json.dumps(
            {"x-region": "br", "origin": "https://www.autoexperts.parts"}
        ),
    }

    provider = AutoExpertsProvider(config)

    print("\n--- TESTANDO BUSCA INTEGRADA AUTOEXPERTS (C2182) ---")
    results = await provider.buscar("C2182")

    if results:
        print(f"Sucesso! {len(results)} aplicações encontradas.")

        # Pega a primeira aplicação para validar campos
        app = results[0]
        print("\nEXEMPLO DE APLICAÇÃO NORMALIZADA:")
        print(f"Marca: {app.get('marca')}")
        print(f"Código: {app.get('codigo')}")
        print(f"Veículo: {app.get('veiculo')}")
        print(f"Modelo: {app.get('modelo')}")
        print(f"Versão: {app.get('versao')}")
        print(f"Motor: {app.get('motor')}")
        print(f"Config. Motor: {app.get('configuracao_motor')}")
        print(f"Ano: {app.get('ano_inicio')} - {app.get('ano_fim')}")
        print(f"Posição: {app.get('posicao')}")
        print(f"Referências OE: {app.get('referencias')[:100]}...")
        print(f"Imagem: {app.get('imagem')[:100]}...")
    else:
        print("Nenhum resultado encontrado.")


if __name__ == "__main__":
    asyncio.run(test_integrated_autoexperts())
