import sys
import os

# Ajusta o path para importar os módulos da aplicação
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.providers.base_provider import BaseProvider

# Mock de dados reais da Spicer (conforme seu JSON)
fraga_specifications = [
    {"description": "Quantidade de estrias", "value": "22 / 23 Und"},
    {"description": "Código de barras (EAN)", "value": "7892724032572"},
    {"description": "Comprimento", "value": "61,00 mm"},
    {"description": "Tipo de rosca", "value": "M20 X 1,0"},
    {"description": "Altura", "value": "240,00 mm"},
    {"description": "Largura", "value": "105,00 mm"}
]

# Instância simulada (BaseProvider é abstrata mas podemos testar o método concreto)
class MockProvider(BaseProvider):
    async def buscar(self, termo): return []

provider = MockProvider()
resultado = provider.parse_specifications(fraga_specifications)

print("\n--- TESTE DE PADRONIZAÇÃO DE FICHA TÉCNICA ---")
print(f"Entrada (Itens): {len(fraga_specifications)}")
print(f"Saída (Dicionário): {resultado}")
print("---------------------------------------------\n")

# Validações básicas
assert resultado["Quantidade de estrias"] == "22 / 23 Und"
assert resultado["Comprimento"] == "61,00 mm"
assert resultado["Tipo de rosca"] == "M20 X 1,0"

print("✅ SUCESSO: O parser converteu os dados corretamente!")
