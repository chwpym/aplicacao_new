---
name: schaeffler-integration
description: Conhecimento técnico sobre a integração com o catálogo REST da Schaeffler (LUK, FAG, INA).
---

# Schaeffler Integration (LUK, FAG, INA)

Este provedor utiliza a API REST do portal Vehicle Lifetime Solutions da Schaeffler.

## 1. Arquitetura de Extração

O catálogo é hierárquico e exige múltiplas chamadas para obter a aplicação completa:

1.  **Discovery (Search)**:
    - Endpoint: `/api/AAM-BR/products/search`
    - Resolve o código comercial (ex: `619301500`) para o ID interno (`TA-479-6193015000`).
    - **Importante**: O campo `linkages.manufacturers` pode vir vazio na busca inicial se houver muitos resultados.

2.  **Fase Paralela (asyncio.gather)** — Dispara 4 requests simultâneos:
    - **OE Numbers**: `/api/AAM-BR/products/{code}/oenumbers` — Extrai referências cruzadas OE com prefixo de marca. **ATENÇÃO**: endpoint é todo minúsculo (`oenumbers`), não camelCase.
    - **Product Detail**: `/api/AAM-BR/products/{code}?fields=FULL` — Extrai imagem, dimensões (comprimento/largura/altura/peso) e classificações (diâmetro, info complementar, etc.).
    - **Kit Contents**: `/api/AAM-BR/products/{code}/references?referenceType=CONSISTS_OF&inverse=false&fields=DEFAULT` — Extrai composição do kit (Platô, Disco, Rolamento, etc.).
    - **Manufacturers Fallback**: `/api/AAM-BR/products/{code}/linkages/manufacturers` — Chamado caso a busca inicial não retorne as montadoras.

3.  **Hydration L2 (Model Series)**:
    - Endpoint: `/api/AAM-BR/products/{code}/linkages/manufacturers/{mfr_uuid}/modelSeries`
    - Retorna as linhas de veículos (ex: `DOBLO`, `PALIO`).

4.  **Hydration L3 (Targets)**:
    - Endpoint: `/api/AAM-BR/products/{code}/linkages/modelSeries/{series_uuid}/targets`
    - Retorna a motorização, anos detalhados e especificações técnicas.

## 2. Padrões de Dados

### Datas e Anos
- A API retorna datas no formato `MM.YYYY` (ex: `11.2001`).
- O provedor utiliza o método `_parse_schaeffler_year` para extrair apenas o ano (`YYYY`), evitando que o motor de normalização confunda o mês com um ano curto (ex: `11` -> `2011`).

### Referências Cruzadas (OE Numbers)
- Extraídas do endpoint dedicado `/oenumbers` (não do campo `productReferences` que vem vazio).
- O provedor distingue entre referências "intercambiáveis" (prefixo `MARCA:`) e referências de peça (prefixo `MARCA (REF):`).
- Formato obrigatório para o frontend: `MARCA: CÓDIGO` (ex: `FIAT: 46743928`).

### Composição do Kit (Contém)
- Extraída do endpoint `/references?referenceType=CONSISTS_OF`.
- Cada componente tem `fullName` e `catalogArticleNumber`.
- Injetado na ficha técnica como campo `CONTÉM` (ex: `Platô da embreagem (119 0124 10) + Disco de embreagem (319 0150 10)`).

### Imagens
- Extraídas do campo `images` do endpoint de detalhes (`?fields=FULL`).
- Formatos: `product` (imagem principal), `zoom` (alta resolução), `thumbnail`.
- URLs relativas são prefixadas com `https://vehiclelifetimesolutions.schaeffler.com.br`.

### Dimensões e Classificações
- `dimensions` → Comprimento, Largura, Altura (mm).
- `weight` → Peso (kg).
- `classifications[].features[]` → Diâmetro, Info complementar, etc. (filtra SVHC automaticamente).

### Marcas e Códigos
- Embora o provedor seja único (`schaeffler`), ele extrai a marca real do produto (`LUK`, `FAG` ou `INA`) dinamicamente.
- O código da peça é extraído de `catalogArticleNumber` do produto original para garantir consistência em todas as linhas de aplicação.

## 3. Integração Frontend

### Ficha Técnica na Cópia (clipboard.ts)
- O bloco de ficha técnica é adicionado no `clipboard.ts` após a referência de similares.
- Filtra por `provedor` ou `marca` sendo `LUK`, `FAG` ou `INA`.
- Formato: `FICHA TÉCNICA (LUK):` seguido de `CAMPO: VALOR` por linha.
- O título do bloco usa a marca dinâmica do primeiro resultado com ficha.

## 4. Resiliência e Performance
- Utiliza `asyncio.gather` com `chunk_size` de 15 para processar centenas de aplicações sem estourar o limite de conexões ou ser bloqueado pelo servidor.
- Headers simulam um navegador real para evitar erros 403 Forbidden.
- Timeout de 30s por request de hidratação L3.
