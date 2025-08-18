import typer
import redis
import json
from rich_console import Console

r = redis.Redis(host='localhost', port=6379, decode_responses=True)
QUEUE_NAME = 'task_queue'

app = typer.Typer()
console = Console()

@app.command()
def enqueue(task_name:str, args_json:str = '{}'):
    """
    Enfileira uma nova tarefa no Redis.

    Exemplos de uso:
    
    python cli.py enqueue send_email '{"email": "mentor@techlead.com", "message": "Vamos começar!"}'

    python cli.py enqueue generate_report '{"report_type": "vendas_mensal", "filters": {"ano": 2025}}'
    """
    try:
        kwargs = json.loads(args_json)

        task_payload = {
            "task_name":task_name,
            "args": [],
            "kwargs": kwargs
        }

        task_json = json.dumps(task_payload)
        r.rpush(QUEUE_NAME, task_json)

        console.print(f"[bold green]✅ Tarefa '{task_name}' enfileirada com sucesso![/bold green]")
        console.print(f" Payload: [cyan]{task_json}[/cyan]")

    except json.JSONDecodeError:
        console.print("[bold red]❌ Erro: O texto de argumentos fornecido não é um JSON válido.[/bold red]")
    except redis.exceptions.RedisError as e:
        console.print(f"[bold red]🚨 Erro de conexão com o Redis: {e}[/bold red]")
    except Exception as e:
        console.print(f"[bold red]🔥 Ocorreu um erro inesperado: {e}[/bold red]")
    
if __name__ == "__main__":
    app()