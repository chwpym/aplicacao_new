---
description: Como adicionar um novo provedor de catálogo (GraphQL ou REST)
---

# Fluxo para Adicionar Novo Provedor

Siga estas etapas para integrar uma nova fonte de dados ao sistema:

1. **Investigação Inicial:**
   - Descubra se o provedor usa **GraphQL** ou **REST**.
   - Verifique se o acesso é público ou exige login (Keycloak).

2. **Cadastro via Interface:**
   - Acesse a tela de **Configuração de Provedores**.
   - Clique em **Novo Provedor**.
   - Se for GraphQL, utilize o template automático.
   - Insira o nome oficial (ex: `AMPRI`, `NAKATA`).

3. **Configuração de Autenticação (Opcional):**
   - Caso exija login, marque **Requer Autenticação**.
   - Insira as credenciais. O sistema cuidará da limpeza de espaços e gestão de tokens JWT.

4. **Teste de Validação:**
   - Realize uma busca por um código de peça conhecido deste fabricante.
   - Verifique os logs do terminal para confirmar:
     - `[PROVEDOR] Login realizado via Bearer Token` (se houver login).
     - `[PROVEDOR] UUID encontrado` (sucesso no Discovery).

5. **Ajuste de Sigla (Se necessário):**
   - Se a marca retornar nomes diferentes (ex: `INDISA` vs `Indisa S.A`), cadastre uma nova **Sigla** nas configurações para unificar a visualização.
