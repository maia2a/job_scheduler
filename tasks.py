import time
import random

def send_email(email:str, message:str):
  print(f"Preparando para enviar email para {email} com a mensagem: {message}")
  time.sleep(random.uniform(0.5, 2.0))  # Simula o tempo de envio do email
  print(f"Email enviado para {email} com a mensagem: {message}")
  return {"status": "success", "recipient": email}

def generate_report(report_type:str, filters:dict):
  print(f"Iniciando a geração do relatório do tipo {report_type} com filtros {filters}")
  total_iterations = 200_000_000
  for i in range(total_iterations):
    if i % (total_iterations // 4) == 0:
      print(f"Progresso do relatório: {(i/total_iterations) * 100:.0f}%")
  time.sleep(random.uniform(2,4))
  print(f"Relatório do tipo {report_type} gerado com sucesso.")
  return {"status": "success", "report_type": report_type, "row": random.randint(100, 1000)}
  