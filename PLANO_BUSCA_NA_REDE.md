# Plano de Correção — Provedor "Busca na Rede"

## Diagnóstico

O provedor `BuscaNaRedeProvider` (ID 48) causa **erro 500** ao ser acionado:

```
Can't instantiate abstract class BuscaNaRedeProvider
without an implementation for abstract method 'buscar'
```

### Causa Raiz (3 problemas encontrados)

| # | Problema | Arquivo | Linha |
|---|---------|---------|-------|
| 1 | **Método `buscar` não existe.** O provedor implementa `search()` (síncrono), mas o `BaseProvider` exige `async buscar()`. O Python recusa instanciar a classe. | `busca_na_rede_provider.py` | L31 |
| 2 | **Construtor incompatível.** O `__init__` recebe parâmetros avulsos (`provedor_id`, `nome`, `slug`...) e chama `super().__init__(...)` com esses argumentos, mas o `BaseProvider` **não tem `__init__`** — é uma ABC pura. Isso gera `TypeError`. | `busca_na_rede_provider.py` | L18-19 |
| 3 | **Factory passa `config_model.slug`** que pode ser `None` se o campo não estiver preenchido no banco. | `provider_factory.py` | L87 |

### Por que o servidor cai?

O `search_service.py` chama `provider_factory.get_provider(p_db)`, que tenta instanciar `BuscaNaRedeProvider(...)`. Como a classe **não pode** ser instanciada (falta o método abstrato), o Python lança uma exceção que não é capturada, resultando em HTTP 500.

---

## Plano de Correção (5 passos)

### Passo 1 — Refatorar o construtor para o padrão `config dict`

Todos os outros provedores recebem um único `config: Dict`. O `BuscaNaRedeProvider` deve seguir esse padrão.

### Passo 2 — Renomear `search()` → `async buscar()`

Converter o método `search` síncrono para `async buscar`, usando `httpx.AsyncClient` em vez de `requests`.

### Passo 3 — Converter `_hydrate_product_details` para async

Mesma conversão: `requests.get` → `await client.get`.

### Passo 4 — Usar `formatar_resultado()` do `BaseProvider`

O provedor atual monta os dicts manualmente. Devemos usar `self.formatar_resultado(raw_data)` para que os resultados passem pela normalização.

### Passo 5 — Atualizar a Factory

Simplificar a chamada na `provider_factory.py` para seguir o padrão `BuscaNaRedeProvider(config)`.

---

## Impacto

| Arquivo | Tipo |
|---------|------|
| `backend/app/providers/busca_na_rede_provider.py` | REESCRITA |
| `backend/app/providers/provider_factory.py` | MINOR (5 linhas → 2 linhas) |

> **IMPORTANTE:** Nenhum arquivo Core é alterado (BaseProvider, NormalizationService, SearchService).
