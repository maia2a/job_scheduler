import redis
import json

import redis.exceptions
import tasks
import time
import logging
import signal
import sys
from typing import Any, Dict, Optional, Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

QUEUE_NAME = 'task_queue'

AVAILABLE_TASKS = {
    "send_email": tasks.send_email,
    "generate_report": tasks.generate_report
}

def make_redis_client() -> redis.Redis:
    return redis.Redis(host='localhost', port=6379, decode_responses=True)

running = True

def handle_signal(signum, frame):
    global running
    logger.info("Sinal recebido (%s). Encerrando worker...", signum)
    running = False

signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

def process_task(task_json: str) -> None:
    try:
        logger.info(f"📥 Tarefa recebida: %s", task_json)
        task_data: Dict[str, Any] = json.loads(task_json)
        
        if not isinstance(task_data, dict):
            logger.error("Payload inválido: não é um objeto JSON")
            return
        
        task_name = task_data.get("task_name")
        task_args = task_data.get("args", [])
        task_kwargs = task_data.get("kwargs", {})
        
        func = AVAILABLE_TASKS.get(task_name)
        if not func:
            logger.error("❌ Tarefa '%s' não reconhecida.", task_name)
            return
        
        logger.info("🏃 Executando '%s' com args=%s, kwargs=%s", task_name, task_args, task_kwargs)
        result = func(*task_args, **task_kwargs)
        logger.info("✅ Tarefa '%s' concluída com sucesso. Resultado: %s", task_name, result)
        
    except Exception:
        logger.exception("🔥 Ocorreu um erro inesperado ao processar a tarefa.")

def main():
    client = make_redis_client()
    backoff = 1.0
    max_backoff = 30.0
    
    while running:
        try:
            item: Optional[Tuple[str, str]] = client.blpop(QUEUE_NAME, timeout=5)
            if item is None:
                continue
            
            _, task_json = item
            process_task(task_json)
            
            backoff = 1.0  # Reset backoff on success
        except redis.exceptions.ConnectionError as e:
            logger.warning("🚨 Erro de conexão com o Redis: %s. Reconectando em ~%s segundos...",e,backoff)
            time.sleep(backoff)
            backoff = min(max_backoff, backoff * 2)
            client = make_redis_client()
        except Exception:
            logger.exception("Erro inesperado no loop do worker")
            time.sleep(1)
    
    logger.info("Worker encerrado.")
    try:
        client.close()
    except Exception:
        pass
           
  
if __name__ == "__main__":
  main()