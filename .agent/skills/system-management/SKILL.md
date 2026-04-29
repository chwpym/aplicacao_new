# System Management & Monitoring

Esta skill detalha os procedimentos de monitoramento, backup e recuperação do sistema de catálogos.

## 1. Monitoramento via Logs
Os logs do sistema são gravados em `backend/logs/app.log`.

### Como ler os logs:
- **[SCRAPER]**: Erros ou informações sobre a busca nos sites (ex: TSA, DS).
- **[NORMALIZATION]**: Detalhes sobre a correção de marcas e modelos (ex: FOX -> VW).
- **[DATABASE]**: Status de conexão e inicialização do banco de dados local.
- **[FIPE_API]**: Status da sincronização com a BrasilAPI.

> [!TIP]
> Em caso de comportamento estranho, verifique as últimas linhas do arquivo para ver se houve erro `[ERRO]` ou aviso `[AVISO]`.

## 2. Sistema de Backup (Exportação)
Para garantir que você nunca perca seus provedores ou o catálogo corrigido, realize backups periódicos.

### Como realizar um backup:
Abra o terminal na pasta `backend` e rode:
```powershell
python scripts/export_system_state.py
```
Os dados serão salvos em uma pasta dentro de `backend/backups/`.

## 3. Sistema de Recuperação (Importação)
Se você precisar restaurar o sistema ou migrar para outro PC:

### Como restaurar um backup:
Abra o terminal na pasta `backend` e rode:
```powershell
python scripts/import_system_state.py backups/backup_YYYYMMDD_HHMMSS
```
*(Substitua pelo nome da pasta do backup desejado)*.

> [!CAUTION]
> A restauração irá sobrescrever as configurações atuais pelas configurações contidas no backup.

## 4. Estrutura de Backup (JSON)
Os backups são salvos em formato JSON para que você possa inspecioná-los manualmente:
- `sql_configs.json`: Contém Provedores, Siglas e Palavras para remover.
- `fipe_catalog.json`: Contém o banco de dados oficial de Marcas e Modelos.
