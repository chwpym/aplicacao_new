---
name: cofap-fraga-integration
description: Conhecimento especializado para integrar os catálogos COFAP e Monroe (plataforma Fraga) com extração enriquecida de dados.
---

# Integração COFAP / Monroe (Fraga)

Este skill descreve como manter e expandir a integração com os catálogos da plataforma Fraga (especificamente COFAP e Monroe), que utilizam GraphQL com estruturas complexas de veículos e especificações.

## Arquitetura de Extração

A integração utiliza o `CofapProvider` (em `backend/app/providers/cofap_provider.py`), que herda de `GraphQLProvider` mas sobrescreve métodos críticos para lidar com as particularidades da API Fraga.

### 1. Descoberta de UUID (Discovery)

Diferente de outros provedores, a Fraga exige o parâmetro `market: "BRA"` (ou similar) já na fase de busca por código.

- **Método**: `search_product_id`
- **Query**: `catalogSearch`
- **Variáveis**: `query`, `market: "BRA"`

### 2. Recuperação Enriquecida (Retrieval)

A query principal deve capturar não apenas o produto e veículos, mas também referências cruzadas e especificações para extrair informações como o "Modelo" do produto (ex: SUPER, TURBOGAS).

**Campos Essenciais na Query**:

```graphql
product(id: $id, market: $market) {
  images { imageUrl }
  crossReferences { brand { name } partNumber }
  specifications { description value }
  vehicles { brand name startYear endYear note only restriction ... }
}
```

### 3. Parser e Formatação

- **Referências Cruzadas**: Devem ser extraídas sem filtros restritivos para garantir que OEM e marcas concorrentes sejam exibidas.
- **Imagens**: A primeira imagem da lista `images` deve ser definida como `imagem` principal.
- **Modelo (Especificações)**: O campo `Modelo` dentro de `specifications` deve ser verificado. Se o veículo não possuir um modelo claro, ou se este valor for mais descritivo, ele deve ser injetado.

## Autenticação

Utiliza o fluxo Keycloak dinâmico via `AuthService`.

- **Realm**: Geralmente `cat_cofap`.
- **Headers**: Exige `Origin` e `Referer` apontando para `https://cofap.catalogofraga.com.br`.

## Scripts Úteis

- `backend/tools/seed_cofap.py`: Restaura as configurações básicas do provedor.
- `backend/tools/update_cofap_query.py`: Atualiza a query GraphQL no banco de dados.
- `backend/tools/test_restored_cofap.py`: Valida a extração completa de dados.
