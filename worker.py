import redis
import json
import tasks

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

QUEUE_NAME = 'task_queue'

AVAILABLE_TASKS = {
    "send_email": tasks.send_email,
    "generate_report": tasks.generate_report
}

def main():
    while True:
        try:
            _ , task_json = r.blpop(QUEUE_NAME)
            print(f"\n📥 Tarefa recebida: {task_json}")

            task_data = json.loads(task_json)
            task_name = task_data.get("task_name")
            task_args = task_data.get("args",[])
            task_kwargs = task_data.get("kwargs",{})

            func = AVAILABLE_TASKS.get(task_name)

            if func:
                print(f"🏃 Executando '{task_name}' com args={task_args}, kwargs={task_kwargs}")
                result = func(*task_args, **task_kwargs)
                print(f"✅ Tarefa '{task_name}' concluída com sucesso. Resultado: {result}")
            else:
                print(f"❌ Tarefa '{task_name}' não reconhecida.")
        except redis.exceptions.ConnectionError as e:
            print(f"🚨 Erro de conexão com o Redis: {e}. Tentando reconectar em 5 segundos...")
            time.sleep(5)
        except Exception as e:
            print(f"🔥 Ocorreu um erro inesperado ao processar a tarefa: {e}")
  
if __name__ == "__main__":
  main()