---
name: catalog-integration
description: Conhecimento especializado para integrar e manter catálogos de produtos via GraphQL e APIs REST, incluindo fluxos de autenticação Keycloak/OIDC.
---

# Catalog Integration & Maintenance

Esta skill capacita o gerenciamento do ecossistema de provedores de dados, combinando robustez técnica com flexibilidade de interface.

## 1. Conhecimento Técnico Core

### GraphQL (Padrão Fraga)
A maioria dos catálogos (SABÓ, INDISA, Authomix) utiliza o gateway da Fraga.
- **Endpoint Padrão:** `https://bff.catalogofraga.com.br/gateway/graphql`
- **Query Recomendada:** Deve incluir `product`, `crossReferences` (para OEM) e `vehicles` (para aplicações).
- **Estrutura de Mercado:** Utilizar a variável `$market: MarketType!` com fallback para `BRA`, `BRAZIL`, ou `Brasil`.

### Autenticação Keycloak (OIDC)
Para provedores protegidos como Authomix:
- **Fluxo:** Login na URL do Keycloak -> capturar `code` -> trocar por `access_token` no endpoint `/protocol/openid-connect/token`.
- **Bearer Token:** Enviar no cabeçalho `Authorization: Bearer <token>`.
- **Resiliência:** Sempre aplicar `.strip()` nas credenciais.

### Mapeamento de Peças (UUID)
1. **Discovery:** Converte o código da peça (ex: FOL0803) em um UUID único.
2. **Retrieval:** Usa o UUID para buscar os detalhes completos.

## 2. Interface Adaptativa (Metadata UI)

### Labels Dinâmicos
- **Configuração:** Adicione um objeto `labels` no mapeamento do provedor no Banco de Dados.
- **Efeito:** O Frontend substitui o nome da coluna conforme o provedor (Ex: `configuracao_motor` vira `Combustível` para DS).

### Padronização de Colunas (Grid)
Para manter o alinhamento visual no Frontend (`Home.tsx`), o dicionário de retorno em `formatar_resultado()` deve seguir estritamente:
- **`marca`**: Nome da Marca do Produto / Provedor (*Ex: COFAP, NAKATA, PERFECT*).
- **`codigo`**: Código específico da peça no catálogo (*Ex: HF87A, BD5602, TN3906*). Essencial para diferenciar variações de uma mesma família de peças.
- **`veiculo`**: Nome da Montadora (*Ex: VW, FIAT, CITROEN*).
- **`modelo`**: Nome do Veículo / Carro (*Ex: GOL, UNO, XANTIA*).
- **`versao`**: Versão do Modelo (*Ex: 1.6 16V, GLX*).

> [!IMPORTANT]
> Provedores baseados em GraphQL (Fraga) herdam essa formatação automaticamente de `GraphQLProvider`. Evite sobrescrever `formatar_resultado` em subclasses para prevenir desalinhamentos.

### Padronização de Dados (Cópia)
- **Referências:** Devem ser enviadas no formato `Marca: Código`.
- **Separação:** Itens separados por ` | `. Isso permite que a função de cópia centralizada agrupe os números originais no final da colagem (`ORIGINAL:`).

## 3. Manutenção e Resiliência

### Scraper Sentinel
- Scrapers (como o `DSProvider`) são sensíveis a mudanças de layout.
- **Protocolo:** Se a busca falhar, verifique o seletor `container` (ex: `.jq-apps tr`).
- **Update:** Altere o mapeamento via interface (`ProvedorForm`) antes de mexer no código Python.

### Melhores Práticas
- **Tokens:** Nunca salve tokens no código; use cache em memória/DB.
- **Frontend:** Garanta que os estados do formulário nunca sejam `null` para evitar warnings de inputs controlados.
