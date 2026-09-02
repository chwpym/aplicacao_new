---
name: catalog-integration-workflow
description: Fluxo mestre para integração total de novos provedores de catálogo em todas as camadas (Back, Front e Docs).
---

# 🚀 Fluxo de Integração Total de Catálogos

Este documento define o processo obrigatório para adicionar uma nova marca ao sistema, dividido em duas fases para garantir a qualidade dos dados.

## 🏁 Fase 1: Homologação Técnica (Apenas Backend)
Nesta fase, o provedor é adicionado apenas ao "coração" do sistema para teste real.

1.  **Backend:** Criar a classe em `backend/app/providers/nome_da_marca_provider.py`.
2.  **Registro:** Adicionar o tipo no `backend/app/providers/provider_factory.py`.
3.  **Banco de Dados:** Inserir a marca na tabela `provedores` do `backend/catalogo.db` (pode ser via script de seed ou comando SQL).
4.  **Validação Visual (USER):** O desenvolvedor deve avisar o usuário que a marca está pronta para teste na **Busca Principal**. O usuário verificará se os dados estão caindo nas colunas corretas (Montadora, Veículo, Motor, etc.).

---

## 🛠️ Fase 2: Integração Total (UI e Docs)
**Somente após o usuário confirmar que a busca está correta**, realizamos as mudanças no resto do sistema para garantir uma experiência premium:

1.  **Frontend Form:** Adicionar o novo tipo no `<select>` do `frontend_new/src/components/ProvedorForm.tsx`.
2.  **Frontend Playground:** Adicionar o tipo na constante `API_OPTIONS` em `frontend_new/src/pages/Playground.tsx`. O sistema cuidará da **ordenação automática (A-Z)**.
3.  **Clipboard:** Atualizar `frontend_new/src/utils/clipboard.ts` para incluir o bloco de **Ficha Técnica** específico da marca no final do texto copiado.
4.  **Documentação Técnica (Skill):** Criar uma Skill específica em `.agent/skills/marca-integration` detalhando os padrões de extração (labels usados, regex de anos, tratamento de motorização).

---

## ✅ Palavra-Chave de Finalização
Quando **TODOS** os passos da Fase 1 e Fase 2 forem concluídos e o sistema estiver 100% sincronizado, escreva:

> **`INTEGRACAO_CATALOGO_CONCLUIDA_COM_SUCESSO`**

---

## 💡 Regras de Ouro
- **Fase 1 Primeiro:** Nunca altere o formulário ou o playground antes de validar a busca no backend.
- **Normalização:** Se os dados estiverem em colunas erradas, ajuste o `formatar_resultado` na classe Python do provedor.
- **Nomes:** Use `(Nativo)` no select do frontend para passar confiança.
- **🛡️ PROTEÇÃO DO BASE PROVIDER:** **NUNCA** modifique o arquivo `backend/app/providers/base_provider.py` sem autorização explícita do usuário. Qualquer alteração sugerida deve vir acompanhada de uma explicação técnica detalhada de como essa mudança beneficia **TODOS** os provedores existentes e não causa regressões.
