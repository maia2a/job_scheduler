# Orquestrador de Tarefas Distribuídas (Job Scheduler)

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

Um sistema de backend distribuído, construído em Python, para agendamento e execução de tarefas (jobs) de forma confiável e tolerante a falhas. O projeto é inspirado em sistemas como Celery e Sidekiq, focado em demonstrar conceitos avançados de engenharia de software.

## Problema Solucionado

Empresas frequentemente precisam executar tarefas em background que são essenciais, mas não devem travar a experiência do usuário: enviar emails de marketing à meia-noite, gerar relatórios complexos a cada 6 horas, fazer backups de bancos de dados diariamente, etc. Este sistema fornece uma plataforma robusta para que desenvolvedores possam agendar essas tarefas com a garantia de que elas serão executadas na hora certa e de forma confiável, mesmo que servidores falhem.

## Principais Recursos Técnicos

- ✅ **Execução Distribuída:** Múltiplos workers podem ser executados em paralelo em diferentes máquinas ou contêineres para processar a fila de tarefas.
- ✅ **Agendamento de Tarefas:** Jobs podem ser configurados para executar em horários específicos ou em intervalos recorrentes (ex: CRON jobs).
- ✅ **Tolerância a Falhas:** Mecanismos como heartbeats e locks distribuídos garantem que a falha de um worker não resulte na perda de uma tarefa.
- ✅ **Garantias de Execução:** Implementação de estratégias como "at least once" para assegurar a execução de tarefas críticas.
- ✅ **Alta Disponibilidade (HA) do Scheduler:** Um mecanismo de eleição de líder (Leader Election) previne que múltiplos schedulers dupliquem tarefas.
- ✅ **Interface de Linha de Comando (CLI):** Uma CLI robusta para submeter novos jobs, verificar status e gerenciar o sistema.

## Arquitetura do Sistema

O sistema é composto por múltiplos componentes desacoplados que se comunicam através de um broker de mensagens e um banco de dados, seguindo padrões de arquitetura de microsserviços.

![Diagrama da Arquitetura](https://i.imgur.com/iY9A6kY.png)

1.  **CLI (Cliente)**: Interface para o usuário definir e agendar jobs.
2.  **Banco de Dados (PostgreSQL)**: Persiste as definições dos jobs, o histórico de execuções e os resultados.
3.  **Scheduler (Agendador)**: O cérebro do sistema. Lê as definições do banco de dados, determina quais jobs devem ser executados e os enfileira no broker.
4.  **Broker (Redis)**: Atua como a fila de tarefas, garantindo a comunicação assíncrona entre o Scheduler e os Workers.
5.  **Workers (Trabalhadores)**: Consomem as tarefas da fila, executam a lógica de negócio e reportam o resultado.

## Tech Stack

| Componente               | Tecnologia                                  |
| ------------------------ | ------------------------------------------- |
| **Linguagem**            | Python 3.10+ (com `asyncio`)                |
| **Banco de Dados**       | PostgreSQL                                  |
| **Broker de Mensagens**  | Redis                                       |
| **Comunicação Direta**   | gRPC (para controle do Scheduler -> Worker) |
| **CLI Framework**        | Typer                                       |
| **Ambiente de Execução** | Docker & Docker Compose                     |

## Começando (Getting Started)

Siga os passos abaixo para executar o projeto em seu ambiente local.

### Pré-requisitos

- Git
- Python 3.10 ou superior
- Docker e Docker Compose

### Instalação

1.  **Clone o repositório:**

    ```bash
    git clone <URL_DO_SEU_REPOSITORIO>
    cd job_scheduler
    ```

2.  **Crie e ative o ambiente virtual:**

    ```bash
    python -m venv venv
    source venv/bin/activate
    # No Windows: venv\Scripts\activate
    ```

3.  **Instale as dependências Python:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Inicie os serviços de infraestrutura (Redis & Postgres):**
    Crie um arquivo `docker-compose.yml` na raiz do projeto com o seguinte conteúdo:

    ```yaml
    version: "3.8"
    services:
      redis:
        image: "redis:7-alpine"
        ports:
          - "6379:6379"
        volumes:
          - redis_data:/data

      # Adicionaremos o Postgres em fases futuras
      # postgres:
      #   image: postgres:15-alpine
      #   environment:
      #     - POSTGRES_USER=admin
      #     - POSTGRES_PASSWORD=admin
      #     - POSTGRES_DB=scheduler_db
      #   ports:
      #     - "5432:5432"
      #   volumes:
      #     - postgres_data:/var/lib/postgresql/data

    volumes:
      redis_data:
      # postgres_data:
    ```

    Agora, inicie os containers com um único comando:

    ```bash
    docker-compose up -d
    ```

### Execução

1.  **Inicie um Worker:**
    Abra um terminal, ative o ambiente virtual e execute:

    ```bash
    python worker.py
    ```

    O worker ficará aguardando por novas tarefas.

2.  **Enfileire uma Tarefa via CLI:**
    Abra um **segundo terminal**, ative o ambiente virtual e use a CLI para enviar uma tarefa:

    ```bash
    # Exemplo 1: Enviar um email
    python cli.py enqueue send_email '{"email": "exemplo@email.com", "message": "Olá, Mundo!"}'

    # Exemplo 2: Gerar um relatório
    python cli.py enqueue generate_report '{"report_type": "vendas_Q3", "filters": {}}'
    ```

    Observe o primeiro terminal para ver o worker processando a tarefa em tempo real.

## Estrutura do Projeto

```
.
├── venv/                 # Ambiente virtual Python
├── cli.py                # Implementação da Interface de Linha de Comando
├── worker.py             # Lógica do worker para processar tarefas
├── tasks.py              # Definições das tarefas executáveis
├── scheduler.py          # (Futuro) Lógica do serviço de agendamento
├── requirements.txt      # Dependências Python
└── docker-compose.yml    # Definição dos serviços de infraestrutura
```

## Roadmap do Projeto

- [x] **Fase 1: Esqueleto Funcional (MVP)**
  - [x] Comunicação via Redis entre CLI e Worker.
  - [x] Execução de tarefas simples.
- [ ] **Fase 2: Persistência e Agendamento**
  - [ ] Integração com PostgreSQL.
  - [ ] Implementação do serviço do Scheduler para ler do DB e enfileirar tarefas.
  - [ ] CLI para criar/atualizar definições de jobs no DB.
- [ ] **Fase 3: Tolerância a Falhas**
  - [ ] Implementação de distributed locks (Redis `SETNX`) para evitar dupla execução.
  - [ ] Mecanismo de heartbeat/timeout para detectar workers mortos e re-enfileirar tarefas.
- [ ] **Fase 4: Alta Disponibilidade (HA)**
  - [ ] Implementação de Leader Election para o Scheduler.
- [ ] **Fase 5: Funcionalidades Avançadas**
  - [ ] Comunicação via gRPC para cancelamento de tarefas.
  - [ ] Dashboard web simples para visualização.

## Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.
