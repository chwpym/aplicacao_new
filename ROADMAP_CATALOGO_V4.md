# Catalogo V4 — Roadmap de Ideias e Evoluções

> Documento vivo com todas as ideias discutidas para futuras implementações.
> Última atualização: 2026-05-06

---

## 🔴 URGENTE (Próxima Sessão)

- [x] Estabilização do provedor "Busca na Rede" (Tuba, Sampel, TC Chicotes)
- [x] Parser resiliente via metadados (eliminando erros 500)
- [x] Filtro de colunas e limpeza de referências de marketing
- [x] Integração do provedor Japanparts (API REST nativa, 35 veículos/7 montadoras no FO313S)

---

## 🟡 CURTO PRAZO (Próximas 2-3 Sessões)

### 2. Destaque Visual + Ordenação por Relevância na Busca
- **Problema:** Quando busca "BIELETA ONIX", o ONIX aparece misturado no meio da lista
- **Solução (2 camadas):**
  - **Highlight:** Destacar o termo buscado (ex: "ONIX") com cor neon/amarela na tabela
  - **Ordenação inteligente:** Colocar no topo os resultados onde o veículo bate com o termo buscado, depois ordenar o restante alfabeticamente
- **Arquivos afetados:** Apenas frontend (tabela de resultados)
- **Estimativa:** 1-2 horas

### 3. Formatador de Texto "Selvagem" (Texto da Internet → Padrão do Sistema)
- **Problema:** Usuário copia texto bagunçado de WhatsApp/sites e precisa formatar manualmente
- **Solução:** Ferramenta no Playground que recebe texto livre e usa o NormalizationService + AutomakerService para separar em colunas (Carro, Motor, Ano, Montadora)
- **Arquivos afetados:** Nova página ou seção no Playground + endpoint no backend
- **Estimativa:** 2-3 horas

---

## 🟢 MÉDIO PRAZO (Versão 5)

### 4. Cache Permanente de Aplicações (Super Catálogo Local)
- **Problema:** Toda busca vai na internet, mesmo que já tenha sido feita antes
- **Solução:**
  - Salvar aplicações pesquisadas no SQLite existente
  - Chave primária: **MARCA_PECA + CÓDIGO** (nunca só código, pois Wega 123 ≠ Cobreq 123)
  - Salvar também a **descrição da peça** para consultas futuras
  - Tela de "Gestão de Cache" para visualizar, editar e excluir registros salvos
- **Desafios:**
  - Peças diferentes com mesmo código em marcas diferentes
  - Quando atualizar o cache? (Expiração por data ou manual)
  - Como lidar com peças que mudam aplicação ao longo do tempo
- **Arquitetura sugerida:** API de Enriquecimento isolada (não mexe no fluxo atual)
- **Estimativa:** 1-2 dias

### 5. Procura Inteligente (Padrão CERTTUS)
- **Referência:** Sistema CERTTUS (ERP de autopeças)
- **Cascata de busca (por ordem de prioridade):**
  1. Código Interno
  2. Código Fabricante
  3. Código Fabricante + Marca (tudo junto, ex: BB134025MWM)
  4. Marca (ex: MWM)
  5. Marca + Descrição (ex: MWM BRONZINA)
  6. Descrição (ex: BRONZINA BIELA 0,25)
  7. Aplicação (ex: MERCEDES BENZ OM352)
  8. Descrição + Aplicação (ex: BRONZINA OM352)
  9. Código de Barras
- **Pré-requisito:** Ter o Cache Permanente (item 4) funcionando
- **Estimativa:** 2-3 dias

### 6. Buscar Descrição de Peças em Todos os Provedores
- **Problema:** Hoje o sistema busca só por código. Para implementar a "Procura Inteligente", precisa saber o que a peça é (filtro, bieleta, bronzina, etc.)
- **Solução:**
  - Cada provedor passa a extrair o nome/descrição do produto durante o scraping
  - Armazenar no Cache Permanente (item 4)
  - Construir uma API isolada de consulta para não afetar o fluxo atual
- **Risco:** Pode deixar a busca mais lenta se não for bem planejado
- **Mitigação:** Construir fora do fluxo principal, como o usuário sugeriu — uma API separada só para consumir as informações enriquecidas
- **Estimativa:** 1-2 dias

---

## 📋 Regras para Implementação

1. **Nunca alterar arquivos Core** (NormalizationService, BaseProvider, SearchService, AutomakerService, text_service, synonyms.py) a menos que o benefício seja global para todos os provedores
2. **Problemas específicos de um provedor** → resolver no arquivo do provedor
3. **Testar sempre** com pelo menos 3 provedores diferentes antes de fazer commit
4. **Nome do sistema:** Catalogo V4 / Gerenciador de Peças (nunca Synergia OS)
5. **UI:** Nunca usar `alert()` ou `confirm()` nativos. Sempre Toast + ConfirmModal

---

## ✅ Concluídos (Sessão 2026-05-05)

- [x] Integração do provedor Autafastar (Discovery + Hydration)
- [x] Sistema de normalização de montadoras via JSON Mestre (FIPE)
- [x] Módulo "Biblioteca de Carros" para gestão manual
- [x] Sincronização automática com API FIPE/BrasilAPI
- [x] Regex de motorização aprimorado (motores múltiplos 1.0/1.3)
- [x] Sistema de Toasts Globais (substituindo alert)
- [x] ConfirmModal customizado (substituindo confirm)
- [x] Skill de Arquitetura Core documentada
