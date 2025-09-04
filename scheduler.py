from ast import main
import time
import json
import logging
import os
import signal
from datetime import datetime
from typing import List, Dict, Any, Optional

import redis
from croniter import croniter

import database as db

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
QUEUE_NAME = os.getenv("QUEUE_NAME", "task_queue")
SLEEP_INTERVAL = int(os.getenv("SLEEP_INTERVAL", "10"))

running = True


def handle_signal(signum, frame):
    global running
    logger.info("Sinal recebido (%s). Encerrando scheduler...", signum)
    running = False


signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)


def make_redis_client() -> redis.Redis:
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


def get_due_jobs() -> List[Dict[str, Any]]:
    """
    Busca os jobs cujo next_run_at indica execução agora.
    """
    now = datetime.now()
    query = """
      SELECT * FROM jobs
      WHERE next_run_at <= %s
        AND is_active = TRUE
    """
    try:
        return db.fetch_all(query, (now,))
    except Exception as e:
        logger.error("Erro ao buscar jobs: %s", e)
        return []


def enqueue_job(redis_conn: redis.Redis, job: Dict[str, Any]) -> bool:
    """Enfileira um job no Redis. Retorna True se OK."""
    try:
        task_payload = job.get("payload") or {}
        # normaliza kwargs: se for string, tenta desserializar; se ausente, usa {}
        kwargs = task_payload.get("kwargs", {}) 
        if isinstance(kwargs, str):
            try:
                kwargs = json.loads(kwargs)
            except json.JSONDecodeError:
                logger.warning("Job %s: kwargs em string inválido JSON, usando {}.", job.get("id"))
                kwargs = {}
        if not isinstance(kwargs, dict):
            logger.warning("Job %s: kwargs não é um objeto, convertendo para {}.", job.get("id"))
            kwargs = {}

        task_payload["kwargs"] = kwargs
        # garante que args existe como lista
        task_payload.setdefault("args", [])

        redis_conn.rpush(QUEUE_NAME, json.dumps(task_payload))
        logger.info("Job %s enfileirado com payload: %s", job.get("id"), task_payload)
        return True
    except Exception as e:
        logger.error("Erro ao enfileirar job %s: %s", job.get("id"), e)
        return False


def update_job_schedule(job: Dict[str, Any]) -> None:
    """
    Atualiza last_run_at e next_run_at do job.
    """
    now = datetime.now()
    try:
        base = job.get("last_run_at") or now
        cron = croniter(job["cron_schedule"], base)
        next_run = cron.get_next(datetime)
        query = """
          UPDATE jobs
          SET last_run_at = %s, next_run_at = %s
          WHERE id = %s
        """
        db.execute(query, (now, next_run, job["id"]))
        logger.info("Job %s atualizado: last_run_at=%s next_run_at=%s", job["id"], now, next_run)
    except Exception as e:
        logger.error("Erro ao atualizar schedule do job %s: %s", job.get("id"), e)


def main_loop():
    logger.info("🚀 Scheduler iniciado. Verificando jobs a cada %s segundos.", SLEEP_INTERVAL)

    # tenta criar cliente Redis com backoff simples
    redis_client = None
    backoff = 1.0
    max_backoff = 30.0

    while running:
        if redis_client is None:
            try:
                redis_client = make_redis_client()
                # testa conexão
                redis_client.ping()
                backoff = 1.0
                logger.info("Conectado ao Redis em %s:%s", REDIS_HOST, REDIS_PORT)
            except Exception as e:
                logger.warning("Falha ao conectar Redis: %s. Retry em ~%s s", e, backoff)
                time.sleep(backoff)
                backoff = min(max_backoff, backoff * 2)
                continue

        try:
            due_jobs = get_due_jobs()
            for job in due_jobs:
                if not running:
                    break
                try:
                    ok = enqueue_job(redis_client, job)
                    if ok:
                        update_job_schedule(job)
                except Exception:
                    logger.exception("Erro ao processar job %s", job.get("id"))
            time.sleep(SLEEP_INTERVAL)
        except redis.exceptions.ConnectionError:
            logger.warning("Perda de conexão com Redis. Forçando reconectar...")
            redis_client = None
        except Exception:
            logger.exception("Erro inesperado no loop do scheduler. Aguardando antes de continuar...")
            time.sleep(1)

    logger.info("Scheduler finalizando.")


if __name__ == "__main__":
    try:
        db.init_pool()
        main_loop()
    except Exception:
        logger.exception("Scheduler encerrado por erro")
    finally:
        try:
            db.close_pool()
        except Exception:
            pass



