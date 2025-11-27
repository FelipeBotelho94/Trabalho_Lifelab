# planejador.py
from datetime import datetime, timedelta

def calcular_horas_necessarias(conhecimento_atual, dificuldade_materia, dias_restantes):
    # Gap: quanto falta aprender (0 a 10)
    gap = 10 - conhecimento_atual
    # Fórmula: (Gap * Dificuldade) * Fator de Carga
    horas_totais = (gap * dificuldade_materia) * 0.8
    # Teto: Não estudar mais que 8h/dia
    teto = dias_restantes * 8
    return min(horas_totais, teto)

def gerar_cronograma_prova(nome_meta, tarefa_base, data_prova, conhecimento, dificuldade, dias_semana_disponiveis):
    hoje = datetime.now()
    dias_restantes = (data_prova - hoje).days
    
    if dias_restantes <= 0:
        return False, "A data deve ser no futuro!"

    horas_totais = calcular_horas_necessarias(conhecimento, dificuldade, dias_restantes)
    
    cronograma = []
    cursor = hoje + timedelta(days=1) # Começa amanhã
    horas_agendadas = 0
    
    while horas_agendadas < horas_totais and cursor < data_prova:
        # Se o dia da semana está na lista permitida (0=Seg, 6=Dom)
        if cursor.weekday() in dias_semana_disponiveis:
            # Define duração do bloco (entre 30min e 2h)
            duracao_min = 60 # Padrão 1h
            
            inicio = cursor.replace(hour=19, minute=0, second=0) # Padrão 19h
            fim = inicio + timedelta(minutes=duracao_min)
            
            cronograma.append({
                "tarefa": f"{tarefa_base} (Rev: {nome_meta})",
                "inicio": inicio.isoformat(),
                "fim": fim.isoformat(),
                "minutos": duracao_min
            })
            horas_agendadas += (duracao_min / 60)
            
        cursor += timedelta(days=1)
        
    return True, cronograma