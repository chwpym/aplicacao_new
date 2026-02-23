---
name: custom-search-provider
description: Guia para criar provedores independentes com motor de busca próprio (Python/REST/Scraping).
---

# Custom Search Provider Development

Este guia é para quando um catálogo **NÃO** segue o padrão genérico (GraphQL Fraga ou REST simples) e exige uma lógica de navegação e extração única (como o caso da BOSCH ou COFAP).

## 1. Estrutura da Classe

O novo provedor deve ser criado em `backend/app/providers/nome_provedor.py`.

```python
from app.providers.base_provider import BaseProvider
import httpx
import asyncio

class MeuProvedorCustom(BaseProvider):
    def __init__(self, config):
        self.config = config
        self.headers = { "User-Agent": "..." }

    async def buscar(self, part_id: str) -> list[dict]:
        # 1. Lógica própria de request (httpx)
        # 2. Parser dos dados retornados
        # 3. Formatação usando self.formatar_resultado
        return resultados_formatados
```

## 2. Hierarquia de Nomes (Crítico)

Para manter a consistência com o Frontend e as **Siglas/Limpeza**, os dados devem ser mapeados para as chaves internas corretas no dicionário `raw_data` antes de passar por `self.formatar_resultado(raw_data)`:

| Nome na Tela   | Chave Interna | O que enviar no dicionário             |
| :------------- | :------------ | :------------------------------------- |
| **Marca Peça** | `brand`       | Nome do fabricante da peça (ex: Bosch) |
| **Montadora**  | `veiculo`     | Nome da montadora (ex: FIAT, VW)       |
| **Veículo**    | `modelo`      | Nome do carro (ex: TORO, ONIX)         |
| **Modelo**     | `versao`      | Especificação (ex: 1.3 GSE, CLASSIC)   |
| **Motor**      | `motor`       | Motorização (ex: 1.0, 1.6)             |

## 3. Registro no Orquestrador

Após criar o arquivo, registre o novo tipo no `backend/app/services/search_service.py`:

1. Importe a classe no topo do arquivo.
2. Adicione a lógica de inicialização no loop de provedores (ou no factory de provedores).

## 4. Dicas de Ouro

- **Timeout**: Use timeouts generosos (30s+) para provedores lentos.
- **Normalização de Data**: Se o catálogo mandar datas como `MM.YYYY`, entregue apenas o `YYYY` para o sistema para evitar erros de interpretação de meses como anos.
- **Imagens**: Sempre retorne uma lista em `images` ou uma URL única em `image`.

> [!IMPORTANT]
> Provedores customizados são mais potentes porque podem fazer múltiplas chamadas (ex: buscar ID -> buscar veículos -> buscar detalhes) em paralelo usando `asyncio.gather`.
