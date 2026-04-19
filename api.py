import os
import time
import requests
import concurrent.futures
import urllib.parse
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from functools import lru_cache
from flask_caching import Cache
from analyzer import analisar_desempenho, comparar_duelo

load_dotenv()
app = Flask(__name__)
CORS(app)

# Configuração do Cache (Armazena na memória RAM do servidor)
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})

API_KEY = os.getenv("RIOT_API_KEY", "").replace('"', '').replace("'", "").strip()
HEADERS = {"X-Riot-Token": API_KEY}

@lru_cache(maxsize=1000)
def get_puuid(name, tag):
    url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{urllib.parse.quote(name)}/{urllib.parse.quote(tag)}"
    res = requests.get(url, headers=HEADERS)
    return res.json().get("puuid") if res.status_code == 200 else None

def get_queue_name(q_id):
    queues = {420: "Ranked Solo", 440: "Ranked Flex", 400: "Normal Draft", 430: "Normal Blind", 450: "ARAM", 1700: "Arena", 490: "Quickplay"}
    return queues.get(q_id, "Normal")

@lru_cache(maxsize=1000)
def fetch_match_data(m_id):
    """Busca os detalhes da partida com cache para não repetir requisições à Riot."""
    url_match = f"https://americas.api.riotgames.com/lol/match/v5/matches/{m_id}"
    
    for _ in range(3): # Tenta até 3 vezes em caso de Rate Limit
        res = requests.get(url_match, headers=HEADERS)
        if res.status_code == 200:
            return res.json()
        elif res.status_code == 429:
            time.sleep(1.2) # Se a Riot pedir para desacelerar, o código espera 1.2 segundos e tenta de novo
        else:
            break
    return None

def history_cache_key():
    data = request.get_json() or {}
    return f"history_{data.get('summoner', '')}"

