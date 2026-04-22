import sys
import os

# Ajustar o PATH para conseguir importar os módulos do app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
from app.providers.base_provider import BaseProvider
from app.services.search_service import _agrupar_por_veiculo

class DummyProvider(BaseProvider):
    async def buscar(self, termo: str) -> list[dict]:
        return []

def testar():
    provider = DummyProvider()

    # Cenário 1: Provedor A mandando sujeira no modelo e com várias referências misturadas
    raw_data_1 = {
        "marca": "TECFIL",
        "montadora": "VW",
        "modelo": "GOL G4 1.0 8V",
        "configuracao_motor": "FLEX",
        "referencias": "OEM: 12345 | BOSCH: BO-12 | TECFIL: TC-34 | WEGA: WG-56"
    }

    # Cenário 2: Provedor B mandando sujeira na configuração e usando nome diferente da montadora
    raw_data_2 = {
        "marca": "TECFIL", # Mesma marca de peça para forçar o agrupamento
        "montadora": "VOLKSWAGEN",
        "modelo": "GOL G4",
        "motor": "1.0",
        "configuracao_motor": "8V FLEX C/ AR CONDICIONADO",
        "referencias": "VW: 12345 | MANN: W712"
    }

    formatted_1 = provider.formatar_resultado(raw_data_1)
    formatted_2 = provider.formatar_resultado(raw_data_2)

    print("=== TESTE 1: PIPELINE DE NORMALIZACAO (COMO FICA O JSON) ===")
    print("\n--- Provedor A (Antes: 'GOL G4 1.0 8V' / 'FLEX') ---")
    print(f"Modelo: '{formatted_1['modelo']}'")
    print(f"Motor: '{formatted_1['motor']}'")
    print(f"Configuração: '{formatted_1['configuracao_motor']}'")
    print(f"Referências: '{formatted_1['referencias']}' (Note que VW (OEM) veio antes das outras!)")

    print("\n--- Provedor B (Antes: '1.0' / '8V FLEX C/ AR CONDICIONADO') ---")
    print(f"Modelo: '{formatted_2['modelo']}'")
    print(f"Motor: '{formatted_2['motor']}'")
    print(f"Configuração: '{formatted_2['configuracao_motor']}'")
    print(f"Referências: '{formatted_2['referencias']}'")

    print("\n\n=== TESTE 2: AGRUPAMENTO DO FRONTEND (COMO FICA A TABELA) ===")
    aplicacoes = [formatted_1, formatted_2]
    agrupados = _agrupar_por_veiculo(aplicacoes)

    print(f"Total de linhas que aparecerão no Frontend: {len(agrupados)} (Antes do ajuste, seriam {len(aplicacoes)} linhas duplicadas)")
    for i, app in enumerate(agrupados):
        print(f"\nLINHA {i+1} NA TELA:")
        print(f"  Montadora/Veículo: {app['veiculo']}")
        print(f"  Modelo Base:       {app['modelo']}")
        print(f"  Motor:             {app['motor']}")
        print(f"  COLUNA CONFIG. MOTOR: >> {app['configuracao_motor']} <<")

if __name__ == "__main__":
    testar()
