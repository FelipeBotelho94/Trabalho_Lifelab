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
import time
import plotly.express as px # Biblioteca de gráficos

# --- CONFIG ---
st.set_page_config(layout="wide", page_title="Sentinela Dashboard", page_icon="🌑")
database.inicializar_db()

if 'navegacao_atual' not in st.session_state:
    st.session_state['navegacao_atual'] = 'Dashboard'

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
        
        st.markdown("---")
        st.subheader("🧠 Calibragem do Cérebro")
        st.caption("Responda com sinceridade para a IA entender como você aprende.")
        
        # PERGUNTA 1: MÉTODO PREFERIDO (Múltipla Escolha com Chips)
        st.write("**1. Ao estudar algo novo, o que você MAIS gosta? (Pode marcar vários)**")
        q1 = sac.chip(
            items=[
                sac.ChipItem('Ler documentação / Livros'),
                sac.ChipItem('Ver vídeos / Tutoriais'),
                sac.ChipItem('Ouvir Podcasts / Explicação'),
                sac.ChipItem('Ir direto para o código'),
            ],
            multiple=True, variant='outline', color='indigo', return_index=False
        )
        
        st.write("") # Espaço
        
        # COLUNAS PARA AS OUTRAS PERGUNTAS (Fica mais organizado)
        c1, c2 = st.columns(2)
        
        with c1:
            # PERGUNTA 2: O QUE CANSA
            q2 = st.radio(
                "2. O que mais te cansa/entedia?",
                [
                    "Ler textos gigantes sem imagens",
                    "Apenas ouvir alguém falando",
                    "Ambientes muito barulhentos",
                    "Ficar só na teoria sem fazer nada"
                ], index=0
            )
            
            # PERGUNTA 3: GADGET NOVO (SITUAÇÃO)
            q3 = st.radio(
                "3. Comprou um celular novo. O que você faz?",
                [
                    "Lê o manual de instruções primeiro",
                    "Procura um review/unboxing no YouTube",
                    "Pede para alguém te explicar",
                    "Sai apertando os botões pra descobrir"
                ], index=0
            )
            
        with c2:
            # PERGUNTA 4: LOCALIZAÇÃO
            q4 = st.radio(
                "4. Você precisa ir a um lugar novo:",
                [
                    "Olha o mapa antes de sair",
                    "Segue o GPS olhando a rota na tela",
                    "Ouve as instruções do Waze passo-a-passo",
                    "Se baseia por pontos de referência físicos"
                ], index=0
            )

            # PERGUNTA 5: ENSINAR
            q5 = st.radio(
                "5. Para ensinar algo a um amigo, você:",
                [
                    "Escreve um resumo/passo-a-passo",
                    "Faz um desenho ou diagrama",
                    "Explica falando/áudio",
                    "Pede para ele fazer enquanto você olha"
                ], index=0
            )

        st.markdown("---")
        
        if st.button("🚀 Analisar Respostas e Entrar", type="primary"):
            if nome and q1: # Garante que tem nome e pelo menos 1 item na Q1
                # --- CÁLCULO DE PONTUAÇÃO (0=Leitura, 1=Visual/Video, 2=Auditivo, 3=Prático) ---
                pontos = [0, 0, 0, 0]
                
                # Q1 (Vale 1 ponto cada)
                for item in q1:
                    if "Ler" in item: pontos[0] += 1
                    elif "Ver" in item: pontos[1] += 1
                    elif "Ouvir" in item: pontos[2] += 1
                    elif "Ir direto" in item: pontos[3] += 1
                
                # Q2 (Invertido: O que cansa indica o oposto)
                if "textos" in q2: pontos[1]+=1; pontos[3]+=1 # Odeia ler -> Gosta de ver/fazer
                elif "ouvir" in q2: pontos[0]+=1; pontos[1]+=1 # Odeia ouvir -> Gosta de ler/ver
                elif "barulhentos" in q2: pontos[0]+=1; pontos[1]+=1 # Odeia som -> Visual/Leitura
                elif "teoria" in q2: pontos[3]+=2 # Odeia teoria -> É MUITO Prático
                
                # Q3 (Gadget)
                if "manual" in q3: pontos[0]+=1
                elif "YouTube" in q3: pontos[1]+=1
                elif "alguém" in q3: pontos[2]+=1
                elif "apertando" in q3: pontos[3]+=1
                
                # Q4 (Mapa)
                if "mapa" in q4: pontos[0]+=1
                elif "GPS" in q4: pontos[1]+=1
                elif "instruções" in q4: pontos[2]+=1
                elif "referência" in q4: pontos[3]+=1
                
                # Q5 (Ensinar)
                if "Escreve" in q5: pontos[0]+=1
                elif "desenho" in q5: pontos[1]+=1
                elif "Explica" in q5: pontos[2]+=1
                elif "Pede" in q5: pontos[3]+=1
                
                # VENCEDOR
                ganhador_cod = np.argmax(pontos)
                nomes_estilos = ["Leitura/Visual 👁️", "Visual/Dinâmico 🎥", "Auditivo 👂", "Cinestésico/Prático 🛠️"]
                perfil_final = nomes_estilos[ganhador_cod]
                
                # SALVAR NO BANCO
                database.salvar_perfil_usuario(nome, perfil_final, int(ganhador_cod))
                
                st.balloons()
                st.success(f"Perfil Identificado: **{perfil_final}**")
                st.experimental_rerun() # Entra no dashboard
            else:
                st.error("Por favor, preencha seu nome e a primeira pergunta.")

