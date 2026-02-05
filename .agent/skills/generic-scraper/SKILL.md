---
name: Generic Scraper Configuration
description: Diretrizes para configurar robôs de extraçã de dados via Web Scraping.
---

# Generic Scraper Configuration

Esta skill define como configurar novos provedores de scraping no sistema sem mexer no código.

## 1. Identificação de Seletores
- **Container**: Use seletores que capturem a linha da tabela (ex: `.table tr`).
- **Campos**: Mapeie cada coluna para os campos padrão:
    - `td.modelo` -> `veiculo`
    - `td.motor` -> `motor`
    - `td.ano` -> `ano_inicio`

## 2. Padrões de Navegação
- Sempre configure a URL de busca com o marcador `{id}` (ex: `https://site.com/busca?q={id}`).
- Verifique se o site tem uma página intermediária de resultados antes da página do produto.

## 3. Boas Práticas
- Use `JSON.stringify` no formulário para manter o mapeamento limpo.
- Prefira seletores de classe (`.classe`) em vez de seletores de ID (`#id`) quando possível.
