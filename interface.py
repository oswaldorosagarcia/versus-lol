import streamlit as st
import requests
import plotly.graph_objects as go
import re

st.set_page_config(page_title="VERSUS.LOL | Arena", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# 🛠️ FUNÇÕES DE SUPORTE & ENGENHARIA DE ELO
# ==========================================
def safe_html(html_content):
    clean_html = re.sub(r'\s+', ' ', html_content).replace('> <', '><')
    st.markdown(clean_html, unsafe_allow_html=True)

def get_champ_img(champ_name):
    name = champ_name.replace(" ", "").replace("'", "").replace(".", "")
    fixes = {
        "Wukong": "MonkeyKing", "RenataGlasc": "Renata", "Nunu&Willump": "Nunu", 
        "KhaZix": "Khazix", "BelVeth": "Belveth", "ChoGath": "Chogath", 
        "VelKoz": "Velkoz", "LeBlanc": "Leblanc", "KSante": "KSante", "KaiSa": "Kaisa"
    }
    name = fixes.get(champ_name, name)
    return f"https://ddragon.leagueoflegends.com/cdn/15.4.1/img/champion/{name}.png"

def get_tier_img(tier):
    t = tier.lower() if tier else "unranked"
    return f"https://opgg-static.akamaized.net/images/medals_new/{t}.png"

def get_spell_img(spell_id):
    spell_map = {
        1: "SummonerBoost", 3: "SummonerExhaust", 4: "SummonerFlash", 
        6: "SummonerHaste", 7: "SummonerHeal", 11: "SummonerSmite", 
        12: "SummonerTeleport", 13: "SummonerMana", 14: "SummonerDot", 
        21: "SummonerBarrier", 32: "SummonerSnowball", 39: "SummonerSnowURFSnowball_Mark"
    }
    name = spell_map.get(spell_id, "SummonerFlash")
    return f"https://ddragon.leagueoflegends.com/cdn/15.4.1/img/spell/{name}.png"

def get_rune_html(rune_id):
    rune_urls = {
        8100: "https://ddragon.leagueoflegends.com/cdn/img/perk-images/Styles/7200_Domination.png", 
        8000: "https://ddragon.leagueoflegends.com/cdn/img/perk-images/Styles/7201_Precision.png", 
        8200: "https://ddragon.leagueoflegends.com/cdn/img/perk-images/Styles/7202_Sorcery.png", 
        8300: "https://ddragon.leagueoflegends.com/cdn/img/perk-images/Styles/7203_Whimsy.png", 
        8400: "https://ddragon.leagueoflegends.com/cdn/img/perk-images/Styles/7204_Resolve.png"
    }
    if rune_id in rune_urls: 
        return f"<img src='{rune_urls[rune_id]}' width='22' style='background-color:#000; border-radius:50%; border: 1px solid #333;'>"
    return "<div style='width:22px; height:22px; background-color:#222; border-radius:50%; border: 1px solid #333;'></div>"

def get_lane_html(lane):
    lane_urls = {
        "TOP": "https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-static-assets/global/default/images/roles/top.png", 
        "JUNGLE": "https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-static-assets/global/default/images/roles/jungle.png", 
        "MIDDLE": "https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-static-assets/global/default/images/roles/mid.png", 
        "BOTTOM": "https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-static-assets/global/default/images/roles/bot.png", 
        "UTILITY": "https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-static-assets/global/default/images/roles/support.png"
    }
    if not lane or lane in ["NONE", "Invalid"]: return ""
    url = lane_urls.get(lane.upper(), "")
    return f"<img src='{url}' width='16'>" if url else ""

def format_time(duration):
    if duration > 10000: duration = duration // 1000 
    m, s = divmod(duration, 60)
    return f"{m}m {s}s"

def build_item_html(items):
    html = "<div style='display:flex; gap:2px; justify-content:center; margin-top:5px;'>"
    for item in items:
        if item == 0: 
            html += "<div style='width:28px; height:28px; background-color:rgba(0,0,0,0.5); border:1px solid #333; border-radius:3px;'></div>"
        else: 
            html += f"<img src='https://ddragon.leagueoflegends.com/cdn/15.4.1/img/item/{item}.png' width='28' height='28' style='border:1px solid #555; border-radius:3px;'>"
    return html + "</div>"

def build_stat_bar(label, val1, val2, suffix="", invert_colors=False):
    total = val1 + val2 if (val1 + val2) > 0 else 1
    pct1, pct2 = (val1 / total) * 100, (val2 / total) * 100
    c1, c2 = ("#1E88E5", "#D32F2F") if (val1 >= val2 if not invert_colors else val1 <= val2) else ("#555", "#555")
    s1, s2 = (f"{val1:.1f}" if isinstance(val1, float) else str(val1)), (f"{val2:.1f}" if isinstance(val2, float) else str(val2))
    
    return f"""
    <div style="margin-bottom: 20px; padding: 0 10px;">
        <div style="display:flex; justify-content:space-between; margin-bottom:5px; align-items:flex-end;">
            <span style="color:{c1}; font-weight:900; font-size:1.3rem;">{s1}{suffix}</span>
            <span style="color:#FFF; font-weight:bold; font-style:italic; font-size:0.9rem; letter-spacing: 1px;">{label}</span>
            <span style="color:{c2}; font-weight:900; font-size:1.3rem;">{s2}{suffix}</span>
        </div>
        <div style="display:flex; width:100%; height:12px; background-color:#111; overflow:hidden; border: 1px solid #333;">
            <div style="width:{pct1}%; background-color:#1E88E5; border-right: 2px solid #000;"></div>
            <div style="width:{pct2}%; background-color:#D32F2F;"></div>
        </div>
    </div>
    """

# 🔥 FUNÇÕES DE ENGENHARIA DE ELO (Mapeamento Matemático de MMR)
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
# 🎨 CSS GLOBAL 
# ==========================================
st.markdown("""
    <style>
    .stApp { background-color: #0D0D0D; color: #EEEEEE; font-family: 'Arial', sans-serif; }
    h1, h2, h3, h4 { color: #FFFFFF !important; font-weight: 900 !important; text-transform: uppercase; }
    .lol-title { font-family: 'Impact', sans-serif; text-align: center; font-size: 6rem; font-style: italic; margin-bottom: 20px; color: #FFFFFF; text-shadow: -4px 0px 0px #00BFFF, 4px 0px 0px #FF2A2A; }
    
    [data-testid="stForm"] [data-testid="column"] { padding: 0 !important; }
    div[data-testid="stHorizontalBlock"] { gap: 0rem !important; }

    .stTextInput>div>div>input { background-color: #000000; border: 2px solid #555555; color: #FFFFFF; font-weight: bold; text-align: center; font-size: 1.5rem; height: 65px; border-radius: 8px 0 0 8px !important; border-right: none !important;}
    .stTextInput>div>div>input::placeholder { color: #DDDDDD; }
    .stButton>button { background-color: #1A1A1A; border: 2px solid #333333; color: #FFFFFF; font-weight: 900; font-size: 1.2rem; font-style: italic; border-radius: 0px; box-shadow: 4px 4px 0px #000000; width:100%;}
    .stButton>button:hover { background-color: #FFFFFF; color: #000000; border-color: #FFFFFF; transform: translate(-2px, -2px); }
    .data-card { background-color: #1A1A1A; border: 1px solid #333333; padding: 15px; margin-bottom: 12px; border-radius: 4px;}
    .vs-logo { font-family: 'Impact', sans-serif; font-size: 6rem; color: #fff; text-shadow: 4px 4px 0 #D32F2F, -4px -4px 0 #1E88E5; font-style: italic; text-align: center; margin-top: 40px; }
    .badge { background-color: #222; border: 1px solid #555; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; color: #0ac8b9; font-weight: bold; margin-right: 8px; text-transform: uppercase; box-shadow: 2px 2px 0px #000;}
    
    .overview-header { display:flex; justify-content:space-between; align-items:center; border-top: 4px solid #1E88E5; padding: 25px; background: linear-gradient(135deg, #111, #1a1a1a); border-radius: 6px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); border: 1px solid #333; border-top: 4px solid #1E88E5;}
    .champ-row { display:flex; align-items:center; justify-content:space-between; border-bottom:1px solid #222; padding:10px 8px; transition: all 0.2s ease; border-radius: 4px; }
    .champ-row:hover { background-color: rgba(255,255,255,0.05); border-color: #444; }
    .metric-card { background: linear-gradient(180deg, #1A1A1A, #111); border: 1px solid #333; padding: 10px; text-align: center; border-radius: 6px; flex: 1; box-shadow: 2px 2px 8px rgba(0,0,0,0.6); }
    .metric-val { font-size: 1.5rem; font-weight: 900; color: #FFF; margin: 0; text-shadow: 1px 1px 2px #000; }
    .metric-lbl { font-size: 0.65rem; color: #AAA; margin: 0; text-transform: uppercase; font-weight:bold; letter-spacing: 0.5px; margin-top: 4px;}
    
    [data-testid="stFormSubmitButton"] > button { height: 65px; border-radius: 0 8px 8px 0 !important; font-size: 1.8rem; border-top: 2px solid #555 !important; border-bottom: 2px solid #555 !important; border-right: 2px solid #555 !important; border-left: none !important; background-color: #000000; margin: 0; padding: 0;}
    [data-testid="stFormSubmitButton"] > button:hover { background-color: #1A1A1A; border-color: #FFFFFF !important; color: #FFFFFF; transform: none; }
    </style>
""", unsafe_allow_html=True)

if 'view' not in st.session_state: st.session_state.view = 'busca'
if 'current_summoner' not in st.session_state: st.session_state.current_summoner = "" 
if 'player_data' not in st.session_state: st.session_state.player_data = None
if 'match_id' not in st.session_state: st.session_state.match_id = ""

BACKEND_URL = "https://versus-lol.onrender.com/"

ADS_HTML = """
<div style='background: repeating-linear-gradient(45deg, #111, #111 10px, #1a1a1a 10px, #1a1a1a 20px); border: 2px dashed #555; padding: 40px 20px; text-align: center; margin-bottom: 20px; color: #555; font-weight: 900; font-style: italic; min-height: 250px; display:flex; flex-direction:column; justify-content:center; border-radius:4px;'>
    <h3>ADVERTISEMENT</h3><p>300x250</p>
</div>
<div style='background: repeating-linear-gradient(45deg, #111, #111 10px, #1a1a1a 10px, #1a1a1a 20px); border: 2px dashed #555; padding: 40px 20px; text-align: center; margin-bottom: 20px; color: #555; font-weight: 900; font-style: italic; min-height: 600px; display:flex; flex-direction:column; justify-content:center; border-radius:4px;'>
    <h3>ADVERTISEMENT</h3><p>300x600<br>Premium Space</p>
</div>
"""

# ==========================================
# 🎯 TELA 1: BUSCA
# ==========================================
if st.session_state.view == 'busca':
    st.markdown("<div style='height: 28vh;'></div>", unsafe_allow_html=True)
    st.markdown("<h1 class='lol-title'>VERSUS.LOL</h1>", unsafe_allow_html=True)

    # Injeção de CSS focada e blindada apenas para a Barra de Busca
    st.markdown("""
    <style>
    /* Remove a caixa ao redor do formulário inteiro */
    [data-testid="stForm"] {
        border: none !important;
        background-color: transparent !important;
        padding: 0 !important;
    }

    /* Zera o espaço (gap) entre a coluna do texto e a coluna do botão */
    div[data-testid="stForm"] div[data-testid="stHorizontalBlock"] {
        gap: 0px !important;
    }

    /* Estilização da Caixa de Texto */
    div[data-testid="stTextInput"] input {
        height: 60px !important;
        border-radius: 8px 0 0 8px !important; /* Arredonda só a esquerda */
        border: 2px solid #333333 !important;
        border-right: none !important; /* Apaga a borda que encosta no botão */
        background-color: #000000 !important;
        color: #FFFFFF !important;
        font-size: 1.5rem !important;
        font-weight: bold !important;
        text-align: center !important;
        padding: 0 !important;
        box-shadow: none !important;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color: #1E88E5 !important;
    }

    /* Estilização do Botão de Busca (Lupa) */
    div[data-testid="stFormSubmitButton"] button {
        height: 60px !important;
        border-radius: 0 8px 8px 0 !important; /* Arredonda só a direita */
        border: 2px solid #333333 !important;
        border-left: none !important; /* Apaga a borda que encosta na caixa de texto */
        background-color: #111111 !important;
        color: #FFFFFF !important;
        font-size: 1.5rem !important;
        width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
        box-shadow: none !important;
        transition: all 0.3s ease;
    }
    div[data-testid="stFormSubmitButton"] button:hover {
        background-color: #1E88E5 !important;
        border-color: #1E88E5 !important;
        color: #FFFFFF !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Estrutura das colunas centralizadas na tela
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        with st.form("search_bar", border=False):
            
            # Divide a barra de pesquisa: 5 partes pro texto, 1 parte pro botão
            c_i, c_b = st.columns([5, 1])
            
            with c_i: 
                summoner_id = st.text_input("Busca", placeholder="Nome#TAG", label_visibility="collapsed")
            with c_b: 
                btn_buscar = st.form_submit_button("🔍")
            
            if btn_buscar and summoner_id and '#' in summoner_id:
                st.session_state.current_summoner = summoner_id 
                
                with st.spinner('Buscando Invocador...'):
                    sucesso = False
                    try:
                        res = requests.post(f"{BACKEND_URL}/history", json={"summoner": summoner_id}, timeout=30)
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
        icon_url = f"https://ddragon.leagueoflegends.com/cdn/15.4.1/img/profileicon/{p_data.get('profile_icon', 1)}.png"
        p_tier_raw = str(p_data.get('tier', 'UNRANKED')).upper()
        current_lp = p_data.get('lp', 0)
        
        if p_tier_raw in ["", "UNRANKED", "NONE"]:
            tier_html = "<div style='width:80px; height:80px; background-color:#111; border-radius:50%; display:flex; align-items:center; justify-content:center; border: 2px dashed #555;'><span style='color:#555; font-size:0.8rem; font-weight:bold;'>N/A</span></div>"
            rank_str = "UNRANKED"
        else:
            tier_html = f"<img src='{get_tier_img(p_tier_raw)}' width='80' style='filter: drop-shadow(0 0 8px rgba(0,0,0,0.5));'>"
            rank_str = f"{p_tier_raw} {p_data.get('rank', '')}".strip()
        
        total_games = p_data.get('wins', 0) + p_data.get('losses', 0)
        winrate = round((p_data.get('wins', 0) / max(total_games, 1)) * 100) if total_games > 0 else 0
        badges_html = "".join([f"<span class='badge'>{b}</span>" for b in dash['badges']])
        win_color = "#0ac8b9" if winrate >= 50 else "#D32F2F"

        safe_html(f"""
        <div class='overview-header' style='margin-bottom: 20px;'>
            <div style='display:flex; align-items:center; gap:25px;'>
                <img src='{icon_url}' width='100' style='border: 3px solid #333; border-radius: 12px; box-shadow: 0 0 10px rgba(0,0,0,0.8);'>
                <div>
                    <h1 style='margin:0 0 5px 0; color:#FFF !important; font-size: 2.2rem; letter-spacing: 1px;'>{p_data['player']} <span style='color:#888; font-size: 1.4rem; text-transform:none; font-weight: normal;'>#{p_data.get('tag', '')}</span></h1>
                    <div style='margin-top:12px;'>{badges_html}</div>
                </div>
            </div>
            <div style='display:flex; align-items:center; gap:20px; border-left: 1px solid #333; padding-left:30px;'>
                {tier_html}
                <div style='min-width: 220px;'>
                    <p style='margin:0 0 2px 0; color:#888; font-size:0.85rem; font-weight:bold; letter-spacing: 0.5px;'>{p_data.get('rank_type', 'Ranked Solo')}</p>
                    <h2 style='margin:0; color:#1E88E5 !important; font-size:1.6rem; white-space: nowrap;'>{rank_str} <span style='color:#FFF; font-size:1.1rem;'>{current_lp} LP</span></h2>
                    <div style='display:flex; justify-content:space-between; font-size:0.9rem; margin-top:8px;'>
                        <span style='color:#AAA;'>{p_data.get('wins', 0)}W {p_data.get('losses', 0)}L</span>
                        <span style='color:{win_color}; font-weight:900;'>{winrate}% WR</span>
                    </div>
                    <div style='width:100%; height:8px; background:#222; border-radius:4px; margin-top:4px; border: 1px solid #111;'>
                        <div style='width:{winrate}%; height:100%; background:{win_color}; border-radius:4px; box-shadow: 0 0 5px {win_color};'></div>
                    </div>
                </div>
            </div>
        </div>
        """)

        # Divisor unificado
        safe_html("""
        <div style='display:flex; align-items:center; justify-content:center; margin: 30px 0 20px 0;'>
            <div style='height: 1px; background: linear-gradient(90deg, transparent, #333, transparent); flex-grow: 1;'></div>
            <span style='background-color:rgba(10, 200, 185, 0.1); color:#0ac8b9; font-size:0.75rem; font-weight:900; letter-spacing:2px; border: 1px solid #0ac8b9; padding: 4px 15px; border-radius: 20px; margin: 0 20px; box-shadow: 0 0 8px rgba(10, 200, 185, 0.2);'>ANÁLISE DAS ÚLTIMAS 15 PARTIDAS</span>
            <div style='height: 1px; background: linear-gradient(90deg, transparent, #333, transparent); flex-grow: 1;'></div>
        </div>
        """)

        dash_c1, dash_c2, dash_c3 = st.columns([1.2, 1.3, 1])
        
        with dash_c1:
            with st.container(border=True): 
                safe_html(f"<div style='text-align:center; margin-bottom:10px;'><h4 style='color:#FFF; font-size:0.9rem; font-weight:900; letter-spacing:1px; margin:0;'>PERFORMANCE RADAR (GPI)</h4></div>")
                
                rv = list(dash['radar'].values())
                # 🔥 Injetando os valores diretamente no eixo do radar
                tv = [f"{k}<br><b>{v}</b>" for k, v in dash['radar'].items()]
                
                if rv:
                    rv.append(rv[0])
                    tv.append(tv[0])
                    
                fig_r = go.Figure(data=go.Scatterpolar(
                    r=rv, theta=tv, 
                    fill='toself', fillcolor='rgba(30, 136, 229, 0.4)', 
                    line=dict(color='#1E88E5', width=3), marker=dict(color='#1E88E5', size=6), 
                    hovertemplate="<b>%{theta}</b><extra></extra>"
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
                
        with dash_c2:
            with st.container(border=True):
                safe_html(f"<div style='text-align:center; margin: 10px 0;'><h4 style='color:#FFF; font-size:0.9rem; font-weight:900; letter-spacing:1px; margin:0;'>RECENT CHAMPIONS</h4></div>")
                ch_h = "<div style='height: 290px; background-color: #111; border: 1px solid #333; border-radius: 6px; padding: 10px; overflow-y: auto; overflow-x: hidden;'>"
                for c, s in sorted(dash['champs'].items(), key=lambda x: x[1]['games'], reverse=True):
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
            
        with dash_c3:
            with st.container(border=True):
                safe_html(f"<div style='text-align:center; margin: 10px 0;'><h4 style='color:#FFF; font-size:0.9rem; font-weight:900; letter-spacing:1px; margin:0;'>LP PROGRESS TRACKING</h4></div>")
                
                abs_lp_current = get_abs_lp(p_tier_raw, p_data.get('rank', 'I'), current_lp)
                hist_wins = [g['win'] for g in reversed(p_data['history'])]
                abs_path = []
                temp_abs = abs_lp_current
                for win in reversed(hist_wins):
                    abs_path.insert(0, temp_abs)
                    temp_abs = temp_abs - 22 if win else temp_abs + 19
                
                x_vals = list(range(1, len(abs_path)+1))
                
                hover_texts = []
                marker_colors = []
                for val in abs_path:
                    full_r, short_r, l, c = get_rank_info_from_abs(val)
                    marker_colors.append(c)
                    if full_r == "MASTER+": hover_texts.append(f"<b><span style='color:{c}'>MASTER+</span></b><br>{l} LP")
                    else: hover_texts.append(f"<b><span style='color:{c}'>{full_r}</span></b><br>{l} LP")
                    
                fig_l = go.Figure()
                
                # 1. Fill background (translúcido neutro)
                fig_l.add_trace(go.Scatter(
                    y=abs_path, x=x_vals, mode='none', fill='tozeroy', fillcolor='rgba(255, 255, 255, 0.05)', 
                    hoverinfo='skip', showlegend=False
                ))
                
                # 2. Colored line segments (Linha multicolorida que acompanha as cores do Elo)
                for i in range(len(abs_path) - 1):
                    seg_x = [x_vals[i], x_vals[i+1]]
                    seg_y = [abs_path[i], abs_path[i+1]]
                    seg_c = marker_colors[i+1]
                    fig_l.add_trace(go.Scatter(x=seg_x, y=seg_y, mode='lines', line=dict(color=seg_c, width=3), hoverinfo='skip', showlegend=False))
                
                # 3. Markers (Bolinhas coloridas)
                fig_l.add_trace(go.Scatter(
                    y=abs_path, x=x_vals, mode='markers', customdata=hover_texts,
                    marker=dict(size=7, color=marker_colors, line=dict(width=1.5, color='#111')),
                    hovertemplate="%{customdata}<extra></extra>", showlegend=False
                ))
                
                # Zoom Dinâmico do Eixo Y (Evita a "linha espremida")
                min_abs, max_abs = (min(abs_path) if abs_path else 0), (max(abs_path) if abs_path else 0)
                y_min = (int(min_abs) // 100) * 100
                y_max = ((int(max_abs) // 100) + 1) * 100
                if y_max - y_min < 100: 
                    y_min -= 50; y_max += 50
                
                tick_vals = list(range(y_min, y_max + 1, 100))
                tick_texts = []
                for v in tick_vals:
                    _, short_rank, _, b_color = get_rank_info_from_abs(v)
                    # O Pulo do Gato: O Eixo Y aceita HTML e exibe as cores exatas do Elo na lateral esquerda!
                    tick_texts.append(f"<b style='color:{b_color}'>{short_rank}</b>")
                
                fig_l.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                    xaxis=dict(visible=True, showgrid=False, tickmode='array', tickvals=[1, len(abs_path)//2, len(abs_path)], ticktext=["15 games ago", "8", "Last game"], tickfont=dict(color='#666', size=10)), 
                    # Eixo Y ativado, com linhas tracejadas em cada Elo, e usando os textos com as cores
                    yaxis=dict(visible=True, showgrid=True, gridcolor='#333', griddash='dot', zeroline=False, range=[y_min - 20, y_max + 20], tickmode='array', tickvals=tick_vals, ticktext=tick_texts, tickfont=dict(size=11)), 
                    margin=dict(l=10, r=10, t=10, b=10), height=160
                )
                
                st.plotly_chart(fig_l, use_container_width=True, config={'displayModeBar': False})
                
                safe_html(f"""
                <div style='display:flex; gap:8px; margin-top:5px; padding:0 10px 10px 10px;'>
                    <div class='metric-card'><p class='metric-val'>{dash['metrics']['fb_pct']}%</p><p class='metric-lbl'>FIRST BLOOD</p></div>
                    <div class='metric-card'><p class='metric-val'>{dash['metrics']['c_wards']}</p><p class='metric-lbl'>CTRL WARDS</p></div>
                </div>
                <div style='display:flex; gap:8px; padding:0 10px 10px 10px;'>
                    <div class='metric-card'><p class='metric-val'>{dash['metrics']['avg_vision']}</p><p class='metric-lbl'>AVG VISION</p></div>
                    <div class='metric-card'><p class='metric-val'>{dash['metrics']['dpm']}</p><p class='metric-lbl'>AVG DPM</p></div>
                </div>
                """)

        st.write("---")
        safe_html("<h3 style='color:#FFF; font-style:italic;'>RECENT MATCHES</h3>")
        
        for g in p_data['history']:
            is_w = g['win']
            b_c = "#1E88E5" if is_w else "#D32F2F"
            r_b_c = "#D32F2F" if is_w else "#1E88E5"
            st_b = f"<span style='background-color: {'rgba(30,136,229,0.2)' if is_w else 'rgba(211,47,47,0.2)'}; color: {b_c}; padding: 4px 8px; border-radius: 4px; font-weight: 900; font-size: 0.85rem; letter-spacing: 1px;'>{'VITÓRIA' if is_w else 'DERROTA'}</span>"
            
            csm = round(g['cs'] / max(g['duration']/60, 1), 1)
            kda_ratio = round((g['kills'] + g['assists']) / max(g['deaths'], 1), 2)
            
            if kda_ratio >= 4.0: kda_color = "#FFD700" 
            elif kda_ratio >= 3.0: kda_color = "#0ac8b9" 
            elif kda_ratio >= 2.0: kda_color = "#1E88E5" 
            else: kda_color = "#888"    
            
            team1_html = "".join([f"<div style='display:flex; align-items:center; gap:4px; margin-bottom:2px;'><img src='{get_champ_img(p['champ'])}' width='16' height='16' style='border-radius:3px;'><span style='white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:65px;' title='{p['name']}'>{p['name']}</span></div>" for p in g['team100']])
            team2_html = "".join([f"<div style='display:flex; align-items:center; gap:4px; margin-bottom:2px;'><img src='{get_champ_img(p['champ'])}' width='16' height='16' style='border-radius:3px;'><span style='white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:65px;' title='{p['name']}'>{p['name']}</span></div>" for p in g['team200']])
            
            card_html = f"""
            <div class='data-card' style='border-left: 8px solid {b_c}; background-color: rgba(255,255,255,0.02); padding: 0;'>
                <div style='display:flex; justify-content:space-between; align-items:center; padding: 12px;'>
                    
                    <div style='display:flex; align-items:center; gap:15px; width:30%;'>
                        <div style='text-align:center; min-width:80px;'>
                            {st_b}
                            <p style='color:#888; font-size:0.75rem; margin-top:10px;'><b>{g.get('queue', 'Ranked')}</b></p>
                            <p style='color:#888; font-size:0.7rem; margin:0;'>{g.get('time_ago', '')}</p>
                            <p style='color:#888; font-size:0.7rem; margin:0;'>{format_time(g.get('duration', 0))}</p>
                        </div>
                        <div style='position:relative;'>
                            <img src='{get_champ_img(g["champion"])}' width='60' style='border-radius:50%; border:2px solid {b_c};'>
                            <div style='position:absolute; bottom:-3px; right:-3px; background:#000; color:#FFF; font-size:0.6rem; font-weight:bold; border-radius:50%; border:1px solid {b_c}; width:20px; height:20px; display:flex; align-items:center; justify-content:center;'>{g.get('level', 1)}</div>
                        </div>
                        <div style='display:flex; flex-direction:column; gap:2px;'>
                            <img src='{get_spell_img(g.get("spells", [4,4])[0])}' width='22' style='border-radius:3px;'>
                            <img src='{get_spell_img(g.get("spells", [4,4])[1])}' width='22' style='border-radius:3px;'>
                        </div>
                        <div style='display:flex; flex-direction:row; gap:1px;'>
                            {get_rune_html(g.get('runes', {}).get('primary', 8100))} 
                            {get_rune_html(g.get('runes', {}).get('secondary', 8200))}
                        </div>
                    </div>
                    
                    <div style='width:12%; text-align:center;'>
                        <p style='color:#FFF; margin:0; font-size:1.1rem; font-weight:bold;'>{g.get('kills',0)} / <span style='color:#D32F2F;'>{g.get('deaths',0)}</span> / {g.get('assists',0)}</p>
                        <p style='color:{kda_color}; margin:0; font-size:0.85rem; font-weight:bold;'>{kda_ratio}:1 KDA</p>
                    </div>
                    
                    <div style='width:12%; text-align:center;'>
                        <p style='margin:0; color:#FFF; font-weight:bold; font-size:0.9rem;'>{g.get('cs',0)} CS</p>
                        <p style='margin:0; color:#888; font-size:0.8rem;'>({csm}/m)</p>
                        <p style='margin:2px 0 0 0; color:#FF2A2A; font-weight:bold; font-size:0.8rem;'>{g.get('kp', 0)}% KP</p>
                    </div>
                    
                    <div style='width:18%;'>{build_item_html(g.get('items', [0,0,0,0,0,0,0]))}</div>
                    
                    <div style='width:12%; display:flex; flex-direction:column; align-items:center; justify-content:center; border-left: 1px solid #333;'>
                        <p style='color:#888; font-size:0.6rem; font-weight:bold;'>OPONENTE</p>
                        <img src='{get_champ_img(g.get("rival_champ", "Unknown"))}' width='60' style='border-radius:50%; border:2px solid {r_b_c};'>
                        <p style='color:#FFF; margin:4px 0 0 0; font-size:0.75rem; font-weight:bold; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:80px;' title='{g.get("rival_name", "Inimigo")}'>{g.get("rival_name", "Inimigo")}</p>
                    </div>
                    
                    <div style='width:18%; display:flex; justify-content:space-between; font-size:0.65rem; color:#888; padding-left:10px; border-left: 1px solid #333;'>
                        <div style='display:flex; flex-direction:column; width:48%;'>{team1_html}</div>
                        <div style='display:flex; flex-direction:column; width:48%;'>{team2_html}</div>
                    </div>
                </div>
            </div>
            """
            safe_html(card_html)
            
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
    res = requests.post(f"{BACKEND_URL}/duel", json={"summoner": st.session_state.current_summoner, "match_id": st.session_state.match_id}, timeout=20)
    
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
            safe_html(f"""
            <div class='data-card' style='border-top: 8px solid #1E88E5; text-align:center; background:#111;'>
                <h4 style='color:#1E88E5 !important;'>JOGADOR 1 (VOCÊ)</h4>
                <img src='{get_champ_img(j['champion'])}' width='120' style='border-radius: 50%; border: 4px solid #1E88E5; box-shadow: 0 0 20px #1E88E544;'>
                <h1 style='font-size:2.5rem; margin-top:10px;'>{j['champion']}</h1>
                <h3>KDA: {j['kills']}/{j['deaths']}/{j['assists']}</h3>
                <div style='display:flex; justify-content:center; gap:5px;'>
                    {get_rune_html(j['runes']['primary'])} {get_rune_html(j['runes']['secondary'])}
                </div>
                {build_item_html(j['items'])}
            </div>
            """)
            
        with c_v: 
            safe_html("<div class='vs-logo'>VS</div>")
            
        with c_r:
            safe_html(f"""
            <div class='data-card' style='border-top: 8px solid #D32F2F; text-align:center; background:#111;'>
                <h4 style='color:#D32F2F !important;'>JOGADOR 2 (RIVAL)</h4>
                <img src='{get_champ_img(r['champion'])}' width='120' style='border-radius: 50%; border: 4px solid #D32F2F; box-shadow: 0 0 20px #D32F2F44;'>
                <h1 style='font-size:2.5rem; margin-top:10px;'>{r['champion']}</h1>
                <h3>KDA: {r['kills']}/{r['deaths']}/{r['assists']}</h3>
                <div style='display:flex; justify-content:center; gap:5px;'>
                    {get_rune_html(r['runes']['primary'])} {get_rune_html(r['runes']['secondary'])}
                </div>
                {build_item_html(r['items'])}
            </div>
            """)

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