@app.route('/history', methods=['POST'])
@cache.cached(timeout=120, key_prefix=history_cache_key) # Cooldown de 2 minutos por jogador
def get_history():
    data = request.json
    riot_id = data.get('summoner', '')
    
    if '#' not in riot_id: 
        return jsonify({"error": "Formato inválido! Use Nome#TAG"}), 400
    
    try:
        name, tag = riot_id.split('#')
        name = name.strip()
        tag = tag.strip()
        
        puuid = get_puuid(name, tag)
        if not puuid: 
            return jsonify({"error": "Jogador não encontrado"}), 404

        # Ainda precisamos do Summoner-V4 apenas para pegar o Ícone de Perfil e o Level
        url_summoner = f"https://br1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
        sum_res = requests.get(url_summoner, headers=HEADERS)
        
        profile_icon, tier, rank, lp, wins, losses = 1, "UNRANKED", "", 0, 0, 0
        rank_type = "Ranked Solo"
        
        if sum_res.status_code == 200:
            sum_data = sum_res.json()
            profile_icon = sum_data.get("profileIconId", 1)
            
            # 🟢 A SOLUÇÃO: Buscando o Elo diretamente pelo PUUID
            url_league = f"https://br1.api.riotgames.com/lol/league/v4/entries/by-puuid/{puuid}"
            league_res = requests.get(url_league, headers=HEADERS)
            
            if league_res.status_code == 200:
                entries = league_res.json()
                
                solo_q = next((q for q in entries if q.get("queueType") == "RANKED_SOLO_5x5"), None)
                flex_q = next((q for q in entries if q.get("queueType") == "RANKED_FLEX_SR"), None)
                
                valid_q = solo_q if solo_q else flex_q
                if valid_q:
                    tier = valid_q.get("tier", "UNRANKED")
                    rank = valid_q.get("rank", "")
                    lp = valid_q.get("leaguePoints", 0)
                    wins = valid_q.get("wins", 0)
                    losses = valid_q.get("losses", 0)
                    rank_type = "Ranked Solo" if valid_q.get("queueType") == "RANKED_SOLO_5x5" else "Ranked Flex"

        url_matches = f"https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count=15"
        match_ids = requests.get(url_matches, headers=HEADERS).json()

        def fetch_match(m_id): return m_id, fetch_match_data(m_id)

        matches_dict = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(fetch_match, m_id) for m_id in match_ids]
            for future in concurrent.futures.as_completed(futures):
                m_id, match_data = future.result()
                if match_data:
                    matches_dict[m_id] = match_data

        detalhes_partidas = []
        aggr = {"k":0, "d":0, "a":0, "cs":0, "vis":0, "dmg":0, "fb":0, "cw":0}
        champ_stats = {}
        total_duration = 0
        win_loss_seq = []

        for m_id in match_ids:
            match_data = matches_dict.get(m_id)
            if not match_data: continue
            
            info = match_data.get("info", {})
            duration = info.get("gameDuration", 1)
            queue_name = get_queue_name(info.get("queueId", 0))
            
            diff = int(time.time() * 1000) - info.get("gameCreation", 0)
            days = diff // (1000 * 60 * 60 * 24)
            time_ago = f"{days}d ago" if days > 0 else f"{diff // (1000 * 60 * 60)}h ago"
            
            main_p, team_kills = None, {100: 0, 200: 0}
            team100, team200 = [], []
            
            for p in info.get("participants", []):
                t_id = p.get("teamId", 100)
                team_kills[t_id] += p.get("kills", 0)
                player_obj = {
                    "champ": p.get("championName", "Unknown"), 
                    "name": p.get("riotIdGameName", p.get("summonerName", "Unknown")), 
                    "lane": p.get("teamPosition", "")
                }
                if t_id == 100: team100.append(player_obj)
                else: team200.append(player_obj)
                if p.get("puuid") == puuid: main_p = p

            if not main_p: continue

            rival_champ = "Unknown"
            rival_name = "Oponente"
            enemy_team = team200 if main_p.get("teamId") == 100 else team100
            for px in enemy_team:
                if px["lane"] == main_p.get("teamPosition") and px["lane"] not in ["", "Invalid", "NONE"]:
                    rival_champ = px["champ"]
                    rival_name = px["name"]
                    break
            if rival_champ == "Unknown" and enemy_team:
                rival_champ = enemy_team[0]["champ"]
                rival_name = enemy_team[0]["name"]

            tk = max(team_kills.get(main_p.get("teamId", 100), 1), 1)
            kp = round(((main_p.get("kills", 0) + main_p.get("assists", 0)) / tk) * 100)
            cs = main_p.get("totalMinionsKilled", 0) + main_p.get("neutralMinionsKilled", 0)
            is_win = main_p.get("win", False)
            
            win_loss_seq.append(1 if is_win else -1)
            
            aggr["k"] += main_p.get("kills", 0)
            aggr["d"] += main_p.get("deaths", 0)
            aggr["a"] += main_p.get("assists", 0)
            aggr["cs"] += cs
            aggr["vis"] += main_p.get("visionScore", 0)
            aggr["dmg"] += main_p.get("totalDamageDealtToChampions", 0)
            aggr["cw"] += main_p.get("visionWardsBoughtInGame", 0)
            if main_p.get("firstBloodKill") or main_p.get("firstBloodAssist"): 
                aggr["fb"] += 1
                
            total_duration += duration
            
            c_name = main_p.get("championName", "Unknown")
            if c_name not in champ_stats: 
                champ_stats[c_name] = {"games": 0, "wins": 0, "kills": 0, "deaths": 0, "assists": 0, "cs": 0}
            champ_stats[c_name]["games"] += 1
            if is_win: champ_stats[c_name]["wins"] += 1
            champ_stats[c_name]["kills"] += main_p.get("kills", 0)
            champ_stats[c_name]["deaths"] += main_p.get("deaths", 0)
            champ_stats[c_name]["assists"] += main_p.get("assists", 0)
            champ_stats[c_name]["cs"] += cs

            styles = main_p.get("perks", {}).get("styles", [])
            rune_primary = styles[0].get("style", 0) if len(styles) > 0 else 0
            rune_secondary = styles[1].get("style", 0) if len(styles) > 1 else 0

            analise = analisar_desempenho(main_p.get("kills", 0), main_p.get("deaths", 0), main_p.get("assists", 0), is_win)
            
            detalhes_partidas.append({
                "id": m_id, "queue": queue_name, "time_ago": time_ago,
                "champion": c_name, "level": main_p.get("champLevel", 0), "win": is_win,
                "kills": main_p.get("kills", 0), "deaths": main_p.get("deaths", 0), "assists": main_p.get("assists", 0),
                "kda": f"{main_p.get('kills', 0)}/{main_p.get('deaths', 0)}/{main_p.get('assists', 0)}",
                "lane": main_p.get("teamPosition", "NONE"), "cs": cs, "duration": duration, "kp": kp,
                "items": [main_p.get(f"item{i}", 0) for i in range(7)],
                "spells": [main_p.get("summoner1Id", 0), main_p.get("summoner2Id", 0)],
                "runes": {"primary": rune_primary, "secondary": rune_secondary},
                "feedbacks": analise["feedbacks"], "team100": team100, "team200": team200, 
                "rival_champ": rival_champ, "rival_name": rival_name,
                "vision": main_p.get("visionScore", 0),
                "damage": main_p.get("totalDamageDealtToChampions", 0),
                "c_wards": main_p.get("visionWardsBoughtInGame", 0),
                "first_blood": 1 if (main_p.get("firstBloodKill") or main_p.get("firstBloodAssist")) else 0
            })
        
        g_count = len(detalhes_partidas) if len(detalhes_partidas) > 0 else 1
        mins = total_duration / 60 if total_duration > 0 else 1
        
        momentum, acc = [], 0
        for val in reversed(win_loss_seq): 
            acc += val
            momentum.append(acc)
            
        badges = []
        if (aggr["k"] + aggr["a"]) / max(aggr["d"], 1) >= 3.5: badges.append("KDA Player")
        if aggr["dmg"] / mins > 600: badges.append("Damage Dealer")
        if aggr["cw"] / g_count > 2: badges.append("Vision Focused")
        if aggr["fb"] / g_count > 0.2: badges.append("Early Aggressor")
        if len(badges) == 0: badges.extend(["Team Player", "Objective Focused"])
        
        dashboard = {
            "radar": {
                "Combat": min(100, int((aggr["k"]+aggr["a"])/max(aggr["d"],1) * 20)),
                "Farm": min(100, int((aggr["cs"]/mins) * 10)),
                "Vision": min(100, int((aggr["vis"]/mins) * 40)),
                "Aggression": min(100, int((aggr["dmg"]/mins) / 10)),
                "Survival": 100 - min(100, int((aggr["d"]/g_count) * 10))
            },
            "badges": badges[:3],
            "metrics": {
                "c_wards": round(aggr["cw"] / g_count, 1), 
                "fb_pct": round((aggr["fb"] / g_count) * 100),
                "avg_vision": round(aggr["vis"] / g_count), 
                "dpm": round(aggr["dmg"] / mins)
            },
            "champs": champ_stats, 
            "momentum": momentum 
        }

        return jsonify({
            "player": name, "tag": tag, "profile_icon": profile_icon, 
            "tier": tier, "rank": rank, "lp": lp, "wins": wins, "losses": losses, 
            "rank_type": rank_type, 
            "history": detalhes_partidas, "dashboard": dashboard
        })
    except Exception as e: 
        return jsonify({"error": str(e)}), 500

