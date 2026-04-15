# ⚔️ VERSUS.LOL | Arena Dashboard

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32.0-FF4B4B.svg)
![Plotly](https://img.shields.io/badge/Plotly-5.19.0-3F4F75.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

O **VERSUS.LOL** é um dashboard analítico avançado para jogadores de League of Legends. Ele vai além do histórico tradicional de partidas, oferecendo uma visão profunda sobre o *momentum* do jogador, análise de campeões e um simulador de duelo direto (1v1).

## 🚀 Funcionalidades Principais (Foco nas Últimas 15 Partidas)

* **📈 LP Progress Tracking (Engenharia Reversa de MMR):** Um motor gráfico customizado que calcula e exibe a evolução exata de Pontos de Liga (LP) do jogador nas últimas partidas. A linha do gráfico se adapta dinamicamente às cores oficiais da Riot Games baseadas no Elo do jogador naquele exato momento.
* **🕸️ Performance Radar (GPI):** Gráfico interativo minimalista que mapeia o estilo de jogo do invocador (Combate, Agressividade, Visão, Farm e Sobrevivência).
* **⚔️ Combate Direto (Análise 1v1):** Ferramenta exclusiva que isola o jogador e seu oponente de rota de uma partida específica, comparando Ouro/Minuto, Dano, Farm e Visão para definir quem realmente "amassou" na lane phase.
* **📊 Histórico Rico:** Visualização limpa e premium de partidas recentes, incluindo feitiços, runas (primárias e secundárias), KDA, KP% e itens.

## 🛠️ Tecnologias Utilizadas

* **Frontend:** Python, [Streamlit](https://streamlit.io/) (com injeção avançada de HTML/CSS customizado)
* **Visualização de Dados:** [Plotly](https://plotly.com/python/)
* **Backend/Integração:** Servidor próprio consumindo a API oficial da Riot Games via `requests`.

## ⚙️ Como executar o projeto localmente

Siga os passos abaixo para rodar o dashboard na sua máquina:

1. **Clone o repositório:**
   ```bash
   git clone [https://github.com/SEU_USUARIO/versus-lol.git](https://github.com/SEU_USUARIO/versus-lol.git)
   cd versus-lol
