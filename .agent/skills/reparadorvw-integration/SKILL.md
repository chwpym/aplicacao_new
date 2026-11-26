---
name: reparadorvw-integration
description: Conhecimento técnico e diretrizes de integração híbrida do catálogo oficial Volkswagen Reparadores (Ponte GraphQL Fraga) + Fallback Completo de 53.800+ peças e fotos HD na Loja Oficial Peças VW (pecas.vw.com.br / Algolia).
---

# Integração Híbrida Volkswagen Reparadores + Loja Oficial Peças VW (`reparadorvw`)

Esta skill documenta a arquitetura técnica híbrida do provedor **VW REPARADOR** ([`reparadorvw_provider.py`](file:///d:/Dev/aplicacao_new/backend/app/providers/reparadorvw_provider.py)), unificando os dois ecossistemas oficiais de peças genuínas da Volkswagen no Brasil em um único provedor resiliente.

---

## 1. Fonte Primária: Ponte GraphQL Reparador VW (`~2.650` Peças de Manutenção/Mecânica)

O portal `https://www.reparadorvw.com.br/catalogo` consome dados do Catálogo Fraga V2 através de uma **Ponte Reversa** hospedada em:

```
POST https://www.reparadorvw.com.br/api/catalogo/gql
```

### Regras Críticas da Ponte
1. **Autenticação Transparente (Server-Side):** O servidor da Volkswagen injeta internamente o token OAuth2 da Fraga (`login_required = False`). Exige apenas os headers `Origin: https://www.reparadorvw.com.br` e `Referer: https://www.reparadorvw.com.br/catalogo`.
2. **Whitelist Estrita de Queries:** Qualquer query fora da whitelist do bundle JS oficial (`catalogo.*.js`) retorna HTTP `400` (`CATALOGO_CONSULTA_NAO_PERMITIDA`).
3. **Discovery → Hydration Paralela:**
   - **Discovery:** `catalogSearchByCode` (`by: ["PART_NUMBER"]`) com fallback para `catalogSearch`.
   - **Hydration:** `product(id: $id, market: BRA)` trazendo veículos com motor/válvulas/versão detalhados, especificações físicas, NCM e códigos antigos (`oldCodes`).

---

## 2. Fonte Secundária (Fallback Duplo): Loja Oficial `pecas.vw.com.br` (`53.800+` Peças Genuínas via Algolia)

O e-commerce oficial da Volkswagen (`https://pecas.vw.com.br` / `pecas.reparadorvw.com.br`) mantém um índice público de leitura no Algolia (`prod_main_products_v2`, App ID `JPW9SFM280`) com mais de **53.800 peças genuínas** (abrangendo lataria, grades, molduras, para-choques, faróis, lanternas, vidros e acabamentos internos que não constam na base mecânica da Fraga).

O provedor utiliza essa fonte em **dois níveis totalmente isolados por `try/except` e timeout curto (`6s`)** (garantindo que nunca atrase nem quebre a fonte primária):

### Fallback A — Resgate de Fotos `900x900` e Giro `360°`
- Cerca de 95% das peças na base Fraga da VW vêm com `images: []`.
- Quando `images` vem vazio, `_fetch_loja_oficial_photos()` consulta o Algolia pelo Part Number exato e extrai até 8 imagens em alta definição (`https://dvo56mb5swza6.cloudfront.net/900x900/...`), combinando 4 ângulos do giro 360° + fotos avulsas.

### Fallback B — Resgate Completo de Peça e Aplicações (`53.800+` Itens)
- Acionado automaticamente quando o GraphQL do Reparador VW retorna `0` resultados para o código pesquisado (ou quando a peça existe na Fraga sem veículos cadastrados).
- Filtra rigorosamente por match exato (`codigo_original` / `codigosoriginais`) ou prefixo de código base com 7+ caracteres (ex: buscar `5U0853665` encontra automaticamente as variações de cor `5U0853665S9B9` e `5U0853665P9B9`, sem trazer falsos positivos).
- Extrai de cada item:
  - **Aplicações (`resumo_aplicacao`):** Separa nomes compostos (`Polo Track` → `POLO` + `TRACK`, `Tiguan Allspace` → `TIGUAN` + `ALLSPACE`) com `ano_inicio` (`a1`) e `ano_fim` (`a2`).
  - **Lado e Posição (`caracteristicas`):** Mapeia automaticamente `"Lado de Montagem"` → `lado` e `"Posição de Montagem"` → `posicao`.
  - **Ficha Técnica e Imagens:** Preenche `DESCRIÇÃO COMERCIAL`, `CATEGORIA`, `LINHA / SISTEMA`, `UNIDADE DE VENDA`, `GARANTIA` e até 8 fotos `900x900`.

---

## 3. Tratamento de Dados e Normalização Específica

| Origem | Campo Bruto | Destino `BaseProvider` | Regra Aplicada |
| :--- | :--- | :--- | :--- |
| GraphQL | `vehicle.brand` | `montadora` | Atalho rápido `VOLKSWAGEN` → `VW` |
| GraphQL | `vehicle.model` | `versao` | `S- TRONIC` → `S-TRONIC`; `TOTAL FLEX` / `TOTALFLEX` → `FLEX`; remoção de `\xa0` |
| GraphQL | `vehicle.engineName` | `motor` | Remoção de milhar redundante (`AP 1800` → `AP` quando `engineConfiguration` já tem `1.8 L 8V`) |
| Algolia | `resumo_aplicacao[].moto` | `modelo` + `versao` | Desmembramento inteligente de sufixos (`Polo Track` → `POLO` / `TRACK`) |
| Algolia | `caracteristicas[]` | `lado` / `posicao` / `ficha_tecnica` | Extração automática de Lado (Motorista/Passageiro) e Posição (Dianteiro/Traseiro) |

---

## 4. Códigos Validados para Homologação
- **`026103547A`** *(Fonte Primária GraphQL)* — Defletor de óleo (`593` aplicações históricas VW/Seat, 4 fotos Fraga).
- **`04E115561AC`** *(Fonte Primária GraphQL)* — Filtro de óleo (`282` aplicações modernas VW/Audi, 5 fotos Fraga + medidas técnicas completas).
- **`5U0853665S9B9`** / **`5U0853665`** *(Fallback B Algolia `pecas.vw.com.br`)* — Moldura de Farol de Milha (`Gol`, `Saveiro`, `Voyage` `2017..2022`, `Lado: ESQUERDO (MOTORISTA)`, `Posição: DIANTEIRO`, 4 fotos HD `900x900`).
- **`2QB698151C`** *(Fallback B Algolia `pecas.vw.com.br`)* — Pastilha de Freio Dianteira (`Polo`, `Polo Track`, `Tera`, `Virtus`, `Posição: DIANTEIRO`, 4 fotos HD `900x900`).
