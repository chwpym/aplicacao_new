---
name: change-documentation
description: Diretrizes e padrões para documentar alterações, atualizações e changelogs de componentes (Back, Front e Layout) de forma didática e estruturada.
---

# Documentação de Mudanças e Changelog

Esta skill define as melhores práticas, estruturas e regras para a documentação física de qualquer alteração realizada no repositório. Ela orienta o agente de IA e os desenvolvedores sobre como documentar desde pequenos ajustes de layout até grandes refatorações de código no Back e no Front, garantindo rastreabilidade, aprendizado contínuo e clareza absoluta para o usuário final.

---

## 1. Por que Documentar Mudanças?

Uma excelente documentação de mudanças assegura:
* **Transparência:** O usuário final entende exatamente o que mudou no comportamento da aplicação.
* **Manutenibilidade:** Futuros desenvolvedores ou agentes conseguem ler o histórico técnico sem depender de arqueologia de código.
* **Aprendizado Técnico:** A documentação serve como ferramenta pedagógica para demonstrar as decisões de engenharia, escolhas de design e correções de erros.

---

## 2. Tipos de Alterações e o que Documentar

Cada tipo de mudança requer atenção a detalhes específicos no momento de documentar:

### A. Ajustes de Layout e Frontend (CSS / Componentes React)
* **Mudança Estética/Estrutural:** Explique por que a estrutura anterior estava falha (ex: quebra de linha de botões, sobreposição de inputs, falta de espaço no celular) e qual técnica foi adotada (ex: CSS Grid responsivo, Flexbox,breakpoints customizados).
* **Grid e Alinhamentos:** Detalhe a matriz física do layout (ex: Grade de 4 colunas e 2 linhas) e sua lógica de empilhamento para aparelhos menores (`grid-cols-2 sm:grid-cols-4`).
* **Estilo e Cores:** Documente classes Tailwind ou tokens de cor utilizados (ex: `bg-orange-500/10`, `text-orange-600`, transições de hover e suporte a Dark Mode).

### B. Integrações de Provedores de Catálogo e Scraping
* **Fontes de Dados:** Documente a plataforma de origem (ex: Jahu, DS, WMW e-commerce) e o protocolo de extração (GraphQL, REST, HTML Scraping).
* **Mecanismos de Resiliência:** Explique como erros de rede, limites de caracteres e cookies de sessão expirados são tratados.
* **Normalização Automotiva:** Documente as regras aplicadas para padronizar anos, marcas, combustíveis e modelos (ex: conversão de "FLEX" para "FLEX / GASOLINA").

### C. Alinhamentos de Cópia e Clipboard (ERP e Whatsapp)
* **Lógicas de Cálculo Físico:** Documente o uso de cálculos de proporcionalidade de fonte (ex: Canvas 2D API em `clipboardTable.ts`) usados para computar o alinhamento de colunas em fontes não mono-espaçadas.
* **Configurações Especiais:** Detalhe opções como "Ocultar Divisórias (---)" e as razões físicas de sua existência (como evitar o encurtamento físico de hifens em fontes proporcionais do ERP).

---

## 3. Estrutura do Changelog (Histórico Físico)

Sempre que concluir um ciclo de entregas ou responder a um pedido de modificação do usuário, documente as novidades no arquivo [walkthrough.md](file:///C:/Users/Estoque_Original/.gemini/antigravity/brain/10de3936-56fe-45ed-b7a0-28c2bf7d5efa/walkthrough.md) ou no repositório central de documentação utilizando o seguinte padrão estruturado:

### Modelo Padrão de Entrada de Registro:

```markdown
### 🗓️ [DD/MM/AAAA] - [Título Conciso da Entrega]

#### 🚀 O que há de novo:
* **[Nome do Componente/Área]**: Breve explicação da funcionalidade adicionada de forma compreensível em português.

#### 🔧 Correções e Ajustes (Fixes):
* **[Área Afetada]**: Problema que ocorria -> Solução definitiva aplicada.

#### 🎨 Ajustes de Layout e UX:
* **[Componente Visual]**: Redesenho do elemento de interface explicando a nova estrutura de grid/flex e breakpoints.

#### 📂 Arquivos Modificados / Criados:
* ➕ [NOVO] [nome_do_arquivo.ts](file:///absolute/path/to/file.ts): O que o arquivo realiza.
* 📝 [MODIFY] [outro_arquivo.tsx](file:///absolute/path/to/other.tsx): Ajuste específico feito nas linhas X-Y.
```

---

## 4. Diretrizes Pedagógicas para Changelogs

Para garantir que o changelog atue como uma ferramenta pedagógica ativa para o usuário:

1. **Evite Jargão Seco:** Em vez de apenas escrever "fixed button styling using tailwind grid", explique:
   > *"Redesenhamos os botões em uma grade uniforme de 4 colunas e 2 linhas. Isso impede que o botão PDF seja empurrado sozinho para baixo quando a tela encolhe, mantendo os botões de cópia ordenadamente alinhados na linha inferior."*
2. **Use Recursos Visuais e Markdown:**
   * **Alertas GitHub:** Chame atenção para recursos novos ou configurações padrão que foram ativadas (ex: hifens desabilitados por padrão).
   * **Blocos de Código e Diffs:** Mostre de forma didática pequenos trechos do antes e depois de alterações críticas.
   * **Links Clicáveis:** Sempre use caminhos absolutos no formato `file:///` sem crases ao redor do link para facilitar a navegação local instantânea.
3. **Tom de Voz:** Humilde, preciso, profissional e focado no valor de negócios ou de uso diário do usuário.

---

## 5. Relação com Outras Skills

* **[development-flow-and-pedagogy](file:///d:/Dev/aplicacao_new/.agent/skills/development-flow-and-pedagogy/SKILL.md)**: Esta skill de documentação complementa o fluxo de desenvolvimento pedagógico, focando especificamente em *como formatar e explicar as mudanças realizadas no código e no layout*, enquanto a de pedagogia cuida das regras gerais de Git e interação humana.
* **[ui-ux-pro-max](file:///d:/Dev/aplicacao_new/.agent/skills/ui-ux-pro-max/SKILL.md)**: Use as terminologias e conceitos de UI/UX desta skill ao justificar decisões de design visual nos relatórios de entrega.
