import streamlit as st
import re

def load_css(file_name):
    """Carrega as customizações CSS a partir de um arquivo externo."""
    with open(file_name, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

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
            html += "<div style='width:28px; height:28px; background-color:rgba(0,0,0,0.5); border:1px solid #333; border-radius:8px;'></div>"
        else: 
            html += f"<img src='https://ddragon.leagueoflegends.com/cdn/15.4.1/img/item/{item}.png' width='28' height='28' style='border:1px solid #555; border-radius:8px;'>"
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
        <div style="display:flex; width:100%; height:12px; background-color:#111; overflow:hidden; border: 1px solid #333; border-radius: 8px;">
            <div style="width:{pct1}%; background-color:#1E88E5; border-right: 2px solid #000;"></div>
            <div style="width:{pct2}%; background-color:#D32F2F;"></div>
        </div>
    </div>
    """

ADS_HTML = """
<div style='background: repeating-linear-gradient(45deg, #111, #111 10px, #1a1a1a 10px, #1a1a1a 20px); border: 2px dashed #555; padding: 40px 20px; text-align: center; margin-bottom: 20px; color: #555; font-weight: 900; font-style: italic; min-height: 250px; display:flex; flex-direction:column; justify-content:center; border-radius:16px;'>
    <h3>ADVERTISEMENT</h3><p>300x250</p>
</div>
<div style='background: repeating-linear-gradient(45deg, #111, #111 10px, #1a1a1a 10px, #1a1a1a 20px); border: 2px dashed #555; padding: 40px 20px; text-align: center; margin-bottom: 20px; color: #555; font-weight: 900; font-style: italic; min-height: 600px; display:flex; flex-direction:column; justify-content:center; border-radius:16px;'>
    <h3>ADVERTISEMENT</h3><p>300x600<br>Premium Space</p>
</div>
"""

def build_overview_header_html(p_data):
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
    status_msg = "🔥 Jogador em chamas!" if winrate >= 60 else ("📈 Escalando de forma constante." if winrate >= 50 else "🧊 Fase fria, precisa focar mais.")
    
    badge_styles = {
        "KDA Player": ("⭐", "#FFD700", "rgba(255, 215, 0, 0.15)"),
        "Damage Dealer": ("🔥", "#FF2A2A", "rgba(255, 42, 42, 0.15)"),
        "Vision Focused": ("👁️", "#9d48e0", "rgba(157, 72, 224, 0.15)"),
        "Early Aggressor": ("⚔️", "#FF8C00", "rgba(255, 140, 0, 0.15)"),
        "Team Player": ("🤝", "#209b58", "rgba(32, 155, 88, 0.15)"),
        "Objective Focused": ("🎯", "#1E88E5", "rgba(30, 136, 229, 0.15)")
    }
    
    badges_html = ""
    for b in dash['badges']:
        icon, color, bg = badge_styles.get(b, ("✨", "#0ac8b9", "rgba(10, 200, 185, 0.15)"))
        badges_html += f"<span class='profile-badge' style='background-color: {bg}; border: 1px solid {color}66; padding: 6px 14px; border-radius: 20px; font-size: 0.8rem; color: {color}; font-weight: 900; text-transform: uppercase; box-shadow: 0 4px 10px {bg}; display: inline-flex; align-items: center; gap: 6px; letter-spacing: 0.5px;'><span style='font-size: 1rem;'>{icon}</span> {b}</span>"

    win_color = "#0ac8b9" if winrate >= 50 else "#D32F2F"

    return f"""
    <div class='overview-header' style='margin-bottom: 20px;'>
        <div style='display:flex; align-items:center; gap:25px;'>
            <img src='{icon_url}' width='100' style='border: 3px solid #333; border-radius: 24px; box-shadow: 0 0 15px rgba(0,0,0,0.5);'>
            <div>
                <h1 style='margin:0 0 5px 0; color:#FFF !important; font-size: 2.2rem; letter-spacing: 1px;'>{p_data['player']} <span style='color:#888; font-size: 1.4rem; text-transform:none; font-weight: normal;'>#{p_data.get('tag', '')}</span></h1>
                <div style='margin-top:12px; display: flex; flex-wrap: wrap; gap: 8px;'>{badges_html}</div>
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
                <div style='width:100%; height:8px; background:#222; border-radius:8px; margin-top:4px; border: 1px solid #111;'>
                    <div style='width:{winrate}%; height:100%; background:{win_color}; border-radius:8px; box-shadow: 0 0 8px {win_color};'></div>
                </div>
                <p style='margin: 6px 0 0 0; font-size: 0.75rem; color: #AAA; font-style: italic; text-align: right;'>{status_msg}</p>
            </div>
        </div>
    </div>
    """

def build_match_card_html(g):
    is_w = g['win']
    b_c = "#1E88E5" if is_w else "#D32F2F"
    r_b_c = "#D32F2F" if is_w else "#1E88E5"
    st_b = f"<span style='background-color: {'rgba(30,136,229,0.2)' if is_w else 'rgba(211,47,47,0.2)'}; color: {b_c}; padding: 4px 10px; border-radius: 12px; font-weight: 900; font-size: 0.85rem; letter-spacing: 1px;'>{'VITÓRIA' if is_w else 'DERROTA'}</span>"
    
    csm = round(g['cs'] / max(g['duration']/60, 1), 1)
    kda_ratio = round((g['kills'] + g['assists']) / max(g['deaths'], 1), 2)
    
    if kda_ratio >= 4.0: kda_color = "#FFD700" 
    elif kda_ratio >= 3.0: kda_color = "#0ac8b9" 
    elif kda_ratio >= 2.0: kda_color = "#1E88E5" 
    else: kda_color = "#888"    
    
    team1_html = "".join([f"<div style='display:flex; align-items:center; gap:4px; margin-bottom:2px;'><img src='{get_champ_img(p['champ'])}' width='16' height='16' style='border-radius:6px;'><span style='white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:65px;' title='{p['name']}'>{p['name']}</span></div>" for p in g['team100']])
    team2_html = "".join([f"<div style='display:flex; align-items:center; gap:4px; margin-bottom:2px;'><img src='{get_champ_img(p['champ'])}' width='16' height='16' style='border-radius:6px;'><span style='white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:65px;' title='{p['name']}'>{p['name']}</span></div>" for p in g['team200']])
    
    feedbacks_html = "".join([f"<span style='background-color:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); color:#DDD; font-size:0.65rem; padding:4px 10px; border-radius:20px; font-weight:bold; letter-spacing:0.5px;'>{f}</span>" for f in g.get('feedbacks', [])])

    return f"""
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
                    <img src='{get_spell_img(g.get("spells", [4,4])[0])}' width='22' style='border-radius:6px;'>
                    <img src='{get_spell_img(g.get("spells", [4,4])[1])}' width='22' style='border-radius:6px;'>
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
        <div style='padding: 8px 12px; background-color: rgba(0,0,0,0.3); border-top: 1px solid #222; display:flex; flex-wrap:wrap; gap:6px; border-bottom-left-radius: 16px; border-bottom-right-radius: 16px;'>
            {feedbacks_html}
        </div>
    </div>
    """

def build_duel_player_card(player, title, color):
    return f"""
    <div class='data-card' style='border-top: 8px solid {color}; text-align:center; background:#111;'>
        <h4 style='color:{color} !important;'>{title}</h4>
        <img src='{get_champ_img(player['champion'])}' width='120' style='border-radius: 50%; border: 4px solid {color}; box-shadow: 0 0 20px {color}44;'>
        <h1 style='font-size:2.5rem; margin-top:10px;'>{player['champion']}</h1>
        <h3>KDA: {player['kills']}/{player['deaths']}/{player['assists']}</h3>
        <div style='display:flex; justify-content:center; gap:5px;'>
            {get_rune_html(player['runes']['primary'])} {get_rune_html(player['runes']['secondary'])}
        </div>
        {build_item_html(player['items'])}
    </div>
    """