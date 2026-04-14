---
name: backend-provider-development
description: Guia para criar, implementar e registrar novos provedores (classes Python) no backend.
---

# Backend Provider Development

Esta skill detalha como expandir o sistema com novas fontes de dados.

## 1. Criando a Classe do Provedor
Todos os provedores devem herdar de `BaseProvider` e ser salvos em `backend/app/providers/`.

```python
from app.providers.base_provider import BaseProvider

class MeuNovoProvider(BaseProvider):
    def __init__(self, config):
        super().__init__(config)
        self.headers = { "User-Agent": "..." }

    async def buscar(self, part_id):
        # Lógica de request usando self.client (httpx)
        # Extração de dados
        return [self.formatar_resultado(v) for v in resultados]
```

## 2. Padronização de Retorno (Smart Mapping)
O `BaseProvider.formatar_resultado()` é inteligente e aceita diversos nomes de chaves (sinônimos) para preencher os campos do Frontend. O desenvolvedor deve retornar um dicionário com os dados brutos; o sistema cuidará da normalização (Upper Case, limpeza Wega, extração de anos e combustíveis).

| Campo Final | Chaves Aceitas no Raw Data (Sinônimos) |
| :--- | :--- |
| **Marca Peça** | `marca_peca`, `marca`, `provedor` |
| **Montadora** | `brand`, `montadora`, `marca_veiculo` |
| **Veículo** | `name`, `veiculo`, `modelo` |
| **Versão** | `model`, `version`, `versao` |
| **Motor** | `engineName`, `motor` |
| **Combustível** | `fuel`, `combustivel` (Também extraído da `versao` via regex) |
| **Anos** | `startYear` / `endYear` ou `ano_inicio` / `ano_fim` |
| **Referências** | `originalNumbers`, `crossReferences`, `referencias` (Padrão `Marca: Código`) |
| **Imagens** | `image`, `imageUrl`, `imagem` (Single) ou `images`, `imagens` (List) |
| **Especificações**| `ficha_tecnica`, `specifications` (Dicionário ou Lista) |

> [!TIP]
> **Inteligência de Anos:** Se você enviar `2014 -->` no campo `startYear`, o sistema automaticamente preencherá o `ano_inicio` como `2014` e o `ano_fim` como vazio.

## 3. Registro e Ativação
Para que o sistema reconheça o novo provedor:
1. Importe-o no `backend/app/services/provider_service.py` (ou onde o Factory estiver).
2. Adicione ao mapeamento de tipos no `ProviderManager`.

## 4. Tratamento de Erros
- Use blocos `try/except` para capturar falhas de rede.
- Retorne uma lista vazia `[]` em caso de erro, para não interromper a busca nos outros provedores.
- Use logs para registrar o status do request.

## 5. Arquitetura de Busca em 2 Níveis (Discovery-Hydration)
Para sites complexos onde a lista de resultados não traz todos os dados técnicos:

1.  **Discovery (Passo 1):** Captura o ID interno ou a URL da peça no site.
    -   *Dica (Mira Laser):* Use atributos como `alt` das imagens ou links específicos para filtrar apenas o resultado exato e ignorar sugestões do site.
2.  **Hydration (Passo 2):** Realiza uma segunda requisição para a página de detalhes.
    -   Extraia: Tabelas de aplicação, Referências OE, Fichas Técnicas e Galeria de Imagens.
3.  **Performance:** Realize o Hydration apenas para os itens que passaram no filtro do Discovery. Use `asyncio.gather` se precisar hidratar múltiplos itens validados simultaneamente.
