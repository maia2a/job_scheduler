
import psycopg2
from psycopg2 import pool
import os

import psycopg2.pool

DB_NAME = os.getenv("DB_NAME", "scheduler_db") 
DB_USER = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "admin")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

try:
    connection_pool = psycopg2.pool.SimpleConnectionPool(
      minconn=1,
      maxconn=5,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT)
    print("🐘 Pool de conexões com o PostgreSQL criado com sucesso!")
  
except psycopg2.OperationalError as e:
    print(f"Erro ao conectar ao PostgreSQL: {e}")
    connection_pool = None

def get_connection():
  """Obtém uma conexão do pool."""
  if connection_pool:
      return connection_pool.getconn()
  else:
      raise Exception("Pool de conexões não está disponível.")

def release_connection(conn):
  """Libera uma conexão de volta para o pool."""
  if connection_pool:
      connection_pool.putconn(conn)
  else:
      raise Exception("Pool de conexões não está disponível.")

def init_db():
    """Inicializa o banco de dados criando a tabela de jobs se não existir."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                   id SERIAL PRIMARY KEY,
                    job_name VARCHAR(255) NOT NULL,
                    schedule VARCHAR(255) NOT NULL, -- Ex: "*/5 * * * *" (cron format)
                    payload JSONB NOT NULL,
                    last_run_at TIMESTAMP,
                    next_run_at TIMESTAMP NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
            print("Tabela 'jobs' criada ou já existente.")
    except Exception as e:
        print(f"Erro ao inicializar o banco de dados: {e}")
    finally:
        release_connection(conn)

if __name__ == "__main__":
    init_db()