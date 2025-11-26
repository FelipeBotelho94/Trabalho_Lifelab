import pandas as pd
from datetime import datetime, timedelta
import database

def calcular_horas_necessarias(conhecimento_atual, dificuldade_materia, dias_restantes):
    """
    Algoritmo que define QUANTAS horas você precisa estudar.
    Quanto menos você sabe e mais difícil a matéria, mais horas.
    """
    # Gap de Conhecimento (o quanto falta aprender de 0 a 10)
    gap = 10 - conhecimento_atual
    
    # Base: 1 hora de estudo para cada ponto de gap, multiplicado pela dificuldade
    # Ex: Gap 8 (sabe pouco) * Dificuldade 3 = 24 horas totais
    # Fator de ajuste 0.5 para não ficar desumano
    horas_totais = (gap * dificuldade_materia) * 0.5
    
    # Se a prova é amanhã (1 dia), não dá pra estudar 50 horas. Teto máximo de 8h/dia.
    teto_maximo = dias_restantes * 8
    
    return min(horas_totais, teto_maximo)

def gerar_cronograma_prova(nome_prova, tarefa, data_prova, conhecimento, dificuldade, dias_disponiveis_semana):
    """
    Distribui as horas necessárias no calendário.
    dias_disponiveis_semana: Lista de dias permitidos [0, 2, 4] (Seg, Qua, Sex)
    """
    hoje = datetime.now()
    dias_ate_prova = (data_prova - hoje).days
    
    if dias_ate_prova <= 0:
        return False, "A data da prova precisa ser no futuro!"

    # 1. Calcular o "Tamanho do Monstro"
    horas_totais = calcular_horas_necessarias(conhecimento, dificuldade, dias_ate_prova)
    
    # 2. Distribuir
    agendamentos = []
    horas_agendadas = 0
    data_cursor = hoje
    
    # Loop para preencher os dias até fechar as horas ou chegar a prova
    while horas_agendadas < horas_totais and data_cursor < data_prova:
        
        # Verifica se o dia da semana atual (0-6) está nos dias que o usuário escolheu
        if data_cursor.weekday() in dias_disponiveis_semana:
            
            # Quanto estudar neste dia?
            # Estratégia: Tentar colocar blocos de 1h ou 2h
            horas_hoje = 2 
            
            # Se faltar pouco, coloca só o que falta
            if (horas_totais - horas_agendadas) < 2:
                horas_hoje = horas_totais - horas_agendadas
            
            # Criar o evento (Aqui definimos um horário padrão, ex: 19:00, mas poderia ser dinâmico)
            inicio = data_cursor.replace(hour=19, minute=0, second=0, microsecond=0)
            fim = inicio + timedelta(hours=horas_hoje)
            
            # Converte minutos para o padrão do banco
            minutos_foco = int(horas_hoje * 60)
            
            # Salva na memória para mostrar pro usuário antes de gravar
            agendamentos.append({
                "tarefa": tarefa,
                "inicio": inicio.isoformat(),
                "fim": fim.isoformat(),
                "minutos": minutos_foco
            })
            
            horas_agendadas += horas_hoje
            
        # Vai para o próximo dia
        data_cursor += timedelta(days=1)
        
    return True, agendamentos