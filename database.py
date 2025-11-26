import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = 'sentinela.db'

def conectar():
    return sqlite3.connect(DB_NAME)

def inicializar_db():
    conn = conectar()
    c = conn.cursor()
    
    # Tabela 1: Usuário
    c.execute('''CREATE TABLE IF NOT EXISTS usuario (
        id INTEGER PRIMARY KEY, nome TEXT, estilo_aprendizagem TEXT, estilo_codigo INTEGER
    )''')
    
    # Tabela 2: Tarefas
    c.execute('''CREATE TABLE IF NOT EXISTS tarefas (
        id INTEGER PRIMARY KEY, nome TEXT UNIQUE, categoria_ia INTEGER
    )''')
    
    # Tabela 3: Agenda
    c.execute('''CREATE TABLE IF NOT EXISTS agenda (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tarefa_nome TEXT,
        inicio DATETIME,
        fim DATETIME,
        minutos_foco_planejado INTEGER,
        minutos_foco_realizado INTEGER,
        feedback_cansaco INTEGER,
        concluido BOOLEAN DEFAULT 0
    )''')
    
    # Tabela 4: Metas (Para o Planejador)
    c.execute('''CREATE TABLE IF NOT EXISTS metas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome_meta TEXT,
        tarefa_associada TEXT,
        data_alvo DATETIME,
        nivel_conhecimento INTEGER,
        total_horas_estimadas REAL,
        concluido BOOLEAN DEFAULT 0
    )''')
    
    # --- AQUI ESTÁ A SUA LISTA PERSONALIZADA ---
    # Categorias IA: 0=Ler, 1=Video, 2=Audio, 3=Prática
    
    c.execute("SELECT count(*) FROM tarefas")
    if c.fetchone()[0] == 0:
        tarefas_devops = [
            # Categoria 0: Leitura / Visual (Cansa a vista, passivo)
            ("Ler Documentação Técnica / Manuais", 0),
            ("Ler Artigos / Medium", 0),
            ("Estudar Teoria (Livro/PDF)", 0),
            ("Revisar Anotações", 0),

            # Categoria 1: Vídeo (Misto visual + áudio)
            ("Assistir Aula da Faculdade", 1),
            ("Ver Tutorial no YouTube", 1),
            ("Assistir Curso Online (Udemy/Alura)", 1),

            # Categoria 2: Áudio (Descansa a vista)
            ("Ouvir Podcast Tech", 2),
            ("Treinar Listening (Inglês/Espanhol)", 2),

            # Categoria 3: Prática / Mão na Massa (Alto gasto de energia, ativo)
            ("Laboratório DevOps (Docker/K8s)", 3),
            ("Codar em Python / IA", 3),
            ("Resolver Lista de Exercícios", 3),
            ("Projeto Prático / Protótipo", 3),
            ("Configurar Servidor / Infra", 3)
        ]
        
        c.executemany("INSERT INTO tarefas (nome, categoria_ia) VALUES (?, ?)", tarefas_devops)
        conn.commit()
        print("Banco de dados inicializado com tarefas DEVOPS!")
        
    conn.close()
    conn = conectar()
    c = conn.cursor()
    
    # Tabela 1: Usuário (Perfil)
    c.execute('''CREATE TABLE IF NOT EXISTS usuario (
        id INTEGER PRIMARY KEY, nome TEXT, estilo_aprendizagem TEXT, estilo_codigo INTEGER
    )''')
    
    # Tabela 2: Tarefas (Categorias)
    c.execute('''CREATE TABLE IF NOT EXISTS tarefas (
        id INTEGER PRIMARY KEY, nome TEXT UNIQUE, categoria_ia INTEGER
    )''')
    
    # Tabela 3: Agenda (Eventos do Calendário)
    # Aqui guardamos o planejado E o realizado
    c.execute('''CREATE TABLE IF NOT EXISTS agenda (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tarefa_nome TEXT,
        inicio DATETIME,
        fim DATETIME,
        minutos_foco_planejado INTEGER,
        minutos_foco_realizado INTEGER, -- Preenchido depois
        feedback_cansaco INTEGER,       -- Preenchido depois
        concluido BOOLEAN DEFAULT 0
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS metas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome_meta TEXT,      -- Ex: "Prova de Cálculo"
        tarefa_associada TEXT,
        data_alvo DATETIME,
        nivel_conhecimento INTEGER, -- 1 a 10
        total_horas_estimadas REAL,
        concluido BOOLEAN DEFAULT 0
    )''')
    
    # Inserir tarefas padrão se vazio
    c.execute("SELECT count(*) FROM tarefas")
    if c.fetchone()[0] == 0:
        tarefas = [("Ler Livro", 0), ("Videoaula", 1), ("Podcast", 2), ("Programar/Prática", 3)]
        c.executemany("INSERT INTO tarefas (nome, categoria_ia) VALUES (?, ?)", tarefas)
        conn.commit()
        
    conn.close()

# --- FUNÇÕES DE AGENDA ---

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
    """Busca eventos para mostrar no calendário"""
    conn = conectar()
    # Formatamos para JSON que o calendário entende
    df = pd.read_sql_query("SELECT id, tarefa_nome, inicio, fim, concluido FROM agenda", conn)
    conn.close()
    
    eventos = []
    for _, row in df.iterrows():
        cor = "#28a745" if row['concluido'] else "#3174ad" # Verde se feito, Azul se pendente
        eventos.append({
            "title": row['tarefa_nome'],
            "start": row['inicio'],
            "end": row['fim'],
            "backgroundColor": cor,
            "id": str(row['id']) # ID para podermos editar depois
        })
    return eventos
    
def get_tarefas():
    conn = conectar()
    df = pd.read_sql_query("SELECT nome, categoria_ia FROM tarefas ORDER BY nome", conn)
    conn.close()
    return df