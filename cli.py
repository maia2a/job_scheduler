import typer
import redis
import json
from rich.console import Console
from typing import Optional, List
from pathlib import Path

r = redis.Redis(host='localhost', port=6379, decode_responses=True)
QUEUE_NAME = 'task_queue'

app = typer.Typer()
console = Console()

@app.command()
def enqueue(task_name:str, args_json: Optional[str]=typer.Argument(None), file: Optional[Path]=typer.Option(None, "--file", "-f", help="Caminho para um arquivo JSON com kwargs")):
    """
    Enfileira uma nova tarefa no Redis.

    Exemplos:
      python3 cli.py enqueue send_email '{"email":"a@b.com","message":"Oi"}'
      python3 cli.py enqueue send_email -- '{"email":"a@b.com","message":"Oi"}'
      python3 cli.py enqueue send_email -f payload.json
    """
     
    try:
        if file:
            if not file.exists():
                console.print(f"[bold red]❌ Arquivo não encontrado: {file}[/bold red]")
                raise typer.Exit(code=1)
            json_text = file.read_text()
        else:
            json_text = "{}" if not args_json else " ".join(args_json)
        
        kwargs = json.loads(json_text)
        
        if not isinstance(kwargs, dict):
            console.print("[bold red]❌ Erro: Os argumentos fornecidos devem ser um objeto JSON (dicionário).[/bold red]")
            raise typer.Exit(code=1)

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