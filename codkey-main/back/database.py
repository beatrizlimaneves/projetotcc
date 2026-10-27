import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Em hospedagens com disco persistente, configure DATABASE_PATH para um caminho persistente.
BANCO = os.environ.get("DATABASE_PATH", os.path.join(BASE_DIR, "academia.db"))

def conectar():
    pasta = os.path.dirname(os.path.abspath(BANCO))
    os.makedirs(pasta, exist_ok=True)
    conexao = sqlite3.connect(BANCO, timeout=15)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    conexao.execute("PRAGMA busy_timeout = 15000")
    return conexao

def _colunas(conexao, tabela):
    return {linha["name"] for linha in conexao.execute(f"PRAGMA table_info({tabela})")}

def criar_banco():
    conexao = conectar()
    conexao.execute("PRAGMA journal_mode = WAL")
    conexao.executescript("""
    CREATE TABLE IF NOT EXISTS usuarios (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      nome TEXT NOT NULL,
      email TEXT NOT NULL UNIQUE COLLATE NOCASE,
      senha TEXT NOT NULL,
      criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS alunos (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      nome TEXT NOT NULL,
      email TEXT COLLATE NOCASE,
      telefone TEXT,
      idade INTEGER,
      data_nascimento TEXT,
      plano TEXT,
      status TEXT NOT NULL DEFAULT 'Ativo',
      criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS professores (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      nome TEXT NOT NULL,
      email TEXT COLLATE NOCASE,
      telefone TEXT,
      especialidade TEXT,
      criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS planos (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      nome TEXT NOT NULL,
      preco REAL NOT NULL CHECK(preco >= 0),
      descricao TEXT,
      duracao INTEGER DEFAULT 1,
      criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS pagamentos (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      aluno_id INTEGER NOT NULL,
      valor REAL NOT NULL CHECK(valor >= 0),
      data TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'Pendente',
      forma_pagamento TEXT,
      FOREIGN KEY (aluno_id) REFERENCES alunos(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS treinos (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      aluno_id INTEGER NOT NULL,
      nome TEXT NOT NULL,
      descricao TEXT,
      professor_id INTEGER,
      divisao TEXT,
      criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (aluno_id) REFERENCES alunos(id) ON DELETE CASCADE,
      FOREIGN KEY (professor_id) REFERENCES professores(id) ON DELETE SET NULL
    );
    """)
    # Migração segura para bases existentes: adiciona somente colunas ausentes.
    migrations = {
      "alunos": {"data_nascimento":"TEXT", "plano":"TEXT", "status":"TEXT NOT NULL DEFAULT 'Ativo'", "criado_em":"TEXT"},
      "planos": {"duracao":"INTEGER DEFAULT 1", "criado_em":"TEXT"},
      "pagamentos": {"forma_pagamento":"TEXT"},
      "treinos": {"professor_id":"INTEGER", "divisao":"TEXT", "criado_em":"TEXT"},
      "usuarios": {"criado_em":"TEXT"},
      "professores": {"criado_em":"TEXT"}
    }
    for tabela, colunas in migrations.items():
        existentes = _colunas(conexao, tabela)
        for coluna, definicao in colunas.items():
            if coluna not in existentes:
                conexao.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {definicao}")
    conexao.execute("CREATE INDEX IF NOT EXISTS idx_alunos_email ON alunos(email)")
    conexao.execute("CREATE INDEX IF NOT EXISTS idx_pagamentos_aluno ON pagamentos(aluno_id)")
    conexao.execute("CREATE INDEX IF NOT EXISTS idx_treinos_aluno ON treinos(aluno_id)")
    conexao.commit()
    conexao.close()

if __name__ == "__main__":
    criar_banco()
    print(f"Banco SQLite pronto: {BANCO}")
