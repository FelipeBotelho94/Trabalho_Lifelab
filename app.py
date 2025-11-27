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
            st.markdown("""
                <h1 style='font-weight: 800; font-size: 36px; margin-bottom: 20px; 
                text-transform: uppercase; letter-spacing: 2px; color: #FFFFFF;'>
                Central de Comando
                </h1>
            """, unsafe_allow_html=True)
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
        st.markdown("<h1 style='color: white; font-weight: 800;'>⚡ Nova Sessão (IA)</h1>", unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            df = database.get_tarefas()
            # Dropdown de tarefas
            tar = st.selectbox("O que vamos atacar?", df['nome'])
            # Pega o ID da categoria oculto
            cat = df[df['nome']==tar].iloc[0]['categoria_ia']
            
            local = st.selectbox("Onde você está?", ["Casa", "Biblioteca", "Café/Rua"])
            rui = st.select_slider("Nível de Ruído", ["Silencioso", "Moderado", "Barulhento"])
            # Mapas para converter texto em número para a IA
            mapa_local = {"Casa":0, "Biblioteca":1, "Café/Rua":2}
            mapa_ruido = {"Silencioso":0, "Moderado":1, "Barulhento":2}

        with c2:
            # Inputs Biológicos
            sono = st.slider("Horas de Sono (Noite passada)", 0.0, 12.0, 7.0)
            jej = st.number_input("Horas sem comer (Jejum)", 0.0, 24.0, 2.0)
            ref = st.slider("Nível de Alerta (Reflexo)", 200, 600, 300, help="Menor = Mais rápido")
            
            # Inputs Subjetivos (Escondidos no expander pra limpar o visual)
            with st.expander("Detalhes da Tarefa"):
                prazo = st.slider("Urgência (Prazo)", 1, 10, 5)
                dif = st.slider("Dificuldade", 1, 5, 3)
                inter = st.slider("Interesse", 1, 5, 3)

        st.markdown("---")

        if st.button("🧠 PROCESSAR DADOS", type="primary", use_container_width=True):
            if model:
                # 1. Prepara os dados (O vetor de 11 dimensões que a IA aprendeu)
                agora = datetime.now()
                
                # Vetor: [Dia, Hora, Local, Ruido, Cat, Prazo, Dif, Inter, Sono, Jejum, Reflexo]
                dados_entrada = [[
                    agora.weekday(), agora.hour, 
                    mapa_local[local], mapa_ruido[rui],
                    cat, prazo, dif, inter, 
                    sono, jej, ref
                ]]
                
                # 2. Normaliza e Prevê
                input_scaled = scaler.transform(dados_entrada)
                predicao = model.predict(input_scaled)[0][0]
                foco_ia = int(predicao)
                pausa_ia = int(foco_ia * 0.2) # 20% de pausa
                
                # 3. Exibe Resultado "Gamer"
                c_res1, c_res2, c_res3 = st.columns(3)
                c_res1.metric("⏱️ Foco Sugerido", f"{foco_ia} min")
                c_res2.metric("☕ Pausa", f"{pausa_ia} min")
                
                # Análise de Buffs/Debuffs (Explicação)
                msg = "🟢 Condições Normais"
                if jej > 4: msg = "🔴 Debuff: Fome detectada"
                elif sono < 5: msg = "🔴 Debuff: Sono crítico"
                elif local == "Biblioteca": msg = "🔵 Buff: Ambiente Focado"
                c_res3.info(msg)
                
                # 4. Salva Automaticamente
                inicio = datetime.now().isoformat()
                fim = (datetime.now() + timedelta(minutes=foco_ia)).isoformat()
                database.adicionar_evento(tar, inicio, fim, foco_ia)
                st.toast("💾 Sessão salva no calendário!", icon="✅")
                
            else:
                st.error("IA não carregada. Verifique os arquivos .h5")

    elif menu == 'Planejador':
        st.markdown("<h1 style='color: white; font-weight: 800;'>🎓 Arquiteto de Rotina</h1>", unsafe_allow_html=True)
        st.info("Defina seu objetivo e a IA distribuirá a carga de estudos até a data.")
        
        with st.form("form_plano"):
            c_a, c_b = st.columns(2)
            meta = c_a.text_input("Nome do Objetivo", placeholder="Ex: Prova de AWS Cloud")
            data_alvo = c_b.date_input("Data do Evento/Prova", min_value=datetime.now())
            
            c_c, c_d = st.columns(2)
            df_tarefas = database.get_tarefas()
            tarefa_base = c_c.selectbox("Matéria Base", df_tarefas['nome'])
            
            # Dias da semana (Multiselect é melhor aqui)
            dias_semana = st.multiselect("Dias disponíveis para estudar:", 
                                         ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"],
                                         default=["Seg", "Qua", "Sex"])
            
            # Converter nomes dos dias para números (0-6)
            mapa_dias = {"Seg":0, "Ter":1, "Qua":2, "Qui":3, "Sex":4, "Sáb":5, "Dom":6}
            dias_codigos = [mapa_dias[d] for d in dias_semana]

            st.markdown("---")
            st.markdown("### Calibragem de Carga")
            conhecimento = st.slider("Quanto você já sabe? (1=Leigo, 10=Expert)", 1, 10, 3)
            dif = st.slider("Dificuldade da Matéria (1=Fácil, 5=Insana)", 1, 5, 3)
            
            gerar = st.form_submit_button("🔨 Construir Cronograma", type="primary")
            
            if gerar and meta:
                dt_alvo = datetime.combine(data_alvo, datetime.min.time())
                
                sucesso, resultado = planejador.gerar_cronograma_prova(
                    meta, tarefa_base, dt_alvo, conhecimento, dif, dias_codigos
                )
                
                if sucesso:
                    st.success(f"Plano criado! Foram agendadas **{len(resultado)} sessões** até o dia da prova.")
                    
                    # Salvar no banco
                    progress_text = "Gravando no calendário..."
                    my_bar = st.progress(0, text=progress_text)
                    
                    for i, item in enumerate(resultado):
                        database.adicionar_evento(item['tarefa'], item['inicio'], item['fim'], item['minutos'])
                        my_bar.progress((i + 1) / len(resultado), text=progress_text)
                    
                    my_bar.empty()
                    st.balloons()
                    st.markdown("### 👀 Prévia do Plano:")
                    for item in resultado[:3]: # Mostra só os 3 primeiros
                        data_fmt = datetime.fromisoformat(item['inicio']).strftime("%d/%m")
                        st.write(f"📅 {data_fmt}: {item['minutos']} min - {item['tarefa']}")
                    st.info("Veja o plano completo no Dashboard.")
                    
                else:
                    st.error(resultado)
        
    elif menu == 'Configurações':
        if st.button("Reset"):
            conn=database.conectar(); conn.execute("DELETE FROM usuario"); conn.commit(); conn.close()
            st.experimental_rerun()