else:
    user = database.get_usuario()
    with st.sidebar:
        st.write("")
        c1,c2,c3=st.columns([1,2,1])
        with c2: st.image("https://cdn-icons-png.flaticon.com/512/4140/4140048.png", width=100)
        st.markdown(f"<div style='text-align:center'><h3>{user['nome']}</h3><p style='color:#666'>{user['estilo_aprendizagem']}</p></div>", unsafe_allow_html=True)
        
        # Mapeamento para o menu saber onde está
        mapa_nav = {'Dashboard':0, 'Cronômetro':1, 'Nova Sessão':2, 'Gerenciar Missões':3, 'Planejador':4, 'Configurações':5}
        index_atual = mapa_nav.get(st.session_state.get('navegacao_atual', 'Dashboard'), 0)

        menu = sac.menu([
            sac.MenuItem('Dashboard', icon='grid-fill'),
            sac.MenuItem('Cronômetro', icon='stopwatch-fill'), 
            sac.MenuItem('Nova Sessão', icon='lightning-charge-fill', tag=sac.Tag('IA', color='purple')),
            sac.MenuItem('Gerenciar Missões', icon='clipboard-data-fill'),
            sac.MenuItem('Planejador', icon='calendar2-range-fill'),
            sac.MenuItem('Configurações', icon='gear-fill'),
        ], format_func='upper', size='lg', color='indigo', variant='filled', index=index_atual)
        
        # Sincroniza se você clicar no menu manualmente
        if menu != st.session_state['navegacao_atual']:
            st.session_state['navegacao_atual'] = menu
            st.experimental_rerun()

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

        df_concluidos = database.get_dados_concluidos()
        
        if not df_concluidos.empty:
            # Agrupa por tarefa somando os minutos
            df_chart = df_concluidos.groupby('tarefa_nome')['minutos_foco_realizado'].sum().reset_index()
            
            # Cria coluna de Horas só para o texto bonito
            df_chart['Horas_Texto'] = df_chart['minutos_foco_realizado'].apply(lambda x: f"{int(x//60)}h {int(x%60)}m")
            
            # Métrica Total
            total_min = df_chart['minutos_foco_realizado'].sum()
            st.metric("🔥 Tempo Total de Foco", f"{int(total_min//60)}h {int(total_min%60)}m")
            
            # Gráfico em MINUTOS (Visualmente melhor)
            fig = px.bar(
                df_chart, 
                x='tarefa_nome', 
                y='minutos_foco_realizado', 
                color='minutos_foco_realizado',
                text='Horas_Texto', # Mostra o tempo formatado em cima da barra
                color_continuous_scale=['#00D2FC', '#3F8CFF', '#6C5DD3', '#FF5275'], 
                template='plotly_dark',
                labels={'minutos_foco_realizado': 'Minutos', 'tarefa_nome': 'Missão'}
            )
            
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)',
                font_family="Inter", 
                font_color="white", 
                height=300, 
                margin=dict(l=0, r=0, t=30, b=0),
                showlegend=False
            )
            fig.update_traces(textposition='outside', marker_line_width=0, opacity=0.9)
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("💡 Use o 'Cronômetro' para registrar suas primeiras horas de estudo e ver o gráfico!")

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
                    
                    # --- BOTÃO MÁGICO ---
                    if st.button(f"▶ INICIAR", key=f"start_{ev['id']}", use_container_width=True):
                        # Configura o Timer
                        st.session_state.cronometro_ativo = True
                        st.session_state.inicio_cronometro = datetime.now()
                        st.session_state.tarefa_atual = ev['title']
                        # Força a ida para a página do Cronômetro
                        st.session_state['navegacao_atual'] = 'Cronômetro'
                        st.experimental_rerun()
                    
                    st.markdown("<div style='margin-bottom:15px'></div>", unsafe_allow_html=True)
            else:
                st.info("Sem missões.")
                
    elif menu == 'Cronômetro':
        st.markdown("<h1 style='color: white; font-weight: 800;'>⏱️ Modo de Foco</h1>", unsafe_allow_html=True)
        
        if 'cronometro_ativo' not in st.session_state:
            st.session_state.cronometro_ativo = False
        
        if not st.session_state.cronometro_ativo:
            c1, c2 = st.columns([2, 1])
            with c1:
                df = database.get_tarefas()
                tarefa_escolhida = st.selectbox("O que vamos estudar agora?", df['nome'])
            
            st.info("A tela vai atualizar a cada segundo. Não feche a aba.")
            if st.button("🔥 INICIAR SESSÃO", type="primary"):
                st.session_state.cronometro_ativo = True
                st.session_state.inicio_cronometro = datetime.now()
                st.session_state.tarefa_atual = tarefa_escolhida
                st.experimental_rerun()
        else:
            delta = datetime.now() - st.session_state.inicio_cronometro
            minutos = int(delta.total_seconds() // 60)
            segundos = int(delta.total_seconds() % 60)
            tempo_str = f"{minutos:02d}:{segundos:02d}"
            
            st.markdown(f"""
            <div style="text-align: center; padding: 40px; background: #111; border: 2px solid #00D2FC; border-radius: 20px;">
                <h2 style="color: #888; margin:0;">FOCADO EM: {st.session_state.tarefa_atual}</h2>
                <h1 style="font-size: 100px; color: #00D2FC; margin: 0; font-family: monospace;">{tempo_str}</h1>
            </div>
            """, unsafe_allow_html=True)
            
            st.write("")
            if st.button("🛑 PARAR E SALVAR", type="primary", use_container_width=True):
                fim = datetime.now()
                min_totais = int(delta.total_seconds() / 60)
                if min_totais < 1: min_totais = 1
                
                database.finalizar_missao_manual(st.session_state.tarefa_atual, min_totais, 
                                                 st.session_state.inicio_cronometro.isoformat(), fim.isoformat())
                st.session_state.cronometro_ativo = False
                st.success(f"Parabéns! +{min_totais} minutos registrados.")
                time.sleep(2)
                st.experimental_rerun()
            
            time.sleep(1)
            st.experimental_rerun()
            
    # === PÁGINA CRONÔMETRO (NOVA) ===
    elif st.session_state['navegacao_atual'] == 'Cronômetro':
        st.markdown("<h1 style='color: white; font-weight: 800;'>⏱️ Modo de Foco</h1>", unsafe_allow_html=True)
        
        if 'cronometro_ativo' not in st.session_state:
            st.session_state.cronometro_ativo = False
        
        if not st.session_state.cronometro_ativo:
            st.info("Nenhuma tarefa ativa. Inicie pelo Dashboard ou escolha abaixo:")
            df = database.get_tarefas()
            tar = st.selectbox("Tarefa", df['nome'])
            if st.button("🔥 INICIAR AGORA", type="primary"):
                st.session_state.cronometro_ativo = True
                st.session_state.inicio_cronometro = datetime.now()
                st.session_state.tarefa_atual = tar
                st.experimental_rerun()
        else:
            # TELA DE FOCO
            delta = datetime.now() - st.session_state.inicio_cronometro
            minutos = int(delta.total_seconds() // 60)
            segundos = int(delta.total_seconds() % 60)
            tempo_str = f"{minutos:02d}:{segundos:02d}"
            
            st.markdown(f"""
            <div style="text-align: center; padding: 40px; background: #050505; border: 2px solid #00D2FC; border-radius: 20px;">
                <h3 style="color: #666; margin:0;">EM PROGRESSO</h3>
                <h1 style="color: #fff; margin:10px 0; font-size: 32px;">{st.session_state.tarefa_atual}</h1>
                <h1 style="font-size: 100px; color: #00D2FC; margin: 0; font-family: monospace; text-shadow: 0 0 20px #00D2FC;">{tempo_str}</h1>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🛑 PARAR E SALVAR", type="primary", use_container_width=True):
                # Salva no banco (usando a função nova que criamos no database.py)
                fim = datetime.now()
                min_totais = int(delta.total_seconds() / 60)
                if min_totais < 1: min_totais = 1
                
                database.finalizar_missao_manual(st.session_state.tarefa_atual, min_totais, 
                                                 st.session_state.inicio_cronometro.isoformat(), fim.isoformat())
                st.session_state.cronometro_ativo = False
                st.success(f"Salvo! +{min_totais} min.")
                time.sleep(2)
                st.session_state['navegacao_atual'] = 'Dashboard' # Volta pro inicio
                st.experimental_rerun()
                
            time.sleep(1) # Atualiza relógio
            st.experimental_rerun()

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
                st.success("💾 Sessão salva no calendário!", icon="✅")
                
            else:
                st.error("IA não carregada. Verifique os arquivos .h5")

    elif menu == 'Gerenciar Missões':
        st.markdown("<h1 style='color: white; font-weight: 800;'>📂 Diário de Missões</h1>", unsafe_allow_html=True)
        
        evs = database.get_eventos()
        if not evs:
            st.info("Nenhum registro no banco de dados.")
        else:
            # Ordena do mais novo pro mais velho
            evs_ord = sorted(evs, key=lambda x: x['start'], reverse=True)
            
            # Cabeçalho da Tabela Customizada
            c1, c2, c3 = st.columns([3, 2, 1])
            c1.markdown("**MISSÃO**")
            c2.markdown("**DATA**")
            c3.markdown("**AÇÃO**")
            st.markdown("---")
            
            for ev in evs_ord:
                dt = datetime.fromisoformat(ev['start']).strftime("%d/%m - %H:%M")
                
                c1, c2, c3 = st.columns([3, 2, 1])
                
                # Define cor do texto baseado no tipo (pra ficar visual)
                cor_texto = "#3F8CFF"
                if "Prova" in ev['title']: cor_texto = "#FF5275"
                
                with c1:
                    st.markdown(f"<span style='color:{cor_texto}; font-weight:bold'>{ev['title']}</span>", unsafe_allow_html=True)
                with c2:
                    st.write(dt)
                with c3:
                    # Botão de Excluir com chave única
                    if st.button("🗑️ Excluir", key=f"del_{ev['id']}"):
                        sucesso = database.deletar_evento(ev['id'])
                        if sucesso:
                            st.success("Apagado!")
                            st.experimental_rerun()
                        else:
                            st.error("Erro.")
                
                st.markdown("<hr style='margin:5px 0; opacity:0.1'>", unsafe_allow_html=True)

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