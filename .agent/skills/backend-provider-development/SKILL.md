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

## 2. Padronização de Retorno
O método `buscar` deve retornar uma lista de dicionários com as seguintes chaves (exigidas pelo Frontend):
- `brand` (Marca)
- `name` (Veículo)
- `engineName` (Motor)
- `engineConfiguration` (Combustível/Complemento)
- `startYear` / `endYear` (String ou Inteiro - o sistema converte para string automaticamente para suportar formatos como "2014 -->")
- `images` (Lista de URLs)
- `originalNumbers` (String separada por ` | `)

## 3. Registro e Ativação
Para que o sistema reconheça o novo provedor:
1. Importe-o no `backend/app/services/provider_service.py` (ou onde o Factory estiver).
2. Adicione ao mapeamento de tipos no `ProviderManager`.

## 4. Tratamento de Erros
- Use blocos `try/except` para capturar falhas de rede.
- Retorne uma lista vazia `[]` em caso de erro, para não interromper a busca nos outros provedores.
- Use logs para registrar o status do request.
