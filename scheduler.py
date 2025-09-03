from ast import main
import time
import json
import logging
import os
from datetime import datetime

import redis
from croniter import croniter

import database as db

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
QUEUE_NAME = "task_queue"
SLEEP_INTERVAL = 10

def get_due_jobs():
  """
  Busca os jobs para os quais o cron schedule indica que devem ser executados agora.
  Retorna uma lista de dicionários com os detalhes dos jobs.
  """
  now = datetime.now()
  query = """
    SELECT * FROM jobs
    WHERE next_run_at <= %s
      AND is_active = TRUE
  """
  try:
    due_jobs = db.fetch_all(query, (now,))
    return due_jobs
  except Exception as e:
    logging.error(f"Erro ao buscar jobs: {e}")
    return []

def enqueue_job(redis_conn, job):
  """Enfileira um job no Redis."""
  try:
    task_payload = job['payload']
    if isinstance(task_payload.get('kwargs'),dict):
      task_payload['kwargs'] = json.dumps(task_payload['kwargs'])
      
    redis_conn.rpush(QUEUE_NAME, json.dumps(task_payload))
    logging.info(f"Job {job['id']} enfileirado com payload: {task_payload}")
    return True
  except Exception as e:
    logging.error(f"Erro ao enfileirar job {job['id']}: {e}")
    return False
  
def update_job_schedule(job):
  """
    Atualiza o last_run_at e calcula o próximo next_run_at para o job.
    """
  now = datetime.now()
  try:
    cron = croniter(job['cron_schedule'], job['last_run_at'] or now)
    next_run = cron.get_next(datetime)
    query = """
      UPDATE jobs
      SET last_run_at = %s, next_run_at = %s
      WHERE id = %s
    """
    db.execute(query, (now, next_run, job['id']))
    logging.info(f"Job {job['id']} atualizado: last_run_at={now}, next_run_at={next_run}")
  except Exception as e:
    logging.error(f"Erro ao atualizar job {job['id']}: {e}")

def main_loop():
  """Loop principal do scheduler."""
  logging.info("🚀 Scheduler iniciado. Verificando jobs a cada %s segundos.", SLEEP_INTERVAL)
  
  redis_conn = redis.Redis(host=REDIS_HOST)
  
  while True:
    due_jobs = get_due_jobs()
    
    for job in due_jobs:
      if enqueue_job(redis_conn, job):
        update_job_schedule(job)
    
    time.sleep(SLEEP_INTERVAL)
    
if __name__ == "__main__":
  try:
    db.init_pool()
    main_loop()
  except KeyboardInterrupt:
    logging.info("Scheduler interrompido pelo usuário.")
  except Exception as e:
    logging.error(f"Erro inesperado: {e}")
  finally:
    db.close_pool()
    logging.info("Conexões com o banco de dados fechadas.")
  
  
  
  