def analisar_desempenho(kills, deaths, assists, win):
    kda = round((kills + assists) / max(deaths, 1), 2)
    feedbacks = []
    
    if kda >= 3.0: feedbacks.append("🔥 KDA Excelente")
    elif kda < 1.5: feedbacks.append("⚠️ KDA Baixo")
        
    if deaths > 8: feedbacks.append("💀 Muitas mortes")
    elif deaths <= 3: feedbacks.append("🛡️ Sobrevivência Alta")

    if win: feedbacks.append("🏆 Impacto Positivo na Vitória")
    else: feedbacks.append("❌ Não conseguiu carregar")

    return {"kda_ratio": kda, "feedbacks": feedbacks}

def comparar_duelo(jogador, rival):
    pontos_jogador = 0
    pontos_rival = 0
    
    # 1. Comparação de KDA
    kda_j = (jogador.get('kills', 0) + jogador.get('assists', 0)) / max(jogador.get('deaths', 1), 1)
    kda_r = (rival.get('kills', 0) + rival.get('assists', 0)) / max(rival.get('deaths', 1), 1)
    if kda_j > kda_r: pontos_jogador += 1
    elif kda_r > kda_j: pontos_rival += 1
    
    # 2. Comparação de Ouro
    if jogador.get('gold', 0) > rival.get('gold', 0) + 500: pontos_jogador += 1
    elif rival.get('gold', 0) > jogador.get('gold', 0) + 500: pontos_rival += 1
    
    # 3. Comparação de Dano
    if jogador.get('damage', 0) > rival.get('damage', 0): pontos_jogador += 1
    elif rival.get('damage', 0) > jogador.get('damage', 0): pontos_rival += 1

    # 4. Comparação de Farm
    if jogador.get('cs', 0) > rival.get('cs', 0) + 15: pontos_jogador += 1
    elif rival.get('cs', 0) > jogador.get('cs', 0) + 15: pontos_rival += 1

    # 5. Comparação de Visão
    if jogador.get('vision', 0) > rival.get('vision', 0) + 5: pontos_jogador += 1
    elif rival.get('vision', 0) > jogador.get('vision', 0) + 5: pontos_rival += 1
    
    # Veredito Final
    if pontos_jogador > pontos_rival + 1:
        veredito = "🏆 VOCÊ AMASSOU NA ROTA!"
        cor = "#1E88E5" # Azul
    elif pontos_rival > pontos_jogador + 1:
        veredito = "💀 VOCÊ FOI DOMINADO."
        cor = "#D32F2F" # Vermelho
    else:
        veredito = "⚔️ DUELO EQUILIBRADO."
        cor = "#FFFFFF" # Branco
        
    return {
        "veredito": veredito, 
        "cor": cor, 
        "kda_jogador": round(kda_j, 2), 
        "kda_rival": round(kda_r, 2)
    }