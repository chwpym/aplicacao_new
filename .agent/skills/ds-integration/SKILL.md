---
name: ds-integration
description: Conhecimento técnico sobre a integração com o catálogo da DS (Discovery-Hydration).
---

# DS Integration Skill

Esta skill detalha os padrões e seletores específicos para o catálogo da DS (https://www.ds.ind.br).

## 1. Arquitetura de Busca (Discovery-Hydration)
O catálogo da DS requer busca em dois níveis porque a página de resultados é "rasa" (não contém referências OE nem tabelas de aplicação completas).

### Passo 1: Discovery (Busca Full)
- **URL:** `https://www.ds.ind.br/pt/busca-full?q={query}`
- **Mira Laser:** Filtre os resultados comparando o código buscado com o atributo `alt` das tags `img` dentro dos cards. Isso evita processar sugestões irrelevantes do site.
  ```python
  img = card.select_one("img")
  if img and img.get("alt") == part_id:
      # Item validado para Hydration
  ```

### Passo 2: Hydration (Detalhes)
Acesse a URL capturada no Discovery para extrair os dados técnicos.

## 2. Seletores Críticos

| Dado | Seletor CSS | Observação |
| :--- | :--- | :--- |
| **Título** | `h1` | Geralmente o nome da peça. |
| **Referências OE** | `.jq-codes tr`, `.tabela-referencias tr` | **Atenção:** Pode vir em coluna única (`td`). Use `separator=":"` no `get_text()`. |
| **Aplicações** | `.jq-apps tr`, `.table-aplicacao tr` | Coluna 3 contém Complemento/Combustível. |
| **Imagens** | `.pgwSlider img`, `.img-produto` | Capture o `src` ou `data-src`. |

## 3. Mapeamento de Combustível e Motor
Para evitar duplicação no grid, aplique a heurística de limpeza:

- Se a coluna **"Combustível"** (Complemento) contiver apenas um combustível conhecido (Ex: "FLEX"), mova-o para o campo `fuel` e limpe o campo `configuracao_motor`.
- Tipos comuns: `["FLEX", "GASOLINA", "ALCOOL", "DIESEL", "GNV", "TETRAFUEL"]`.

## 4. Tratamento de Erros
- **Redirects:** A DS às vezes redireciona buscas com 1 resultado direto para a página do produto. O robô deve tratar tanto o cenário de `200 OK` (lista) quanto o de redirect para o produto.