def duel_cache_key():
    data = request.get_json() or {}
    return f"duel_{data.get('match_id', '')}"

@app.route('/duel', methods=['POST'])
@cache.cached(timeout=3600, key_prefix=duel_cache_key) # Cache de 1 hora (Partidas passadas nunca mudam os dados)
def get_duel():
    data = request.json
    riot_id = data.get('summoner', '')
    match_id = data.get('match_id')
    try:
        name, tag = riot_id.split('#')
        puuid = get_puuid(name, tag)
        match_data = fetch_match_data(match_id)
        if not match_data:
            return jsonify({"error": "Partida não encontrada."}), 404
        duration = match_data.get("info", {}).get("gameDuration", 0)
        jogador, rival = None, None
        
        for p in match_data["info"]["participants"]:
            if p["puuid"] == puuid:
                jogador = {
                    "champion": p.get("championName", "Unknown"), "kills": p.get("kills", 0), "deaths": p.get("deaths", 0), "assists": p.get("assists", 0), 
                    "gold": p.get("goldEarned", 0), "damage": p.get("totalDamageDealtToChampions", 0), "lane": p.get("teamPosition", ""), "team": p.get("teamId", 0),
                    "cs": p.get("totalMinionsKilled", 0) + p.get("neutralMinionsKilled", 0), "vision": p.get("visionScore", 0), "obj_damage": p.get("damageDealtToObjectives", 0),
                    "items": [p.get(f"item{i}", 0) for i in range(7)],
                    "runes": {"primary": p.get("perks", {}).get("styles", [{}])[0].get("style", 0) if p.get("perks", {}).get("styles") else 0, "secondary": p.get("perks", {}).get("styles", [{}, {}])[1].get("style", 0) if len(p.get("perks", {}).get("styles", [])) > 1 else 0}
                }
                break
                
        if jogador:
            for p in match_data["info"]["participants"]:
                if p.get("teamId") != jogador["team"]:
                    if not rival or p.get("teamPosition") == jogador["lane"]:
                        rival = {
                            "champion": p.get("championName", "Unknown"), "kills": p.get("kills", 0), "deaths": p.get("deaths", 0), "assists": p.get("assists", 0), 
                            "gold": p.get("goldEarned", 0), "damage": p.get("totalDamageDealtToChampions", 0), "cs": p.get("totalMinionsKilled", 0) + p.get("neutralMinionsKilled", 0),
                            "vision": p.get("visionScore", 0), "obj_damage": p.get("damageDealtToObjectives", 0), "items": [p.get(f"item{i}", 0) for i in range(7)],
                            "runes": {"primary": p.get("perks", {}).get("styles", [{}])[0].get("style", 0) if p.get("perks", {}).get("styles") else 0, "secondary": p.get("perks", {}).get("styles", [{}, {}])[1].get("style", 0) if len(p.get("perks", {}).get("styles", [])) > 1 else 0}
                        }
                    if p.get("teamPosition") == jogador["lane"]: break 
        
        if not jogador or not rival: 
            return jsonify({"error": "Não foi possível identificar duelo."}), 400
            
        return jsonify({
            "jogador": jogador, "rival": rival, "analise": comparar_duelo(jogador, rival), "duration": duration
        })
    except Exception as e: 
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True, threaded=True)
