import streamlit as st
import streamlit_antd_components as sac
import pandas as pd
import numpy as np
import tensorflow as tf
import joblib
import database
import planejador
import calendar as pycalendar # Biblioteca nativa do Python
from datetime import datetime, timedelta

# --- CONFIG ---
st.set_page_config(layout="wide", page_title="Sentinela Dashboard", page_icon="🌑")
database.inicializar_db()

def carregar_css(nome_arquivo):
    try:
        with open(nome_arquivo, encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except: pass
carregar_css("style.css")

@st.cache_resource
def carregar_ia():
    try:
        model = tf.keras.models.load_model('sentinela_brain_v3.h5')
        scaler = joblib.load('meu_scaler_v3.pkl')
        return model, scaler
    except: return None, None
model, scaler = carregar_ia()

# --- FUNÇÃO MÁGICA: GERA O CALENDÁRIO EM HTML PURO ---
def renderizar_calendario_html(ano, mes, eventos):
    cal = pycalendar.Calendar(firstweekday=0) # 0 = Segunda
    dias_do_mes = cal.monthdayscalendar(ano, mes)
    
    nomes_dias = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    hoje = datetime.now()
    
    # HTML DO CABEÇALHO
    html = '<div class="cyber-calendar-container">'
    html += '<div class="calendar-header">'
    for d in nomes_dias:
        html += f'<div class="day-name">{d}</div>'
    html += '</div>'
    
    # HTML DO GRID
    html += '<div class="calendar-grid">'
    
    for semana in dias_do_mes:
        for dia in semana:
            if dia == 0:
                # Dia vazio (mês anterior/próximo)
                html += '<div class="day-cell" style="background: transparent; border: none;"></div>'
            else:
                # É hoje?
                classe_hoje = "day-today" if (dia == hoje.day and mes == hoje.month and ano == hoje.year) else ""
                
                # HTML DA CÉLULA DO DIA
                html += f'<div class="day-cell {classe_hoje}">'
                html += f'<div class="day-number">{dia}</div>'
                
                # BUSCAR EVENTOS DESTE DIA
                data_atual_str = f"{ano}-{mes:02d}-{dia:02d}"
                
                for ev in eventos:
                    # O banco salva como '2025-11-26T19:00:00'. Pegamos só a data.
                    if ev['start'].startswith(data_atual_str):
                        titulo = ev['title']
                        # Define cor CSS
                        classe_cor = "evt-blue"
                        if "Prova" in titulo: classe_cor = "evt-pink"
                        elif "Estudar" in titulo: classe_cor = "evt-purple"
                        elif "Codar" in titulo: classe_cor = "evt-cyan"
                        
                        html += f'<div class="event-pill {classe_cor}">{titulo[:15]}..</div>'
                
                html += '</div>' # Fecha day-cell
                
    html += '</div></div>' # Fecha grid e container
    return html

def desenhar_card_lateral(titulo, data_obj, cor_border):
    d = data_obj.strftime("%d")
    h = data_obj.strftime("%H:%M")
    st.markdown(f"""
    <div class="event-card" style="border-left: 3px solid {cor_border};">
        <div class="card-day-big">{d}</div>
        <div style="overflow: hidden;">
            <div class="card-title">{titulo}</div>
            <div class="card-time">{h} • AGENDADO</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- APP ---
if not database.usuario_existe():
    st.title("🛡️ Bem-vindo ao Sentinela")
    st.markdown("### Configuração de Perfil Neural")
    with st.container():
        nome = st.text_input("Como devemos te chamar?", placeholder="Ex: Felipe")
        st.subheader("Quiz de Aprendizagem")
        c1, c2 = st.columns(2)
        with c1:
            st.write("1. Métodos preferidos (Marque vários):")
            q1 = sac.chip(items=[
                sac.ChipItem('Ler documentação (Visual/Leitura)'),
                sac.ChipItem('Ver vídeos/tutoriais (Visual/Vídeo)'),
                sac.ChipItem('Ouvir podcasts (Auditivo)'),
                sac.ChipItem('Ir direto para código (Prático)'),
            ], multiple=True, variant='outline', color='indigo', return_index=False)
            p2 = st.radio("2. O que mais te cansa?", ["Apenas ouvir", "Ler texto gigante", "Silêncio absoluto", "Só teoria"], index=0)
        with c2:
            p3 = st.radio("3. Como você explicaria?", ["Escreveria resumo", "Gravaria vídeo", "Mandaria áudio", "Faria junto"], index=0)
        st.markdown("---")
        if st.button("🚀 Salvar Perfil", type="primary"):
            if nome and q1:
                votos = [0,0,0,0]
                for item in q1:
                    if "Ler" in item: votos[0]+=1
                    elif "Ver" in item: votos[1]+=1
                    elif "Ouvir" in item: votos[2]+=1
                    elif "Ir direto" in item: votos[3]+=1
                if "ouvir" in p2: votos[0]+=1
                elif "Ler" in p2: votos[1]+=1
                elif "Silêncio" in p2: votos[2]+=1
                elif "teoria" in p2: votos[3]+=1
                if "resumo" in p3: votos[0]+=1
                elif "vídeo" in p3: votos[1]+=1
                elif "áudio" in p3: votos[2]+=1
                elif "Faria" in p3: votos[3]+=1
                ganhador_cod = np.argmax(votos)
                nomes = ["Visual 👁️", "Vídeo 🎥", "Auditivo 👂", "Prático 🛠️"]
                database.salvar_perfil_usuario(nome, nomes[ganhador_cod], int(ganhador_cod))
                st.balloons()
                st.experimental_rerun()
            else: st.error("Preencha nome e a primeira pergunta.")
else:
    user = database.get_usuario()
    with st.sidebar:
        st.write("")
        c1,c2,c3=st.columns([1,2,1])
        with c2: st.image("https://cdn-icons-png.flaticon.com/512/4140/4140048.png", width=100)
        st.markdown(f"<div style='text-align:center'><h3>{user['nome']}</h3><p style='color:#666'>{user['estilo_aprendizagem']}</p></div>", unsafe_allow_html=True)
        menu = sac.menu([
            sac.MenuItem('Dashboard', icon='grid-fill'),
            sac.MenuItem('Nova Sessão', icon='lightning-charge-fill'),
            sac.MenuItem('Planejador', icon='calendar2-range-fill'),
            sac.MenuItem('Configurações', icon='gear-fill'),
        ], size='lg', color='indigo', variant='filled')

    if menu == 'Dashboard':
        # TÍTULO E CONTROLE DE MÊS
        c_title, c_sel = st.columns([3, 1])
        with c_title:
            st.markdown("<h1 style='font-weight:800; text-transform:uppercase; letter-spacing:2px; background: -webkit-linear-gradient(45deg, #00c6fb, #005bea); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>Central de Comando</h1>", unsafe_allow_html=True)
        with c_sel:
            # Seletor simples de mês (Poderia ser mais complexo, mas vamos focar no visual)
            mes_atual = datetime.now().month
            ano_atual = datetime.now().year
            st.caption(f"📅 {datetime.now().strftime('%B %Y')}")

        col_cal, col_list = st.columns([3, 1.2])

        with col_cal:
            # 1. PEGA EVENTOS
            eventos = database.get_eventos()
            # 2. GERA HTML PURO
            html_calendario = renderizar_calendario_html(ano_atual, mes_atual, eventos)
            # 3. RENDERIZA
            st.markdown(html_calendario, unsafe_allow_html=True)

        with col_list:
            st.markdown("### PRÓXIMAS MISSÕES")
            if eventos:
                evs = sorted(eventos, key=lambda x: x['start'])
                for ev in evs[-4:]:
                    dt = datetime.fromisoformat(ev['start'])
                    cor = "#3F8CFF"
                    if "Prova" in ev['title']: cor = "#FF5275"
                    elif "Estudar" in ev['title']: cor = "#6C5DD3"
                    elif "Codar" in ev['title']: cor = "#00D2FC"
                    desenhar_card_lateral(ev['title'], dt, cor)
            else:
                st.info("Sem missões.")

    elif menu == 'Nova Sessão':
        st.title("🤖 Foco Inteligente (IA V3)")
        c1, c2 = st.columns(2)
        with c1:
            df_tarefas = database.get_tarefas()
            tarefa_nome = st.selectbox("O que fazer?", df_tarefas['nome'])
            categoria_ia = df_tarefas[df_tarefas['nome'] == tarefa_nome].iloc[0]['categoria_ia']
            local = st.selectbox("Local:", ["Casa", "Biblioteca", "Café/Rua"])
            ruido = st.select_slider("Ruído:", ["Silencioso", "Moderado", "Barulhento"])
        with c2:
            sono = st.slider("Sono (h):", 0.0, 12.0, 7.0)
            jejum = st.number_input("Jejum (h):", 0.0, 24.0, 2.0)
            reflexo = st.slider("Reflexo (ms):", 200, 600, 300)
            
        if st.button("🧠 Calcular com IA", type="primary"):
            if model:
                mapa_local = {"Casa":0, "Biblioteca":1, "Café/Rua":2}
                mapa_ruido = {"Silencioso":0, "Moderado":1, "Barulhento":2}
                agora = datetime.now()
                input_data = scaler.transform([[agora.weekday(), agora.hour, mapa_local[local], mapa_ruido[ruido], categoria_ia, 5, 3, 3, sono, jejum, reflexo]])
                foco = int(model.predict(input_data)[0][0])
                pausa = int(foco * 0.2)
                c_r1, c_r2 = st.columns(2)
                c_r1.metric("⏱️ Foco", f"{foco} min")
                c_r2.metric("☕ Pausa", f"{pausa} min")
                inicio = datetime.now().isoformat()
                fim = (datetime.now() + timedelta(minutes=foco)).isoformat()
                database.adicionar_evento(tarefa_nome, inicio, fim, foco)
                st.success("✅ Agendado!")
            else: st.error("IA Off")

    elif menu == 'Planejador':
        st.title("🎓 Planejador de Rotina")
        with st.form("plano"):
            c_a, c_b = st.columns(2)
            meta = c_a.text_input("Objetivo (ex: Prova AWS)")
            data_alvo = c_b.date_input("Data da Prova")
            df_tarefas = database.get_tarefas()
            tarefa_base = st.selectbox("Matéria Base:", df_tarefas['nome'])
            conhecimento = st.slider("Nível Atual (1-10):", 1, 10, 3)
            dif = st.slider("Dificuldade (1-5):", 1, 5, 3)
            if st.form_submit_button("Gerar Cronograma"):
                dt_alvo = datetime.combine(data_alvo, datetime.min.time())
                sucesso, res = planejador.gerar_cronograma_prova(meta, tarefa_base, dt_alvo, conhecimento, dif, [0,1,2,3,4])
                if sucesso:
                    st.success("Plano criado!")
                    for item in res: database.adicionar_evento(item['tarefa'], item['inicio'], item['fim'], item['minutos'])
                else: st.error(res)
        
    elif menu == 'Configurações':
        if st.button("Reset"):
            conn=database.conectar(); conn.execute("DELETE FROM usuario"); conn.commit(); conn.close()
            st.experimental_rerun()