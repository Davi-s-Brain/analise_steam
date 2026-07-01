# 🎮 Steam Games Analytics

### Transforme sua biblioteca Steam em insights poderosos

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![R](https://img.shields.io/badge/R-4.0+-276DC3?style=for-the-badge&logo=r&logoColor=white)](https://r-project.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

---

**Analise sua biblioteca Steam** • **Descubra jogos para Steam Deck** • **Visualize suas estatísticas**

[🚀 Início Rápido](#-início-rápido) • [📊 Dashboard](#-dashboard) • [📈 Análises](#-análises) • [🎮 Steam Deck](#-steam-deck)


---

## ✨ O Que Este Projeto Faz

```
┌─────────────────────────────────────────────────────────────────┐
│  Steam API  ──►  Python  ──►  ProtonDB  ──►  Dashboard         │
│     │              │             │              │                │
│     ▼              ▼             ▼              ▼                │
│  Sua lista    Processamento   Compatível    Visualização       │
│  de jogos     + Metacritic    Steam Deck    interativa         │
└─────────────────────────────────────────────────────────────────┘
```

| Recurso | Descrição |
|---------|-----------|
| 🎯 **Extração Automática** | Busca todos os seus jogos via Steam API |
| 📊 **Scores Metacritic** | Notas de críticos para cada jogo |
| 🎮 **Steam Deck** | Status de compatibilidade via ProtonDB |
| 📈 **Dashboard** | Interface interativa para explorar dados |
| ⚡ **Rápido** | Processa 138 jogos em ~30 segundos |

---

## 🚀 Início Rápido

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/analise_steam.git
cd analise_steam
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

### 3. Configure suas credenciais

```bash
cp .env.example .env
# Edite .env com suas chaves de API
```

**Obtenha suas chaves:**
- 🔑 **Steam API**: https://steamcommunity.com/dev/apikey
- 🎯 **OpenCritic** (opcional): https://rapidapi.com/opencritic-opencritic-default/api/opencritic-api

### 4. Execute!

```bash
# Extrair dados (~30 segundos)
python scripts/python/main.py

# Abrir dashboard
streamlit run scripts/dashboard/app.py
```

---

## 📊 Dashboard

O dashboard interativo permite:

| Feature | Descrição |
|---------|-----------|
| 🔍 **Filtros** | Busque por nome, status, horas jogadas |
| 📊 **Gráficos** | Visualizações interativas com Plotly |
| 🎮 **Steam Deck** | Filtre por compatibilidade |
| 📈 **Metacritic** | Top scores e distribuição |
| ⏱ **HowLongToBeat** | Duração estimada vs horas jogadas |
| 📥 **Export** | Baixe dados filtrados em CSV |

**Abrir dashboard:**
```bash
streamlit run scripts/dashboard/app.py
```

**Acesse:** http://localhost:8501

---

## 📈 Análises Disponíveis

### 🎮 Steam Deck

Classificação automática baseada no ProtonDB:

| Tier | Significado | Ação |
|------|-------------|------|
| ✅ **Verified** | Funciona perfeitamente | Jogue tranquilo! |
| 🟡 **Playable** | Funciona com ajustes | Pode jogar |
| ⚠️ **Unsupported** | Não funciona | Evite |

### 📊 Metacritic

Scores de críticos especializados:

| Faixa | Classificação |
|-------|---------------|
| 90-100 | 🏆 Excelente |
| 75-89 | 👍 Muito Bom |
| 60-74 | 😊 Bom |
| 40-59 | 😐 Regular |
| 0-39 | 😕 Ruim |

### 📈 Estatísticas

- **Top jogos** por tempo de jogo
- **Distribuição** Steam Deck
- **Correlação** horas vs scores
- **Backlog** análise

---

## 🏗️ Arquitetura

```
analise_steam/
├── 📁 data/
│   ├── raw/                    # Dados brutos da Steam
│   └── processed/              # Dados processados
├── 📁 scripts/
│   ├── python/
│   │   ├── main.py             # Extração de dados
│   │   └── api_integrations.py # Integrações API
│   ├── dashboard/
│   │   └── app.py              # Dashboard Streamlit
│   └── R/
│       └── analise_steam_report.R  # Análise estatística
├── 📁 outputs/                 # Gráficos gerados
├── 📄 requirements.txt         # Dependências Python
├── 📄 .env.example             # Template de configuração
└── 📄 AGENTS.md                # Guia para agentes AI
```

---

## 🔧 APIs Integradas

| API | Uso | Status |
|-----|-----|--------|
| 🎮 **Steam API** | Dados da biblioteca | ✅ Funcionando |
| 🎯 **ProtonDB** | Compatibilidade Steam Deck | ✅ Funcionando |
| 📊 **Metacritic** | Scores de críticos | ✅ Funcionando |
| ⏱ **HowLongToBeat** | Duração estimada dos jogos | ✅ Funcionando |
| 🎯 **OpenCritic** | Scores alternativos | ⚡ Opcional |

---

## 📊 Exemplo de Uso

### Via Python

```python
from scripts.python.api_integrations import ProtonDBAPI, MetacriticAPI, HowLongToBeatAPI

# Verificar compatibilidade Steam Deck
status = ProtonDBAPI.get_steam_deck_status(413150)  # Stardew Valley
print(f"Stardew Valley: {status}")  # Verified

# Buscar score Metacritic
score = MetacriticAPI.search_game_score("Stardew Valley")
print(f"Score: {score}")  # 89

# Buscar duração estimada (HowLongToBeat)
hltb = HowLongToBeatAPI.search_game("Stardew Valley")
if hltb:
    print(f"Campanha: {hltb['hltb_main_story']}h")
    print(f"Completista: {hltb['hltb_completionist']}h")
```

### Via Terminal

```bash
# Extrair e processar dados
python scripts/python/main.py

# Gerar relatório R
Rscript scripts/R/analise_steam_report.R

# Abrir dashboard
streamlit run scripts/dashboard/app.py
```

---

## 🎯 Comandos Úteis

| Comando | Descrição |
|---------|-----------|
| `python scripts/python/main.py` | Extrair dados da Steam |
| `streamlit run scripts/dashboard/app.py` | Abrir dashboard |
| `Rscript scripts/R/analise_steam_report.R` | Gerar gráficos |
| `pip install -r requirements.txt` | Instalar dependências |

---

## 🤝 Contribuindo

Contribuições são bem-vindas! 

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

---

## 📝 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

<div align="center">

**Feito com ❤️ para gamers que querem entender sua biblioteca**

[⬆ Voltar ao topo](#-steam-games-analytics)

</div>
]]>