import time
import random
import logging
from typing import Callable, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

DelayRange = Tuple[float, float]
ProgressCallback = Callable[[int,int], None]

def _validate_str(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} deve ser uma string não vazia.")

def send_email(email:str, message:str, delay_range: DelayRange =(0.5, 2.0), verbose: bool = False) -> Dict[str, Any]:
    """
    Simula o envio de um e-mail.

    Parâmetros:
      - email: destinatário
      - message: corpo da mensagem
      - delay_range: tupla (min, max) para simular tempo de envio
      - verbose: se True, registra informações no nível INFO

    Retorna um dict com status e destinatário.
    """
    _validate_str("email", email)
    _validate_str("message", message)
    
    if delay_range[0] < 0 or delay_range[1] < delay_range[0]:
        raise ValueError("delay_range inválido.")
    
    if verbose:
        logger.info("Preparando para enviar email para %s", email)
    
    delay = random.uniform(delay_range[0], delay_range[1])
    time.sleep(delay)
    
    if verbose:
        logger.info("Email enviado para %s", email)
    
    return {"status": "success", "recipient": email, "delay": round(delay, 3)}

def generate_report(
  report_type: str,
  filters: Dict[str, Any],
  total_iterations: int = 200_000,
  progress_callback: Optional[ProgressCallback] = None,
  verbose: bool = False
) -> Dict[str, Any]:
    """
    Simula a geração de um relatório pesado.

    - report_type: identificador do relatório
    - filters: dicionário de filtros
    - total_iterations: controla a "carga" da simulação (tornar menor para desenvolvimento)
    - progress_callback: função opcional chamada como progress_callback(current, total)
    - verbose: se True, registra progresso via logger.info

    Retorna um dict com metadados do relatório.
    """
    _validate_str("report_type", report_type)
    if not isinstance(filters, dict):
        raise ValueError("filters deve ser um dicionário.")
    if total_iterations <= 0:
        raise ValueError("total_iterations deve ser um inteiro positivo.")
    
    checkpoint = max(1, total_iterations // 4)
    last_logged = -1
    
    for i in range(total_iterations):
        if i % checkpoint == 0:
            pct = int((i / total_iterations) * 100)
            if progress_callback:
                try:
                    progress_callback(i, total_iterations)
                except Exception:
                    logger.exception("progress_callback falhou")
            elif verbose and pct != last_logged:
                logger.info("Progresso do relatório: %s%%", pct)
                last_logged = pct
    work_time = random.uniform(2,4)
    time.sleep(work_time)
    
    if verbose:
        logger.info("Relatório %s gerado com sucesso", report_type)
    
    return {
        "status": "success",
        "report_type": report_type,
        "rows": random.randint(100, 1000),
        "iterations": total_iterations,
        "work_time": round(work_time, 3),
    }
    
  
  