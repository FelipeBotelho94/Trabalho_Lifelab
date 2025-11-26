import streamlit as st
from streamlit_calendar import calendar
import pandas as pd
import numpy as np
import tensorflow as tf
import joblib
import database
import planejador  # Certifique-se que o arquivo planejador.py está na pasta
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sentinela do Foco", layout="wide", page_icon="🛡️")

# Inicializa o banco de dados ao abrir
database.inicializar_db()

# --- CARREGAR O CÉREBRO (IA) ---
@st.cache_resource
def carregar_ia():
    try:
        # Carrega o modelo V3 e o escalonador V3
        model = tf.keras.models.load_model('sentinela_brain_v3.h5')
        scaler = joblib.load('meu_scaler_v3.pkl')
        return model, scaler
    except Exception as e:
        return None, None

model, scaler = carregar_ia()

# --- BARRA LATERAL (NAVEGAÇÃO) ---
st.sidebar.title("🛡️ Sentinela")
st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "Navegação:", 
    ["📅 Calendário & Agenda", "🤖 Sessão IA (Agora)", "🎓 Planejador de Rotina"]
)

st.sidebar.markdown("---")
st.sidebar.info("Sistema V3.0 Ativo\nModo: Pessoal/DevOps")

# =========================================================
# PÁGINA 1: CALENDÁRIO & AGENDA
# =========================================================
if menu == "📅 Calendário & Agenda":
    st.title("📅 Sua Linha do Tempo")
    
    # 1. Busca eventos no banco de dados
    try:
        eventos_db = database.get_eventos()
    except:
        eventos_db = []
    
    # 2. Configurações do Calendário Visual
    calendar_options = {
        "headerToolbar": {
            "left": "today prev,next",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek,timeGridDay"
        },
        "initialView": "timeGridWeek",  # Visão semanal
        "slotMinTime": "06:00:00",      # Começa as 06h
        "slotMaxTime": "24:00:00",      # Termina as 24h
        "allDaySlot": False,
        "locale": "pt-br"
    }
    
    # 3. Renderiza o Calendário
    calendar(events=eventos_db, options=calendar_options)
    
    st.caption("Dica: Use o 'Planejador' para preencher os buracos na agenda.")

# =========================================================
# PÁGINA 2: SESSÃO COM IA (O "MICRO" GERENCIAMENTO)
# =========================================================
elif menu == "🤖 Sessão IA (Agora)":
    st.title("🤖 Otimizador de Sessão")
    st.markdown("Vou analisar seu estado biológico e o contexto para definir o tempo ideal de agora.")
    
    # --- COLETA DE DADOS ---
    agora = datetime.now()
    dia_semana = agora.weekday() # 0=Segunda
    hora_dia = agora.hour

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("1. O que e Onde?")
        df_tarefas = database.get_tarefas()
        tarefa_nome = st.selectbox("O que vamos estudar?", df_tarefas['nome'])
        
        # Pega a categoria oculta (0, 1, 2, 3) do banco
        categoria_ia = df_tarefas[df_tarefas['nome'] == tarefa_nome].iloc[0]['categoria_ia']
        
        local = st.selectbox("Local:", ["Casa", "Biblioteca", "Café/Rua"])
        mapa_local = {"Casa":0, "Biblioteca":1, "Café/Rua":2}
        
        ruido = st.select_slider("Nível de Ruído:", ["Silencioso", "Moderado", "Barulhento"])
        mapa_ruido = {"Silencioso":0, "Moderado":1, "Barulhento":2}

    with col2:
        st.subheader("2. Estado Biológico")
        sono = st.slider("Horas de Sono:", 0.0, 12.0, 7.0, 0.5)
        jejum = st.number_input("Horas sem comer:", 0.0, 24.0, 2.0)
        
        st.markdown("**Teste de Reflexo (Simulado)**")
        reflexo_real = st.slider("Tempo de Reação (ms):", 200, 600, 300, help="Menor = Mais alerta. Maior = Lento.")
        
        with st.expander("Detalhes da Tarefa (Opcional)"):
            prazo = st.slider("Urgência (1=Longe, 10=Pra hoje):", 1, 10, 5)
            dificuldade = st.slider("Dificuldade:", 1, 5, 3)
            interesse = st.slider("Interesse:", 1, 5, 3)

    st.divider()

    # --- PROCESSAMENTO ---
    if st.button("🧠 Calcular Foco Ideal", type="primary", use_container_width=True):
        if model:
            # Montar vetor de 11 entradas para a IA V3
            input_array = np.array([[
                dia_semana, hora_dia, mapa_local[local], mapa_ruido[ruido],
                categoria_ia, prazo, dificuldade, interesse,
                sono, jejum, reflexo_real
            ]])
            
            # Previsão
            input_scaled = scaler.transform(input_array)
            foco_ia = int(model.predict(input_scaled)[0][0])
            pausa_ia = int(foco_ia * 0.2)
            
            # --- RESULTADO ---
            c1, c2, c3 = st.columns(3)
            c1.metric("⏱️ Tempo de Foco", f"{foco_ia} min")
            c2.metric("☕ Pausa", f"{pausa_ia} min")
            
            # Análise Explicativa (Buffs/Debuffs)
            analise = []
            if prazo > 8: analise.append("🔥 Urgência alta aumentou o tempo.")
            if reflexo_real > 400: analise.append("💤 Reflexos lentos reduziram a carga.")
            if jejum > 4: analise.append("🍔 Atenção: Fome detectada.")
            if local == "Biblioteca": analise.append("📚 Bônus de Biblioteca aplicado.")
            
            with c3:
                if analise:
                    st.warning("Fatores:")
                    for item in analise:
                        st.write(f"- {item}")
                else:
                    st.success("Condições Normais.")
            
            # Agendamento Automático (Opcional)
            inicio_iso = datetime.now().isoformat()
            fim_iso = (datetime.now() + timedelta(minutes=foco_ia)).isoformat()
            database.adicionar_evento(tarefa_nome, inicio_iso, fim_iso, foco_ia)
            st.toast("✅ Sessão salva na Agenda!")
            
        else:
            st.error("Erro: IA V3 não encontrada. Rode 'treinar_modelo.py'.")

