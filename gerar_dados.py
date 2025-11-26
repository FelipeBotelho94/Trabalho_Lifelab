import pandas as pd
import numpy as np
import random

NUM_SESSOES = 2000 # Mais dados pois temos mais variáveis!

dados = []

print("Gerando dados avançados (V3.0)...")

for _ in range(NUM_SESSOES):
    # --- 1. CONTEXTO ---
    # 0=Seg, 6=Dom
    dia_semana = random.randint(0, 6) 
    hora_dia = random.randint(6, 23)
    # 0=Casa, 1=Biblioteca, 2=Café/Rua
    local = random.choice([0, 0, 0, 1, 2]) # Mais chance de ser Casa
    # 0=Silêncio, 1=Moderado, 2=Barulho
    ruido = random.randint(0, 2)
    
    # --- 2. TAREFA ---
    # Categoria (Visual, Auditivo...)
    categoria_tarefa = random.randint(0, 3) 
    # Urgência: 1 (Longe) a 10 (É pra hoje!)
    prazo_urgencia = random.randint(1, 10)
    # Dificuldade: 1 (Fácil) a 5 (Hard)
    dificuldade = random.randint(1, 5)
    # Interesse: 1 (Chato) a 5 (Amo)
    interesse = random.randint(1, 5)
    
    # --- 3. BIOLÓGICO ---
    horas_sono = random.uniform(4.0, 10.0)
    # Tempo desde última refeição (0h a 6h)
    horas_jejum = random.uniform(0.5, 6.0)
    
    # Simulação do TESTE DE REFLEXO (PVT) em milissegundos
    # Base: 250ms (rápido). Aumenta com sono ruim e jejum.
    tempo_reacao_ms = 250 + ((8 - horas_sono) * 20) + (horas_jejum * 10)
    tempo_reacao_ms += random.uniform(-20, 50) # Variação natural
    
    # --- CÁLCULO DO TEMPO IDEAL (A LÓGICA DO ESPECIALISTA) ---
    foco_base = 50
    
    # Fatores que AUMENTAM o foco
    if prazo_urgencia > 8: foco_base += 15 # O "Desespero" ajuda a focar
    if interesse > 3: foco_base += 10      # Flow
    if local == 1: foco_base += 10         # Biblioteca ajuda
    
    # Fatores que DIMINUEM o foco
    if tempo_reacao_ms > 400: foco_base -= 20 # Cérebro lento
    if ruido == 2: foco_base -= 15            # Barulho atrapalha
    if horas_jejum > 4: foco_base -= 10       # Fome
    if dificuldade > 4: foco_base -= 5        # Muito difícil cansa rápido
    if dia_semana >= 5: foco_base -= 10       # Fim de semana (preguiça)
    
    # Limites
    tempo_ideal = max(10, min(120, foco_base + random.uniform(-5, 5)))
    
    dados.append([
        dia_semana, hora_dia, local, ruido, 
        categoria_tarefa, prazo_urgencia, dificuldade, interesse,
        horas_sono, horas_jejum, tempo_reacao_ms,
        int(tempo_ideal)
    ])

# Salvar
colunas = [
    'dia_semana', 'hora_dia', 'local', 'ruido',
    'categoria_tarefa', 'prazo_urgencia', 'dificuldade', 'interesse',
    'horas_sono', 'horas_jejum', 'tempo_reacao_ms', 
    'target'
]
df = pd.DataFrame(dados, columns=colunas)
df.to_csv('historico_estudo_v3.csv', index=False)
print("✅ Dados V3 gerados! Agora rode o treino.")