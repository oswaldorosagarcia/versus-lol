import streamlit as st
import requests
import plotly.graph_objects as go
from components import load_css, safe_html, get_champ_img, get_tier_img, get_spell_img, get_rune_html, get_lane_html, format_time, build_item_html, build_stat_bar, ADS_HTML, build_overview_header_html, build_match_card_html, build_duel_player_card

st.set_page_config(page_title="VERSUS.LOL | Arena", layout="wide", initial_sidebar_state="collapsed")

# 🔥 FUNÇÕES DE ENGENHARIA DE ELO
def get_abs_lp(tier, rank, lp):
    tiers = {'IRON':0, 'BRONZE':1, 'SILVER':2, 'GOLD':3, 'PLATINUM':4, 'EMERALD':5, 'DIAMOND':6}
    ranks = {'IV':0, 'III':1, 'II':2, 'I':3}
    t = str(tier).upper()
    r = str(rank).upper()
    if t in ['MASTER', 'GRANDMASTER', 'CHALLENGER']: return 2800 + lp
    if t not in tiers: return 0
    return (tiers[t] * 400) + (ranks.get(r, 0) * 100) + lp

def get_rank_info_from_abs(abs_lp):
    if abs_lp >= 2800: return "MASTER+", "M+", int(abs_lp - 2800), "#9d48e0"
    if abs_lp < 0: return "IRON IV", "I4", 0, "#5c5b57"
    
    tiers = ['IRON', 'BRONZE', 'SILVER', 'GOLD', 'PLATINUM', 'EMERALD', 'DIAMOND']
    colors = ['#5c5b57', '#cd7e36', '#80989d', '#cd9a31', '#3894a0', '#209b58', '#5368c5'] 
    ranks = ['IV', 'III', 'II', 'I']
    
    t_idx = min(max(int(abs_lp // 400), 0), len(tiers)-1)
    r_idx = min(max(int((abs_lp % 400) // 100), 0), len(ranks)-1)
    lp = int(abs_lp % 100)
    
    short_tier = tiers[t_idx][0]
    rank_num = {'IV':'4', 'III':'3', 'II':'2', 'I':'1'}[ranks[r_idx]]
    return f"{tiers[t_idx]} {ranks[r_idx]}", f"{short_tier}{rank_num}", lp, colors[t_idx]

# ==========================================
# 🎨 CSS GLOBAL - ATUALIZADO COM O TRUQUE MESTRE
# ==========================================
load_css("style.css")

if 'view' not in st.session_state: st.session_state.view = 'busca'
if 'current_summoner' not in st.session_state: st.session_state.current_summoner = "" 
if 'player_data' not in st.session_state: st.session_state.player_data = None
if 'match_id' not in st.session_state: st.session_state.match_id = ""
if 'main_champ' not in st.session_state: st.session_state.main_champ = ""

import os
BACKEND_URL = os.getenv("BACKEND_URL", "https://versus-lol.onrender.com")

# ==========================================
# 🎯 TELA 1: BUSCA
# ==========================================
if st.session_state.view == 'busca':
    st.markdown("<div style='height: 28vh;'></div>", unsafe_allow_html=True)
    st.markdown("<h1 class='lol-title'>VERSUS.LOL</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        # Adicionado o border=False para sumir com a "segunda caixa" da nuvem
        with st.form("search_bar", border=False):
            c_i, c_b = st.columns([6, 1])
            with c_i: 
                summoner_id = st.text_input("", placeholder="Nome#TAG", label_visibility="collapsed")
            with c_b: 
                btn_buscar = st.form_submit_button("🔍")
            
            if btn_buscar and summoner_id and '#' in summoner_id:
                st.session_state.current_summoner = summoner_id 
                
                with st.spinner(''):
                    sucesso = False
                    try:
                        res = requests.post(f"{BACKEND_URL}/history", json={"summoner": summoner_id}, timeout=60)
                        if res.status_code == 200:
                            st.session_state.player_data = res.json()
                            sucesso = True
                        else: 
                            st.error("Jogador não encontrado. Verifique o Nick e a TAG.")
                    except requests.exceptions.RequestException: 
                        st.error("SISTEMA OFFLINE. O servidor backend não está respondendo.")
                    
                    if sucesso:
                        st.session_state.view = 'resultado'
                        st.rerun()

# ==========================================
# 📊 TELA 2: DASHBOARD + HISTÓRICO
# ==========================================
elif st.session_state.view == 'resultado':
    header_col1, header_col2 = st.columns([4, 1])
    with header_col1: safe_html("<h2 style='margin-bottom:0; font-style:italic;'>OVERVIEW DO JOGADOR</h2>")
    with header_col2:
        if st.button("⬅ NOVA BUSCA", use_container_width=True): 
            st.session_state.view = 'busca'
            st.rerun()
            
    st.write("---")
    col_c, col_g, col_a = st.columns([11, 0.5, 4])
    
    with col_c:
        p_data = st.session_state.player_data
        dash = p_data['dashboard']
        p_tier_raw = str(p_data.get('tier', 'UNRANKED')).upper()
        current_lp = p_data.get('lp', 0)
        
        safe_html(build_overview_header_html(p_data))

        # Divisor unificado
        safe_html("""
        <div style='display:flex; align-items:center; justify-content:center; margin: 30px 0 20px 0;'>
            <div style='height: 1px; background: linear-gradient(90deg, transparent, #333, transparent); flex-grow: 1;'></div>
            <span style='background-color:rgba(10, 200, 185, 0.1); color:#0ac8b9; font-size:0.75rem; font-weight:900; letter-spacing:2px; border: 1px solid #0ac8b9; padding: 4px 15px; border-radius: 20px; margin: 0 20px; box-shadow: 0 0 8px rgba(10, 200, 185, 0.2);'>ANÁLISE DAS ÚLTIMAS 50 PARTIDAS</span>
            <div style='height: 1px; background: linear-gradient(90deg, transparent, #333, transparent); flex-grow: 1;'></div>
        </div>
        """)

        # ==========================================
        # 🎛️ NOVO FILTRO GLOBAL DE FILAS
        # ==========================================
        queues = sorted(list(set(g.get('queue', 'Unknown') for g in p_data['history'])))
        c_f1, c_f2, c_f3 = st.columns([1, 2, 1])
        with c_f2:
            safe_html("<div style='text-align:center;'><p style='color:#0ac8b9; font-weight:bold; margin-bottom:5px; font-size:0.85rem; letter-spacing:1px;'>FILTRAR PARTIDAS</p></div>")
            sel_q = st.selectbox("Filtro", ["Todas as Filas"] + queues, label_visibility="collapsed")

        f_hist = p_data['history'] if sel_q == "Todas as Filas" else [g for g in p_data['history'] if g.get('queue') == sel_q]
        
        # Recalcular agregados (Radar e Métricas) para o filtro selecionado
        dash_champs = {}
        aggr = {"k":0, "d":0, "a":0, "cs":0, "vis":0, "dmg":0, "fb":0, "cw":0}
        total_duration = 0
        for g in f_hist:
            c = g['champion']
            if c not in dash_champs: dash_champs[c] = {'games':0, 'wins':0}
            dash_champs[c]['games'] += 1
            dash_champs[c]['wins'] += 1 if g['win'] else 0
            aggr["k"] += g.get("kills", 0); aggr["d"] += g.get("deaths", 0); aggr["a"] += g.get("assists", 0)
            aggr["cs"] += g.get("cs", 0); aggr["vis"] += g.get("vision", 0); aggr["dmg"] += g.get("damage", 0)
            aggr["cw"] += g.get("c_wards", 0); aggr["fb"] += g.get("first_blood", 0)
            total_duration += g.get("duration", 1)
            
        g_count = max(len(f_hist), 1)
        mins = max(total_duration / 60, 1)
        radar = {
            "Combat": min(100, int((aggr["k"]+aggr["a"])/max(aggr["d"],1) * 20)),
            "Farm": min(100, int((aggr["cs"]/mins) * 10)),
            "Vision": min(100, int((aggr["vis"]/mins) * 40)),
            "Aggression": min(100, int((aggr["dmg"]/mins) / 10)),
            "Survival": 100 - min(100, int((aggr["d"]/g_count) * 10))
        }
        metrics = {"c_wards": round(aggr["cw"]/g_count, 1), "fb_pct": round((aggr["fb"]/g_count)*100), "avg_vision": round(aggr["vis"]/g_count), "dpm": round(aggr["dmg"]/mins)}

        dash_c1, dash_c2, dash_c3 = st.columns([1.3, 1.2, 1])
        
        with dash_c1:
            with st.container(border=True):
                safe_html(f"<div style='text-align:center; margin: 10px 0;'><h4 style='color:#FFF; font-size:0.9rem; font-weight:900; letter-spacing:1px; margin:0;'>RECENT CHAMPIONS</h4></div>")
                ch_h = "<div style='height: 290px; background-color: #111; border: 1px solid #333; border-radius: 6px; padding: 10px; overflow-y: auto; overflow-x: hidden;'>"
                for c, s in sorted(dash_champs.items(), key=lambda x: x[1]['games'], reverse=True):
                    wr = round((s['wins']/s['games'])*100)
                    kc = "#1E88E5" if wr>=50 else "#D32F2F"
                    ch_h += f"""
                    <div class='champ-row'>
                        <div style='display:flex; align-items:center; gap:12px;'>
                            <img src='{get_champ_img(c)}' width='38' style='border-radius:50%; box-shadow: 0 0 5px rgba(0,0,0,0.5);'>
                            <div>
                                <p style='margin:0; color:#FFF; font-weight:bold; font-size:1rem;'>{c}</p>
                                <p style='margin:0; color:#888; font-size:0.75rem;'>{s['games']} Played</p>
                            </div>
                        </div>
                        <div style='text-align:right;'>
                            <p style='margin:0; font-weight:900; color:{kc}; font-size:1.1rem;'>{wr}% WR</p>
                        </div>
                    </div>
                    """
                safe_html(ch_h + "</div>")
                
                most_played = sorted(dash_champs.items(), key=lambda x: x[1]['games'], reverse=True)
                if most_played:
                    safe_html("<hr style='border-color:#333; margin:15px 0 10px 0;'><div style='text-align:center; margin-bottom:10px;'><h4 style='color:#0ac8b9; font-size:0.8rem; font-weight:900; letter-spacing:1px; margin:0;'>DEEP DIVE DO CAMPEÃO</h4></div>")
                    sel_champ = st.selectbox("Selecione o campeão:", [c[0] for c in most_played], label_visibility="collapsed")
                    if st.button(f"📈 ANALISAR {sel_champ.upper()}", type="primary", use_container_width=True):
                        st.session_state.main_champ = sel_champ
                        st.session_state.view = 'champ_stats'
                        st.rerun()
                        
        with dash_c2:
            with st.container(border=True): 
                safe_html(f"<div style='text-align:center; margin-bottom:10px;'><h4 style='color:#FFF; font-size:0.9rem; font-weight:900; letter-spacing:1px; margin:0;'>PERFORMANCE RADAR (GPI)</h4></div>")
                
                rv = list(radar.values())
                tv = [f"{k}<br><b>{v}</b>" for k, v in radar.items()]
                
                if rv:
                    rv.append(rv[0])
                    tv.append(tv[0])
                    
                fig_r = go.Figure(data=go.Scatterpolar(
                    r=rv, theta=tv, 
                    fill='toself', fillcolor='rgba(30, 136, 229, 0.4)', 
                    line=dict(color='#1E88E5', width=3), marker=dict(color='#1E88E5', size=6), 
                    hovertemplate="Score: <b>%{r}/100</b><extra></extra>"
                ))
                fig_r.update_layout(
                    polar=dict(
                        radialaxis=dict(visible=True, showticklabels=False, range=[0, 100], showline=False, gridcolor='#333', gridwidth=1), 
                        angularaxis=dict(gridcolor='#333', linecolor='rgba(0,0,0,0)'),
                        bgcolor='rgba(0,0,0,0)'
                    ), 
                    showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                    margin=dict(l=40, r=40, t=10, b=20), font=dict(color='#AAA', size=11, family="Arial"), height=290
                )
                st.plotly_chart(fig_r, use_container_width=True, config={'displayModeBar': False})
                
        with dash_c3:
            with st.container(border=True):
                safe_html(f"<div style='text-align:center; margin: 10px 0;'><h4 style='color:#FFF; font-size:0.9rem; font-weight:900; letter-spacing:1px; margin:0;'>LP PROGRESS TRACKING</h4></div>")
                
                abs_lp_current = get_abs_lp(p_tier_raw, p_data.get('rank', 'I'), current_lp)
                hist_wins = [g['win'] for g in reversed(f_hist)]
                abs_path = []
                temp_abs = abs_lp_current
                for win in reversed(hist_wins):
                    abs_path.insert(0, temp_abs)
                    temp_abs = temp_abs - 22 if win else temp_abs + 19
                
                x_vals = list(range(1, len(abs_path)+1))
                
                hover_texts = []
                marker_colors = []
                for i, val in enumerate(abs_path):
                    full_r, short_r, l, c = get_rank_info_from_abs(val)
                    marker_colors.append(c)
                    delta = ""
                    if i > 0:
                        diff = int(abs_path[i] - abs_path[i-1])
                        d_color = "#0ac8b9" if diff > 0 else "#D32F2F"
                        d_sign = "+" if diff > 0 else ""
                        delta = f"<br><span style='color:{d_color}'><b>{d_sign}{diff} LP</b></span>"
                    
                    if full_r == "MASTER+": hover_texts.append(f"<b><span style='color:{c}'>MASTER+</span></b><br>{l} LP{delta}")
                    else: hover_texts.append(f"<b><span style='color:{c}'>{full_r}</span></b><br>{l} LP{delta}")
                    
                fig_l = go.Figure()
                
                fig_l.add_trace(go.Scatter(
                    y=abs_path, x=x_vals, mode='none', fill='tozeroy', fillcolor='rgba(255, 255, 255, 0.05)', 
                    hoverinfo='skip', showlegend=False
                ))
                
                for i in range(len(abs_path) - 1):
                    seg_x = [x_vals[i], x_vals[i+1]]
                    seg_y = [abs_path[i], abs_path[i+1]]
                    seg_c = marker_colors[i+1]
                    fig_l.add_trace(go.Scatter(x=seg_x, y=seg_y, mode='lines', line=dict(color=seg_c, width=3), hoverinfo='skip', showlegend=False))
                
                fig_l.add_trace(go.Scatter(
                    y=abs_path, x=x_vals, mode='markers', customdata=hover_texts,
                    marker=dict(size=7, color=marker_colors, line=dict(width=1.5, color='#111')),
                    hovertemplate="%{customdata}<extra></extra>", showlegend=False
                ))
                
                min_abs, max_abs = (min(abs_path) if abs_path else 0), (max(abs_path) if abs_path else 0)
                y_min = (int(min_abs) // 100) * 100
                y_max = ((int(max_abs) // 100) + 1) * 100
                if y_max - y_min < 100: 
                    y_min -= 50; y_max += 50
                
                tick_vals = list(range(y_min, y_max + 1, 100))
                tick_texts = []
                for v in tick_vals:
                    _, short_rank, _, b_color = get_rank_info_from_abs(v)
                    tick_texts.append(f"<b style='color:{b_color}'>{short_rank}</b>")
                
                fig_l.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                    xaxis=dict(visible=True, showgrid=False, tickmode='array', tickvals=[1, len(abs_path)//2, len(abs_path)], ticktext=[f"{max(1, len(abs_path)-1)} games ago", str(max(1, (len(abs_path)-1)//2)), "Last game"], tickfont=dict(color='#666', size=10), rangeslider=dict(visible=True, thickness=0.1, bordercolor="#333", borderwidth=1, bgcolor="#000")), 
                    yaxis=dict(visible=True, showgrid=True, gridcolor='#333', griddash='dot', zeroline=False, range=[y_min - 20, y_max + 20], tickmode='array', tickvals=tick_vals, ticktext=tick_texts, tickfont=dict(size=11)), 
                    margin=dict(l=10, r=10, t=10, b=10), height=200
                )
                
                st.plotly_chart(fig_l, use_container_width=True, config={'displayModeBar': False})
                
                safe_html(f"""
                <div style='display:flex; gap:8px; margin-top:5px; padding:0 10px 10px 10px;'>
                    <div class='metric-card'><p class='metric-val'>{metrics['fb_pct']}%</p><p class='metric-lbl'>FIRST BLOOD</p></div>
                    <div class='metric-card'><p class='metric-val'>{metrics['c_wards']}</p><p class='metric-lbl'>CTRL WARDS</p></div>
                </div>
                <div style='display:flex; gap:8px; padding:0 10px 10px 10px;'>
                    <div class='metric-card'><p class='metric-val'>{metrics['avg_vision']}</p><p class='metric-lbl'>AVG VISION</p></div>
                    <div class='metric-card'><p class='metric-val'>{metrics['dpm']}</p><p class='metric-lbl'>AVG DPM</p></div>
                </div>
                """)

        st.write("---")
        safe_html("<h3 style='color:#FFF; font-style:italic;'>RECENT MATCHES</h3>")
        
        for g in f_hist[:15]:
            safe_html(build_match_card_html(g))
            
            if st.button("⚔️ ANALISAR 1v1", key=g['id']): 
                st.session_state.match_id = g['id']
                st.session_state.view = 'duelo'
                st.rerun()

    with col_a: 
        safe_html("<div style='background: repeating-linear-gradient(45deg, #111, #111 10px, #1a1a1a 10px, #1a1a1a 20px); border: 2px dashed #555; padding: 40px 20px; text-align: center; margin-bottom: 20px; color: #555; font-weight: 900; font-style: italic; min-height: 250px; display:flex; flex-direction:column; justify-content:center; border-radius:4px;'><h3>ADVERTISEMENT</h3><p>300x250</p></div>")

# ==========================================
# ⚔️ TELA 3: O DUELO ABSOLUTO
# ==========================================
elif st.session_state.view == 'duelo':
    res = requests.post(f"{BACKEND_URL}/duel", json={"summoner": st.session_state.current_summoner, "match_id": st.session_state.match_id}, timeout=60)
    
    if res.status_code == 200:
        d = res.json()
        j, r, a = d['jogador'], d['rival'], d['analise']
        m = max(d.get('duration', 0) / 60 if d.get('duration', 0) < 10000 else d.get('duration', 0) / 60000, 1)
        
        h_c1, h_c2 = st.columns([4, 1])
        with h_c1: 
            safe_html(f"<h2 style='font-style:italic;'>COMBATE DIRETO</h2><p style='color:#888;'>DURAÇÃO: <span style='color:#FFF;'>{format_time(d.get('duration', 0))}</span> | ID: {st.session_state.match_id}</p>")
        with h_c2:
            if st.button("⬅ VOLTAR", use_container_width=True): 
                st.session_state.view = 'resultado'
                st.rerun()
        
        st.write("---")
        
        v_txt = a.get('veredito', 'Duelo')
        v_c = "#1E88E5" if "AMASSOU" in v_txt else ("#D32F2F" if "DOMINADO" in v_txt else "#FFFFFF")
        safe_html(f"<div style='text-align:center; padding:20px; background:linear-gradient(90deg, transparent, {v_c}44, transparent); border-top: 2px solid {v_c}; border-bottom: 2px solid {v_c}; margin-bottom:30px;'><h1 style='color:{v_c} !important; font-size:3.5rem; letter-spacing:4px; text-shadow: 0 0 20px {v_c}66;'>{v_txt}</h1></div>")

        c_j, c_v, c_r = st.columns([2, 1, 2])
        with c_j:
            safe_html(build_duel_player_card(j, "JOGADOR 1 (VOCÊ)", "#1E88E5"))
            
        with c_v: 
            safe_html("<div class='vs-logo'>VS</div>")
            
        with c_r:
            safe_html(build_duel_player_card(r, "JOGADOR 2 (RIVAL)", "#D32F2F"))

        safe_html("<h3 style='text-align:center; margin:40px 0 20px 0;'>ESTATÍSTICAS COMPARATIVAS</h3>")
        
        with st.container(border=True):
            safe_html(build_stat_bar("OURO TOTAL", j.get('gold',0), r.get('gold',0)))
            safe_html(build_stat_bar("OURO / MINUTO", j.get('gold',0)/m, r.get('gold',0)/m))
            safe_html("<hr style='border-color:#333;'>")
            safe_html(build_stat_bar("DANO A CAMPEÕES", j.get('damage',0), r.get('damage',0)))
            safe_html(build_stat_bar("DPM (DANO POR MINUTO)", j.get('damage',0)/m, r.get('damage',0)/m))
            safe_html("<hr style='border-color:#333;'>")
            safe_html(build_stat_bar("CS (FARM)", j.get('cs',0), r.get('cs',0)))
            safe_html(build_stat_bar("FARM / MINUTO", j.get('cs',0)/m, r.get('cs',0)/m))
            safe_html(build_stat_bar("PLACAR DE VISÃO", j.get('vision',0), r.get('vision',0)))
    else: 
        st.error("Erro ao carregar duelo.")

# ==========================================
# 📈 TELA 4: ESTATÍSTICAS DO CAMPEÃO
# ==========================================
elif st.session_state.view == 'champ_stats':
    c_name = st.session_state.main_champ
    p_data = st.session_state.player_data
    
    h_c1, h_c2, h_c3 = st.columns([3, 2, 1])
    with h_c1: 
        safe_html(f"<div style='display:flex; align-items:center; gap:15px;'><img src='{get_champ_img(c_name)}' width='60' style='border-radius:10px; border:2px solid #1E88E5;'><h2 style='margin:0; font-style:italic;'>DESEMPENHO COM {c_name.upper()}</h2></div>")
    with h_c2:
        queues = sorted(list(set(g.get('queue', 'Unknown') for g in p_data['history'] if g['champion'] == c_name)))
        if len(queues) > 1:
            safe_html("<div style='text-align:center;'><p style='color:#0ac8b9; font-weight:bold; margin-bottom:5px; font-size:0.7rem; letter-spacing:1px;'>FILTRAR FILA</p></div>")
            sel_q_champ = st.selectbox("Filtro", ["Todas as Filas"] + queues, key="champ_q", label_visibility="collapsed")
        else:
            sel_q_champ = "Todas as Filas"
    with h_c3:
        if len(queues) > 1: safe_html("<div style='margin-bottom:23px;'></div>") # Espaçamento para alinhar com o seletor
        if st.button("⬅ VOLTAR", use_container_width=True): 
            st.session_state.view = 'resultado'
            st.rerun()
            
    st.write("---")
    
    champ_history = [g for g in p_data['history'] if g['champion'] == c_name]
    if sel_q_champ != "Todas as Filas":
        champ_history = [g for g in champ_history if g.get('queue') == sel_q_champ]
        
    champ_history.reverse() # Coloca em ordem cronológica para os gráficos
    
    if not champ_history:
        st.warning("Sem dados detalhados nas últimas partidas para este campeão.")
    else:
        total_k = sum(g['kills'] for g in champ_history)
        total_d = sum(g['deaths'] for g in champ_history)
        total_a = sum(g['assists'] for g in champ_history)
        avg_kda = round((total_k + total_a) / max(total_d, 1), 2)
        avg_cs = round(sum(g['cs'] for g in champ_history) / len(champ_history))
        avg_cs_min = round(sum(g['cs'] for g in champ_history) / max(sum(g['duration'] for g in champ_history)/60, 1), 1)
        winrate = round((sum(1 for g in champ_history if g['win']) / len(champ_history)) * 100)
        
        safe_html(f"""
        <div style='display:flex; gap:15px; margin-bottom: 20px;'>
            <div class='metric-card'><p class='metric-val' style='color:{"#1E88E5" if winrate>=50 else "#D32F2F"};'>{winrate}%</p><p class='metric-lbl'>WINRATE</p></div>
            <div class='metric-card'><p class='metric-val'>{avg_kda}:1</p><p class='metric-lbl'>KDA MÉDIO</p></div>
            <div class='metric-card'><p class='metric-val'>{total_k} / {total_d} / {total_a}</p><p class='metric-lbl'>TOTAL K / D / A</p></div>
            <div class='metric-card'><p class='metric-val'>{avg_cs}</p><p class='metric-lbl'>CS MÉDIO</p></div>
        </div>
        """)

        c1, c2 = st.columns(2)
        x_labels = [f"P{i+1}" for i in range(len(champ_history))]
        bar_colors = ["#1E88E5" if g['win'] else "#D32F2F" for g in champ_history]
        hover_texts = [f"<b>{'VITÓRIA' if g['win'] else 'DERROTA'}</b><br>{g['time_ago']}<br>KDA: {g['kills']}/{g['deaths']}/{g['assists']}" for g in champ_history]
        
        with c1:
            kda_vals = [round((g['kills']+g['assists'])/max(g['deaths'], 1), 2) for g in champ_history]
            fig_kda = go.Figure(data=[go.Bar(
                x=x_labels, y=kda_vals, marker_color=bar_colors, 
                text=kda_vals, textposition='outside', 
                textfont=dict(color='#FFF', size=14, family="Impact"),
                marker=dict(line=dict(color='#000', width=2)),
                customdata=hover_texts, hovertemplate="%{customdata}<br>Ratio: <b>%{y}</b><extra></extra>"
            )])
            fig_kda.update_layout(
                title=dict(text="KDA Ratio por Partida", font=dict(color='#0ac8b9', size=16, style='italic')), 
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#FFF'), 
                xaxis=dict(showgrid=False, type='category'), 
                yaxis=dict(showgrid=True, gridcolor='#333', griddash='dot', zeroline=False), 
                margin=dict(t=40, b=20, l=0, r=0), height=320, bargap=0.3
            )
            if kda_vals: 
                fig_kda.update_yaxes(range=[0, max(kda_vals) * 1.3])
                fig_kda.add_hline(y=avg_kda, line_dash="dash", line_color="#0ac8b9", annotation_text=f"MÉDIA: {avg_kda}", annotation_position="top left", annotation_font=dict(color="#0ac8b9", size=10, family="Impact"))
            st.plotly_chart(fig_kda, use_container_width=True, config={'displayModeBar': False})
            
        with c2:
            cs_min_vals = [round(g['cs'] / max(g['duration']/60, 1), 1) for g in champ_history]
            fig_cs = go.Figure(data=[go.Bar(
                x=x_labels, y=cs_min_vals, marker_color=bar_colors, 
                text=cs_min_vals, textposition='outside',
                textfont=dict(color='#FFF', size=14, family="Impact"),
                marker=dict(line=dict(color='#000', width=2)),
                customdata=hover_texts, hovertemplate="%{customdata}<br>CS/m: <b>%{y}</b><extra></extra>"
            )])
            fig_cs.update_layout(
                title=dict(text="FARM (CS/Minuto) por Partida", font=dict(color='#0ac8b9', size=16, style='italic')), 
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#FFF'), 
                xaxis=dict(showgrid=False, type='category'), 
                yaxis=dict(showgrid=True, gridcolor='#333', griddash='dot', zeroline=False), 
                margin=dict(t=40, b=20, l=0, r=0), height=320, bargap=0.3
            )
            if cs_min_vals: 
                fig_cs.update_yaxes(range=[0, max(cs_min_vals) * 1.3])
                fig_cs.add_hline(y=avg_cs_min, line_dash="dash", line_color="#FFD700", annotation_text=f"MÉDIA: {avg_cs_min}", annotation_position="top left", annotation_font=dict(color="#FFD700", size=10, family="Impact"))
            st.plotly_chart(fig_cs, use_container_width=True, config={'displayModeBar': False})