# =========================================================
# PÁGINA 3: PLANEJADOR DE ROTINA (O "MACRO" ESTRATEGISTA)
# =========================================================
elif menu == "🎓 Planejador de Rotina":
    st.title("🎓 Arquiteto de Estudos")
    st.markdown("Diga o objetivo e a data. Eu calculo a carga total e monto a rotina.")
    
    with st.form("form_planejador"):
        col_a, col_b = st.columns(2)
        
        nome_meta = col_a.text_input("Nome do Objetivo (ex: Prova de Cálculo)")
        
        df_tarefas = database.get_tarefas()
        tarefa_base = col_b.selectbox("Qual matéria base?", df_tarefas['nome'])
        
        col_c, col_d = st.columns(2)
        data_prova = col_c.date_input("Data da Prova/Entrega:", datetime.now() + timedelta(days=7))
        conhecimento = col_d.slider("Seu nível atual (1=Leigo, 10=Mestre):", 1, 10, 3)
        dificuldade = st.slider("Dificuldade da Matéria:", 1, 5, 3)
        
        st.write("Quais dias da semana você pode estudar?")
        cols_dias = st.columns(7)
        nomes_dias = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
        dias_escolhidos = []
        
        for i, nome in enumerate(nomes_dias):
            if cols_dias[i].checkbox(nome, value=True):
                dias_escolhidos.append(i)
        
        gerar = st.form_submit_button("🔨 Construir Rotina")
    
    # Lógica de Geração
    if gerar:
        # Converter data para datetime
        data_prova_dt = datetime.combine(data_prova, datetime.min.time())
        
        # Chama o algoritmo do planejador.py
        sucesso, resultado = planejador.gerar_cronograma_prova(
            nome_meta, tarefa_base, data_prova_dt, 
            conhecimento, dificuldade, dias_escolhidos
        )
        
        if sucesso:
            st.success("Plano Gerado com Sucesso!")
            
            # Mostra o preview
            st.subheader(f"📅 Plano de Ataque: {nome_meta}")
            
            col_list, col_save = st.columns([2, 1])
            
            with col_list:
                for item in resultado:
                    inicio_formatado = datetime.fromisoformat(item['inicio']).strftime("%d/%m - %H:%M")
                    st.info(f"📌 {inicio_formatado} | {int(item['minutos'])} min de {item['tarefa']}")
            
            with col_save:
                st.write("### Gostou?")
                if st.button("✅ Salvar Tudo na Agenda"):
                    for item in resultado:
                        database.adicionar_evento(
                            item['tarefa'], 
                            item['inicio'], 
                            item['fim'], 
                            item['minutos']
                        )
                    st.balloons()
                    st.success("Rotina salva! Verifique a aba Calendário.")
                    
        else:
            st.error(f"Erro: {resultado}")