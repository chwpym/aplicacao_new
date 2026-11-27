---
name: provider-lifecycle-management
description: Diretrizes de ciclo de vida, persistência e governança de provedores em nuvem (Render) vs. local (Seed Automático).
---

# Provider Lifecycle Management (Ciclo de Vida de Provedores)

Esta skill documenta a governança, o ciclo de vida e os procedimentos operacionais para criação, edição, remoção e persistência de provedores de dados no Catálogo V4, garantindo resiliência total contra perda de dados em ambientes de nuvem efêmeros (como Render Web Services).

---

## 1. O Desafio: Armazenamento Efêmero na Nuvem (Render)

Em plataformas de hospedagem em nuvem como o Render (plano Web Service padrão sem disco persistente montado):
- O contêiner de execução é **efêmero**: cada novo deploy, restart manual ou período de inatividade zera o sistema de arquivos do container.
- Se você cadastrar, alterar ou excluir um provedor diretamente pela interface web em produção (`https://catalogo-frontend-6cez.onrender.com`), essa alteração é gravada no SQLite temporário do container.
- No próximo deploy ou reinício, o SQLite seria resetado caso dependêssemos apenas da instância em execução.

---

## 2. A Solução: Arquitetura de Seed Automático e Fonte da Verdade

Para eliminar qualquer risco de perda e dispensar a necessidade de versionar arquivos binários pesados (`.db`), a arquitetura adota **`backend/app/data/initial_seed.json`** como a **Fonte Única da Verdade**.

### Como funciona o Auto-Seed:
1. **Inicialização do Backend (`backend/app/main.py`)**:
   - O FastAPI cria as tabelas via SQLAlchemy (`Base.metadata.create_all`).
   - O módulo `backend/app/db_seed.py` verifica se a tabela `provedores` possui registros.
   - Se a contagem for zero (banco novo ou reiniciado no container da nuvem), ele executa `auto_seed_db(db)` automaticamente.
   - Em menos de 50 milissegundos, todos os 64 provedores, 46 siglas, 207 palavras de limpeza e presets de imagem são carregados e indexados.

2. **Repositório Git Limpo**:
   - O arquivo binário `catalogo.db` **NÃO** é commitado no Git (ignorado por `*.db` no `.gitignore`).
   - Evita conflitos de mesclagem binária entre branches `develop` e `main`.
   - O JSON estruturado é 100% versionável, auditável por diff e legível por humanos e robôs.

---

## 3. Fluxos Operacionais (Passo a Passo)

### Cenário A: Adicionando ou Editando Provedores no Ambiente Local (Recomendado)
1. Inicie o sistema localmente (Backend na porta 8000, Frontend na 5173).
2. Acesse a tela de **Provedores** e crie ou edite o provedor desejado.
3. Exporte o estado atualizado para o seed:
   ```bash
   python -c "from app.database import SessionLocal; from app.db_seed import export_database_state; import json; db=SessionLocal(); data=export_database_state(db); open('backend/app/data/initial_seed.json', 'w', encoding='utf-8').write(json.dumps(data, indent=2, ensure_ascii=False))"
   ```
   *(Ou clique no botão **Exportar Backup JSON** na interface e salve como `backend/app/data/initial_seed.json`)*.
4. Faça o commit e push na branch `develop`:
   ```bash
   git add backend/app/data/initial_seed.json
   git commit -m "feat(provedores): adiciona novo provedor XYZ ao seed oficial"
   git push origin develop
   ```
5. Faça o merge para a `main` para publicar em produção:
   ```bash
   git checkout main
   git merge develop
   git push origin main
   git checkout develop
   ```
6. O Render fará o deploy automático e o novo provedor estará disponível permanentemente.

---

### Cenário B: Adicionando ou Editando Provedores Diretamente na Nuvem (Produção)
Se você ou um operador cadastrar ou alterar um provedor diretamente em produção (`catalogo-frontend-6cez.onrender.com`):

1. **Aviso na Interface**:
   - Um banner de alerta em âmbar no topo da tela de **Provedores** e uma nota explicativa dentro do formulário alertam que a alteração precisa ser exportada.
2. **Exportar Cópia de Segurança**:
   - Clique no botão **"📥 Exportar Backup JSON"** localizado no banner de aviso no topo da lista de provedores.
   - O navegador fará o download imediato de um arquivo como `catalogo_seed_backup_YYYY-MM-DD.json`.
3. **Persistir Permanentemente no Código**:
   - Copie esse arquivo para o repositório local substituindo `backend/app/data/initial_seed.json`.
   - Ou solicite ao assistente Antigravity: *"Atualize o initial_seed.json com este backup que exportei de produção"*.
   - Comite na `develop`, teste e faça merge para a `main`.

---

## 4. Endpoints de Governança de Provedores

A API do backend disponibiliza endpoints dedicados para backup e sincronização:

| Método | Endpoint | Descrição |
| :--- | :--- | :--- |
| `GET` | `/config/seed/export` | Retorna o JSON completo de todos os provedores, siglas, filtros e imagens do banco atual |
| `POST` | `/config/seed/import` | Substitui e sincroniza o banco de dados atual com o JSON enviado no payload |
| `POST` | `/config/seed/reload` | Força a restauração do banco a partir do `backend/app/data/initial_seed.json` |
| `POST` | `/config/backup/export` | Gera um snapshot completo em disco físico na pasta `backend/backups/` |

---

## 5. Boas Práticas e Checklist de Segurança
- [x] Nunca comitar credenciais sensíveis desnecessárias em provedores públicos;
- [x] Sempre testar novos provedores no **Playground** antes de ativá-los;
- [x] Verificar se o tipo do provedor (`graphql`, `rest`, `busca_na_rede`, `ds`, `reparadorvw`) possui classe implementada em `backend/app/providers/`;
- [x] Ao alterar provedores em produção, SEMPRE clicar em **Exportar Backup JSON** para não perder o trabalho.
