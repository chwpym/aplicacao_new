# Changelog - Gerenciador de Peças

## [1.2.0] - 2026-07-29
### Adicionado
- Título dinâmico nas abas do navegador para facilitar a diferenciação de abas simultâneas:
  - Título padrão ajustado de `frontend_new` para `Catálogo V4`.
  - Na tela Workspace (Home), o título agora exibe `Workspace - [Nome do Provedor]` caso um provedor específico esteja selecionado, ou `Workspace - Catálogo V4` para buscas gerais.
  - Na tela Playground, o título exibe `Playground - [Nome do Provedor]` conforme a API/template ativa em teste.
  - Nas telas secundárias (Siglas, Provedores, Configurações, etc.), os títulos agora refletem o nome da respectiva funcionalidade.
- Rodapé da Sidebar dinâmico:
  - Substituído o ano estático `2024` por renderização dinâmica usando o ano corrente (`new Date().getFullYear()`), mantendo a data do sistema sempre atualizada.
- Exibição de Data Corrente na Sidebar:
  - Adicionado campo dinâmico `Hoje: DD/MM/AAAA` no cabeçalho da sidebar (abaixo de "Gerenciador de Peças").
- Limpeza e Padronização do Perfil da Sidebar:
  - Removido o termo `Estoque Original` e atualizado as informações do perfil do rodapé para exibir `Administrador` como título e `Catalogo V4` como subtítulo, simplificando a interface para futuros cadastros.
  - Alterado o avatar para `AD` (Administrador).

## [1.1.0] - 2026-02-02
### Adicionado
- Script de inicialização automática `start.bat` e `start.ps1`.
- Suporte a múltiplas imagens na galeria de resultados.
- Extração de colunas "Combustível" e "Observações" no robô DS.
- Sistema de documentação via README e Skills.
- Inclusão de Skills para Desenvolvimento de Provedores e Lógica de Frontend.
- Criação da pasta `debug_analysis` para organizar rascunhos e dumps de HTML.
- Adição de arquivo `.gitignore` para preparação de versionamento.

### Corrigido
- Bug no `DSProvider` que causava `AttributeError` ao processar anos.
- Formatação de anos: agora converte `01 > 06` para `2001 ... 2006` corretamente.
- Labels da interface: "Config. Motor" alterado para "Combustível" para maior clareza.
- Cópia para Clipboard: corrigido o agrupamento de referências originais (formato `Marca: Código`).
- Mapeamento automático no `ProvedorForm` para o tipo DS.

## [1.0.0] - 2026-01-31
### Lançamento Inicial
- Integração básica com GraphQL e REST.
- Sistema de busca unificada por Part ID.
- Primeiro robô scraper (Site DS).
