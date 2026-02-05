# Changelog - Gerenciador de Peças

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
