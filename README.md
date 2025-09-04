# Orquestrador de Tarefas Distribuídas (Job Scheduler)

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

Sistema em Python para agendamento e execução de tarefas (jobs) de forma distribuída e tolerante a falhas. Projeto educativo/prático inspirado em soluções como Celery/Sidekiq.

Principais mudanças recentes

- CLI (cli.py): aceita JSON passado em uma única string, aceita múltiplos tokens (junta automaticamente) e também suporta `--file / -f payload.json`.
- Worker (worker.py): conexão resiliente com Redis (backoff), shutdown gracioso por sinais, logging estruturado e tratamento de exceções.
- Scheduler (scheduler.py): agora lê jobs do PostgreSQL, enfileira no Redis, atualiza next_run_at com `croniter`, usa db.init_pool/close_pool para o pool de conexões.
- Database (database.py): pool (ThreadedConnectionPool) com retries, context manager para conexões, helpers execute/fetch_one/fetch_all.
- Docker: docker-compose atualizado para desenvolvimento com Redis + Postgres + serviços app/worker. Serviços leem variáveis via `.env` (REDIS*HOST/REDIS_PORT, DB*\*).

Conteúdo

- cli.py — interface Typer para enfileirar tarefas e gerenciar o sistema.
- worker.py — consome a fila Redis e executa tasks em tasks.py.
- scheduler.py — agendador que lê jobs do Postgres e enfileira conforme cron.
- database.py — helpers e pool para Postgres.
- tasks.py — implementações de tarefas (send_email, generate_report).
- docker-compose.yml — ambiente Dev (Redis + Postgres + app/worker).
- requirements.txt — dependências Python.

Pré-requisitos

- Git
- Python 3.10+
- Docker & Docker Compose (opcional: Homebrew para instalar Redis/Postgres localmente)
- No macOS/fish: atenção ao ativar venv (veja nota abaixo)

Exemplo de .env (crie na raiz)

```env
# filepath: /Users/biellgm_/projects/job_scheduler/.env
REDIS_HOST=redis
REDIS_PORT=6379

DB_NAME=scheduler_db
DB_USER=admin
DB_PASSWORD=admin
DB_HOST=postgres
DB_PORT=5432

QUEUE_NAME=task_queue
SLEEP_INTERVAL=10
```

Instalação local (sem Docker)

1. Criar e ativar venv

- macOS (bash/zsh):

```bash
python3 -m venv venv
source venv/bin/activate
```

- fish (atenção à sintaxe):

```fish
python3 -m venv venv
# ative com o script para fish
source venv/bin/activate.fish
```

2. Instalar dependências

```bash
pip install -r requirements.txt
# se usar psycopg2 sem binário:
# pip install psycopg2-binary
```

3. Iniciar infra (opções)

- Docker Compose (recomendado para dev):

```bash
docker compose up --build -d
```

- Local (Homebrew):

```bash
brew install redis postgresql
brew services start redis
brew services start postgresql
# inicialize DB e credenciais conforme .env
```

Inicializar banco (uma vez)

```bash
# o módulo database.py tem init_db() quando executado diretamente
python3 database.py
```

Executando localmente

- Iniciar Worker:

```bash
python3 worker.py
```

- Iniciar Scheduler:

```bash
python3 scheduler.py
```

- Enfileirar tarefas via CLI (exemplos válidos)
  - JSON em uma linha (recomendado):
  ```bash
  python3 cli.py enqueue send_email '{"email":"junior.dev@empresa.com","message":"Sua primeira tarefa distribuída!"}'
  ```
  - Forçar resto como único argumento (útil quando o shell quebra tokens):
  ```bash
  python3 cli.py enqueue send_email -- '{"email":"junior.dev@empresa.com","message":"..."}'
  ```
  - Usar arquivo JSON (multilinha):
  ```bash
  python3 cli.py enqueue send_email -f payload.json
  ```
  Observações:
  - A CLI aceita múltiplos tokens para o JSON e junta-os caso você quebre linhas inadvertidamente.
  - A CLI valida que kwargs sejam um objeto JSON (dict). Mensagens de erro são mais informativas agora.

Executando com Docker Compose

- Subir tudo:

```bash
docker compose up --build -d
```

- Rodar o worker via compose:

```bash
docker compose up --build worker
```

- Usar a CLI dentro do container (mantém variáveis de ambiente do compose):

```bash
docker compose run --rm scheduler python3 cli.py enqueue send_email '{"email":"a@b.com","message":"Oi"}'
```

Boas práticas e observações

- O código agora lê REDIS*HOST/REDIS_PORT e DB*\* via env — garanta que `.env` esteja correto ao usar Docker Compose.
- Em desenvolvimento no macOS, monte o volume com :delegated para melhor desempenho (configurado no docker-compose recomendado).
- Para produção, use imagens imutáveis (não monte o código) e gerencie segredos com mecanismos seguros.
- Os serviços implementam reconexão com backoff (worker/scheduler) — designs tolerantes a falhas por intenção.
- Para testes e desenvolvimento reduza parâmetros pesados (ex.: total_iterations) em tasks.generate_report.

Dependências principais (exemplo requirements.txt)

```
redis
typer[all]
rich
croniter
psycopg2-binary
```

Contribuição e roadmap

- Veja o roadmap no final do README original: HA, leader election, distributed locks, heartbeat, métricas e dashboard são próximos itens do projeto.

Licença
MIT — consulte LICENSE.

Se quiser, atualizo o docker-compose.yml e requirements.txt no repositório para refletir estas
