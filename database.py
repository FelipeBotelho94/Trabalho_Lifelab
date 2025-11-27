import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = 'sentinela.db'

def conectar():
    # check_same_thread=False ajuda a evitar erros no Streamlit
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def inicializar_db():
    conn = conectar()
    c = conn.cursor()
    
    # 1. Tabelas
    c.execute('''CREATE TABLE IF NOT EXISTS usuario (
        id INTEGER PRIMARY KEY, nome TEXT, estilo_aprendizagem TEXT, estilo_codigo INTEGER
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS tarefas (
        id INTEGER PRIMARY KEY, nome TEXT UNIQUE, categoria_ia INTEGER
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS agenda (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tarefa_nome TEXT, inicio DATETIME, fim DATETIME,
        minutos_foco_planejado INTEGER, minutos_foco_realizado INTEGER,
        feedback_cansaco INTEGER, concluido BOOLEAN DEFAULT 0
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS metas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nome_meta TEXT, tarefa_associada TEXT,
        data_alvo DATETIME, nivel_conhecimento INTEGER, total_horas_estimadas REAL,
        concluido BOOLEAN DEFAULT 0
    )''')
    
    # 2. Inserir Tarefas Padrão (DevOps) se vazio
    c.execute("SELECT count(*) FROM tarefas")
    if c.fetchone()[0] == 0:
        tarefas_devops = [
            ("Ler Documentação Técnica / Manuais", 0),
            ("Ler Artigos / Medium", 0),
            ("Estudar Teoria (Livro/PDF)", 0),
            ("Revisar Anotações", 0),
            ("Assistir Aula da Faculdade", 1),
            ("Ver Tutorial no YouTube", 1),
            ("Assistir Curso Online (Udemy/Alura)", 1),
            ("Ouvir Podcast Tech", 2),
            ("Treinar Listening (Inglês/Espanhol)", 2),
            ("Laboratório DevOps (Docker/K8s)", 3),
            ("Codar em Python / IA", 3),
            ("Resolver Lista de Exercícios", 3),
            ("Projeto Prático / Protótipo", 3),
            ("Configurar Servidor / Infra", 3)
        ]
        c.executemany("INSERT INTO tarefas (nome, categoria_ia) VALUES (?, ?)", tarefas_devops)
        conn.commit()
        print("Banco inicializado com tarefas padrão.")
        
    conn.close()

# --- FUNÇÕES DE USUÁRIO ---

def usuario_existe():
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT count(*) FROM usuario")
    existe = c.fetchone()[0] > 0
    conn.close()
    return existe

def get_usuario():
    conn = conectar()
    df = pd.read_sql_query("SELECT * FROM usuario LIMIT 1", conn)
    conn.close()
    return df.iloc[0] if not df.empty else None

def salvar_perfil_usuario(nome, estilo_txt, estilo_cod):
    conn = conectar()
    c = conn.cursor()
    try:
        # Limpa anteriores
        c.execute("DELETE FROM usuario") 
        # Insere novo
        c.execute("INSERT INTO usuario (nome, estilo_aprendizagem, estilo_codigo) VALUES (?, ?, ?)",
                  (nome, estilo_txt, estilo_cod))
        conn.commit()
    except Exception as e:
        print(f"Erro ao salvar usuário: {e}")
    finally:
        # O finally garante que fecha MESMO se der erro, mas só no final de tudo
        conn.close()

# --- FUNÇÕES DE AGENDA/TAREFAS ---

def get_tarefas():
    conn = conectar()
    df = pd.read_sql_query("SELECT nome, categoria_ia FROM tarefas ORDER BY nome", conn)
    conn.close()
    return df

def adicionar_evento(tarefa, inicio_iso, fim_iso, minutos_foco):
    conn = conectar()
    c = conn.cursor()
    c.execute("""
        INSERT INTO agenda (tarefa_nome, inicio, fim, minutos_foco_planejado)
        VALUES (?, ?, ?, ?)
    """, (tarefa, inicio_iso, fim_iso, minutos_foco))
    conn.commit()
    conn.close()

def get_eventos():
    conn = conectar()
    df = pd.read_sql_query("SELECT id, tarefa_nome, inicio, fim, concluido, minutos_foco_planejado FROM agenda", conn)
    conn.close()
    
    eventos = []
    for _, row in df.iterrows():
        cor = "#28a745" if row['concluido'] else "#3174ad"
        eventos.append({
            "title": row['tarefa_nome'],
            "start": row['inicio'],
            "end": row['fim'],
            "backgroundColor": cor,
            "id": str(row['id']),
            "minutos_foco_planejado": row['minutos_foco_planejado']
        })
    return eventos

def deletar_evento(evento_id):
    conn = conectar()
    c = conn.cursor()
    try:
        c.execute("DELETE FROM agenda WHERE id=?", (evento_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Erro ao deletar: {e}")
        return False
    finally:
        conn.close()
        
# --- NOVAS FUNÇÕES PARA GRÁFICOS E CRONÔMETRO ---

def get_dados_concluidos():
    """Busca apenas as missões que foram realmente feitas para o gráfico"""
    conn = conectar()
    # Pega nome, data de inicio e o tempo REAL executado
    df = pd.read_sql_query("""
        SELECT tarefa_nome, inicio, minutos_foco_realizado 
        FROM agenda 
        WHERE concluido = 1
    """, conn)
    conn.close()
    return df

def finalizar_missao_manual(nome_tarefa, minutos_reais, inicio_iso, fim_iso):
    """Salva uma sessão feita pelo cronômetro"""
    conn = conectar()
    c = conn.cursor()
    c.execute("""
        INSERT INTO agenda (tarefa_nome, inicio, fim, minutos_foco_planejado, minutos_foco_realizado, concluido)
        VALUES (?, ?, ?, ?, ?, 1)
    """, (nome_tarefa, inicio_iso, fim_iso, minutos_reais, minutos_reais))
    conn.commit()
    conn.close()