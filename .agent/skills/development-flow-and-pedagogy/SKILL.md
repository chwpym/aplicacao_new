---
name: development-flow-and-pedagogy
description: Diretrizes de documentação de alterações em entregas, versionamento estruturado e comunicação pedagógica didática em Português.
---

# Fluxo de Desenvolvimento e Aprendizado (Pedagogia e Documentação)

Esta skill estabelece as regras e diretrizes institucionais para que todo agente de inteligência artificial que atue no projeto documente suas alterações, realize o versionamento de forma limpa e se comunique com o usuário de forma altamente didática, transparente e pedagógica em **Português**.

---

## 1. Didática em Primeiro Lugar (Comunicação)

A prioridade absoluta do desenvolvimento é o **aprendizado do usuário**. 
* **Explicação Claro-Pedagógica:** O agente não deve apenas codificar a solução, mas explicar detalhadamente em português a lógica utilizada e a razão física por trás de cada decisão de engenharia de software.
* **Sem Termos Obscuros:** Conceitos complexos (ex: requisições concorrentes, handshake de cookies, buffers de memória) devem ser explicados de forma simples e visual.
* **Humildade Profissional:** Toda interação deve ser profissional, prestativa e humilde, evitando o uso de superlativos (como "código perfeito", "solução impecável").

---

## 2. Padrão de Documentação Física (Artefatos Locais)

Sempre que um agente realizar modificações ou ajustes estruturais nas chaves do projeto, ele **deve obrigatoriamente** criar ou atualizar dois artefatos físicos locais na pasta de contexto do usuário:

### A. O Checklist de Tarefas (`task.md`)
* Um documento Markdown que funciona como um quadro de controle (TODO List) para que o usuário veja visualmente o andamento.
* Deve usar as marcações:
  * `- [ ]` para tarefas não iniciadas.
  * `- [/]` para tarefas em andamento.
  * `- [x]` para tarefas totalmente concluídas.

### B. O Relatório de Entrega (`walkthrough.md`)
* Um documento Markdown contendo a explicação detalhada de toda a entrega física da fase.
* **Estrutura Obrigatória:**
  1. **Objetivo:** O que motivou a mudança ou ajuste.
  2. **🛠️ O que mudou e por quê:** Listagem de arquivos modificados/criados com sua respectiva justificativa técnica individual.
  3. **🔬 Resultados de Testes:** Amostras ou tabelas reais extraídas de scripts de validação (como `scratch/test_jahu_provider_run.py`) provando que o comportamento desejado foi atingido.

---

## 3. Didática Interna no Código (Comentários)

* Qualquer arquivo criado ou editado pelo agente **deve** conter comentários didáticos ricos, detalhados e em português diretamente nas linhas de código.
* Esses comentários devem guiar o usuário na leitura dos arquivos em seu próprio editor de código externo (como o **Sublime Text**), explicando o que cada bloco de lógica realiza.

---

## 4. Transparência por Links Clicáveis (Markdown File Links)

Como a interface do agente opera em segundo plano sem uma IDE integrada na tela do chat, para dar controle e visibilidade ao usuário:
* O agente **deve** utilizar links absolutos de arquivos em Markdown ao se referir a arquivos do projeto:
  * **Correto:** `[jahu_provider.py](file:///d:/Dev/aplicacao_new/backend/app/providers/jahu_provider.py)`
  * **Incorreto:** `` `jahu_provider.py` `` (nome cru sem link)
* Isso permite que o usuário, ao ler o chat, clique diretamente no link para abrir o arquivo em seu editor externo local instantaneamente.

---

## 5. Padrão de Versionamento e Entregas (Git)

Para manter o histórico do repositório limpo, legível e profissional:
1. **Adicionar Apenas Arquivos de Produção:** Evitar fazer `git add .` para não subir arquivos de teste temporários localizados no diretório `scratch/`. Adicione individualmente os arquivos modificados.
2. **Conventional Commits:** Escrever as mensagens de commit em português seguindo as regras de commits semânticos (Conventional Commits):
   * `feat(jahu): implementacao completa do provedor jahu` (funcionalidade nova)
   * `fix(imagens): correcao de captura de fotos concorrentes` (correção de bugs)
   * `docs(skills): adicao de skill didatica de integracao` (alterações na documentação)
3. **Push Seguro:** Após o commit, realizar o `git push` para o branch ativo (ex: `develop`) garantindo a sincronia com a equipe.
