import os
import time
import logging
from contextlib import contextmanager
from typing import Optional, Any, Iterator

import psycopg2
from psycopg2 import pool, sql, extras

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# configuração via env
DB_NAME = os.getenv("DB_NAME", "scheduler_db")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "admin")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))

# pool global (inicializado via init_pool)
_connection_pool: Optional[pool.ThreadedConnectionPool] = None


def init_pool(minconn: int = 1, maxconn: int = 5, retries: int = 3, retry_delay: float = 2.0) -> None:
    """
    Inicializa o pool de conexões. Pode ser chamada no startup da aplicação.
    Faz tentativas em caso de falha temporária.
    """
    global _connection_pool
    if _connection_pool:
        logger.debug("Connection pool já inicializado")
        return

    attempt = 0
    last_exc: Optional[BaseException] = None
    while attempt < retries:
        try:
            _connection_pool = pool.ThreadedConnectionPool(
                minconn=minconn,
                maxconn=maxconn,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST,
                port=DB_PORT,
            )
            logger.info("🐘 Pool de conexões com o PostgreSQL criado com sucesso (min=%s max=%s).", minconn, maxconn)
            return
        except Exception as e:
            last_exc = e
            attempt += 1
            logger.warning("Tentativa %s/%s de criar pool falhou: %s. Aguardando %.1fs...", attempt, retries, e, retry_delay)
            time.sleep(retry_delay)

    logger.error("Não foi possível criar pool de conexões após %s tentativas.", retries)
    raise last_exc  # re-levanta a última exceção para o chamador tratar


def close_pool() -> None:
    """Fecha o pool e todas as conexões (chamar no shutdown)."""
    global _connection_pool
    if _connection_pool:
        try:
            _connection_pool.closeall()
            logger.info("Pool de conexões fechado.")
        except Exception:
            logger.exception("Erro ao fechar connection pool")
        finally:
            _connection_pool = None


@contextmanager
def get_connection() -> Iterator[psycopg2.extensions.connection]:
    """
    Context manager que fornece uma conexão do pool e garante seu retorno.
    Uso:
      with get_connection() as conn:
          with conn.cursor() as cur:
              cur.execute(...)
    """
    if not _connection_pool:
        raise RuntimeError("Connection pool não inicializado. Chame init_pool() antes.")
    conn = _connection_pool.getconn()
    try:
        yield conn
    finally:
        try:
            # resetar estado de transação caso a conexão tenha sido usada
            if conn:
                conn.rollback()
        except Exception:
            logger.debug("rollback falhou ao retornar conexão")
        _connection_pool.putconn(conn)


def execute(query: str, params: Optional[tuple] = None, commit: bool = True) -> None:
    """Helper para executar comandos (INSERT/UPDATE/DDL)."""
    with get_connection() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute(query, params)
            if commit:
                conn.commit()
        except Exception:
            conn.rollback()
            logger.exception("Erro ao executar query")
            raise


def fetch_one(query: str, params: Optional[tuple] = None) -> Optional[Any]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchone()


def fetch_all(query: str, params: Optional[tuple] = None) -> list:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchall()


def init_db() -> None:
    """Cria a tabela jobs se não existir. Deve ser chamada no startup."""
    init_pool()  # garante pool disponível
    create_sql = """
    CREATE TABLE IF NOT EXISTS jobs (
        id SERIAL PRIMARY KEY,
        job_name VARCHAR(255) NOT NULL,
        schedule VARCHAR(255) NOT NULL,
        payload JSONB NOT NULL,
        last_run_at TIMESTAMP,
        next_run_at TIMESTAMP NOT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        execute(create_sql)
        logger.info("Tabela 'jobs' criada ou já existente.")
    except Exception:
        logger.exception("Erro ao inicializar o banco de dados")
        raise


if __name__ == "__main__":
    # exemplo de uso rápido em desenvolvimento
    try:
        init_db()
    finally:
        close_pool()