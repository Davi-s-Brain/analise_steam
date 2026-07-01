"""
Dashboard Interativo de Análise Steam
=====================================
Visualize, filtre e classifique sua biblioteca de jogos Steam.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ==================== CONFIGURAÇÃO ====================

st.set_page_config(
    page_title="Steam Games Dashboard",
    page_icon="🎮",
    layout="wide"
)

# ==================== CARREGAR DADOS ====================

@st.cache_data
def load_data():
    """Carrega dados processados do CSV"""
    csv_path = Path("/home/dsouza/Documentos/Projetinhos/analise_steam/data/processed/steam_games_processed.csv")
    
    if not csv_path.exists():
        st.error("Dados não encontrados. Execute primeiro: `python scripts/python/main.py`")
        return None
    
    df = pd.read_csv(csv_path)
    
    # Converter tipos com fallback para colunas ausentes
    df['playtime_hours'] = pd.to_numeric(df.get('playtime_hours', 0), errors='coerce').fillna(0)
    df['is_backlog'] = df.get('is_backlog', 'False').astype(str) == 'True'
    df['metacritic_score'] = pd.to_numeric(df.get('metacritic_score'), errors='coerce')
    
    # Colunas novas (podem não existir no CSV antigo)
    if 'protondb_score' in df.columns:
        df['protondb_score'] = pd.to_numeric(df['protondb_score'], errors='coerce').fillna(0)
    else:
        df['protondb_score'] = 0
    
    if 'protondb_tier' not in df.columns:
        df['protondb_tier'] = 'unknown'
    
    # Colunas HLTB (podem não existir no CSV antigo)
    for col in ['hltb_main_story', 'hltb_main_extra', 'hltb_completionist', 'hltb_all_styles']:
        if col not in df.columns:
            df[col] = 0
    for col in ['hltb_main_story', 'hltb_main_extra', 'hltb_completionist', 'hltb_all_styles']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    return df

df = load_data()

if df is None:
    st.stop()

# ==================== SIDEBAR - FILTROS ====================

st.sidebar.header("🔍 Filtros")

# Filtro de busca
search_term = st.sidebar.text_input("Buscar jogo:", "")

# Filtro de backlog
backlog_filter = st.sidebar.selectbox(
    "Status:",
    ["Todos", "Jogados", "Backlog"]
)

# Filtro Steam Deck
deck_options = ["Todos"] + sorted(df['steam_deck_status'].unique().tolist())
deck_filter = st.sidebar.selectbox("Steam Deck:", deck_options)

# Filtro ProtonDB Tier
tier_options = ["Todos"] + sorted(df['protondb_tier'].unique().tolist())
tier_filter = st.sidebar.selectbox("ProtonDB Tier:", tier_options)

# Filtro de horas
min_hours, max_hours = st.sidebar.slider(
    "Horas jogadas:",
    min_value=0.0,
    max_value=float(df['playtime_hours'].max()),
    value=(0.0, float(df['playtime_hours'].max())),
    step=1.0
)

# Filtro Metacritic
has_mc = st.sidebar.checkbox("Apenas com score Metacritic", value=False)

# Filtro HLTB duração
st.sidebar.markdown("---")
st.sidebar.markdown("**⏱ Duração HLTB**")

duration_filter = st.sidebar.selectbox(
    "Categoria de duração:",
    ["Todas", "Muito Curta (<5h)", "Curta (5-15h)", "Média (15-30h)", "Longa (30-60h)", "Muito Longa (>60h)"]
)

# ==================== APLICAR FILTROS ====================

filtered_df = df.copy()

# Busca por nome
if search_term:
    filtered_df = filtered_df[filtered_df['name'].str.contains(search_term, case=False, na=False)]

# Filtro backlog
if backlog_filter == "Jogados":
    filtered_df = filtered_df[~filtered_df['is_backlog']]
elif backlog_filter == "Backlog":
    filtered_df = filtered_df[filtered_df['is_backlog']]

# Filtro Steam Deck
if deck_filter != "Todos":
    filtered_df = filtered_df[filtered_df['steam_deck_status'] == deck_filter]

# Filtro Tier
if tier_filter != "Todos":
    filtered_df = filtered_df[filtered_df['protondb_tier'] == tier_filter]

# Filtro horas
filtered_df = filtered_df[
    (filtered_df['playtime_hours'] >= min_hours) &
    (filtered_df['playtime_hours'] <= max_hours)
]

# Filtro Metacritic
if has_mc:
    filtered_df = filtered_df[filtered_df['metacritic_score'].notna()]

# Filtro duração HLTB
if duration_filter != "Todas":
    if duration_filter == "Muito Curta (<5h)":
        filtered_df = filtered_df[filtered_df['hltb_all_styles'] < 5]
    elif duration_filter == "Curta (5-15h)":
        filtered_df = filtered_df[(filtered_df['hltb_all_styles'] >= 5) & (filtered_df['hltb_all_styles'] < 15)]
    elif duration_filter == "Média (15-30h)":
        filtered_df = filtered_df[(filtered_df['hltb_all_styles'] >= 15) & (filtered_df['hltb_all_styles'] < 30)]
    elif duration_filter == "Longa (30-60h)":
        filtered_df = filtered_df[(filtered_df['hltb_all_styles'] >= 30) & (filtered_df['hltb_all_styles'] < 60)]
    elif duration_filter == "Muito Longa (>60h)":
        filtered_df = filtered_df[filtered_df['hltb_all_styles'] >= 60]

# ==================== HEADER ====================

st.title("🎮 Steam Games Dashboard")
st.markdown(f"**{len(filtered_df)}** jogos encontrados de **{len(df)}** totais")

# ==================== MÉTRICAS GERAIS ====================

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "Total de Horas",
        f"{filtered_df['playtime_hours'].sum():,.0f}h",
        delta=None
    )

with col2:
    st.metric(
        "Média por Jogo",
        f"{filtered_df['playtime_hours'].mean():.1f}h",
        delta=None
    )

with col3:
    verified_count = len(filtered_df[filtered_df['steam_deck_status'] == 'Verified'])
    st.metric(
        "Steam Deck Verified",
        f"{verified_count}",
        delta=f"{verified_count/len(filtered_df)*100:.1f}%" if len(filtered_df) > 0 else "0%"
    )

with col4:
    mc_count = filtered_df['metacritic_score'].notna().sum()
    mc_avg = filtered_df['metacritic_score'].mean() if mc_count > 0 else 0
    st.metric(
        "Com Metacritic",
        f"{mc_count}",
        delta=f"Média: {mc_avg:.0f}" if mc_count > 0 else None
    )

with col5:
    hltb_count = filtered_df['hltb_all_styles'].gt(0).sum()
    hltb_avg = filtered_df[filtered_df['hltb_all_styles'] > 0]['hltb_all_styles'].mean() if hltb_count > 0 else 0
    st.metric(
        "Com HowLongToBeat",
        f"{hltb_count}",
        delta=f"Média: {hltb_avg:.0f}h" if hltb_count > 0 else None
    )

# ==================== GRÁFICOS ====================

st.markdown("---")

# Layout de colunas
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("📊 Top 15 Jogos Mais Jogados")
    
    top_games = filtered_df.nlargest(15, 'playtime_hours')
    
    fig_bar = px.bar(
        top_games,
        x='playtime_hours',
        y='name',
        orientation='h',
        color='steam_deck_status',
        color_discrete_map={
            'Verified': '#2ecc71',
            'Playable': '#f39c12',
            'Unknown': '#95a5a6',
            'Unsupported': '#e74c3c'
        },
        labels={'playtime_hours': 'Horas', 'name': '', 'steam_deck_status': 'Steam Deck'},
        hover_data=['protondb_tier', 'metacritic_score']
    )
    
    fig_bar.update_layout(
        yaxis={'categoryorder': 'total ascending'},
        height=500,
        showlegend=True
    )
    
    st.plotly_chart(fig_bar, width='stretch')

with chart_col2:
    st.subheader("🎯 Distribuição Steam Deck")
    
    deck_counts = filtered_df['steam_deck_status'].value_counts()
    
    fig_pie = px.pie(
        values=deck_counts.values,
        names=deck_counts.index,
        color=deck_counts.index,
        color_discrete_map={
            'Verified': '#2ecc71',
            'Playable': '#f39c12',
            'Unknown': '#95a5a6',
            'Unsupported': '#e74c3c'
        },
        hole=0.4
    )
    
    fig_pie.update_layout(height=500)
    
    st.plotly_chart(fig_pie, width='stretch')

# ==================== TERCEIRA ROW - METACRITIC ====================

st.markdown("---")
st.subheader("🎯 Análise Metacritic")

chart_col5, chart_col6 = st.columns(2)

with chart_col5:
    # Top jogos por score Metacritic
    mc_games = filtered_df[filtered_df['metacritic_score'].notna()].nlargest(15, 'metacritic_score')
    
    if not mc_games.empty:
        fig_mc = px.bar(
            mc_games,
            x='metacritic_score',
            y='name',
            orientation='h',
            color='steam_deck_status',
            color_discrete_map={
                'Verified': '#2ecc71',
                'Playable': '#f39c12',
                'Unknown': '#95a5a6',
                'Unsupported': '#e74c3c'
            },
            labels={'metacritic_score': 'Score Metacritic', 'name': ''},
            hover_data=['playtime_hours', 'protondb_tier']
        )
        
        fig_mc.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            height=500,
            showlegend=True
        )
        
        st.plotly_chart(fig_mc, width='stretch')
    else:
        st.info("Nenhum jogo com score Metacritic encontrado")

with chart_col6:
    # Distribuição de scores Metacritic
    if mc_count > 0:
        fig_dist = px.histogram(
            filtered_df[filtered_df['metacritic_score'].notna()],
            x='metacritic_score',
            nbins=20,
            color='steam_deck_status',
            color_discrete_map={
                'Verified': '#2ecc71',
                'Playable': '#f39c12',
                'Unknown': '#95a5a6',
                'Unsupported': '#e74c3c'
            },
            labels={'metacritic_score': 'Score Metacritic', 'count': 'Quantidade'}
        )
        
        fig_dist.update_layout(height=500)
        
        st.plotly_chart(fig_dist, width='stretch')
    else:
        st.info("Nenhum jogo com score Metacritic encontrado")

# ==================== SEGUNDA ROW ====================

chart_col3, chart_col4 = st.columns(2)

with chart_col3:
    st.subheader("📈 Horas vs ProtonDB Score")
    
    fig_scatter = px.scatter(
        filtered_df[filtered_df['protondb_score'] > 0],
        x='protondb_score',
        y='playtime_hours',
        color='steam_deck_status',
        size='protondb_score',
        hover_name='name',
        color_discrete_map={
            'Verified': '#2ecc71',
            'Playable': '#f39c12',
            'Unknown': '#95a5a6',
            'Unsupported': '#e74c3c'
        },
        labels={
            'protondb_score': 'ProtonDB Score',
            'playtime_hours': 'Horas Jogadas',
            'steam_deck_status': 'Steam Deck'
        }
    )
    
    fig_scatter.update_layout(height=500)
    
    st.plotly_chart(fig_scatter, width='stretch')

with chart_col4:
    st.subheader("🏆 Top ProtonDB Tiers")
    
    tier_counts = filtered_df['protondb_tier'].value_counts()
    
    tier_colors = {
        'platinum': '#e5e4e2',
        'gold': '#ffd700',
        'silver': '#c0c0c0',
        'bronze': '#cd7f32',
        'borked': '#e74c3c',
        'native': '#2ecc71',
        'pending': '#95a5a6',
        'unknown': '#bdc3c7'
    }
    
    fig_tiers = px.bar(
        x=tier_counts.index,
        y=tier_counts.values,
        color=tier_counts.index,
        color_discrete_map=tier_colors,
        labels={'x': 'Tier', 'y': 'Quantidade', 'color': 'Tier'}
    )
    
    fig_tiers.update_layout(height=500, showlegend=False)
    
    st.plotly_chart(fig_tiers, width='stretch')

# ==================== QUARTA ROW - HOW LONG TO BEAT ====================

st.markdown("---")
st.subheader("⏱ Análise HowLongToBeat")

chart_col7, chart_col8 = st.columns(2)

with chart_col7:
    # Scatter: Duração estimada vs horas jogadas
    hltb_data = filtered_df[filtered_df['hltb_all_styles'] > 0].copy()
    if not hltb_data.empty:
        # Calcular % de progresso
        hltb_data['progress_pct'] = (
            (hltb_data['playtime_hours'] / hltb_data['hltb_all_styles'] * 100)
            .clip(0, 200)
        )
        
        fig_hltb = px.scatter(
            hltb_data,
            x='hltb_all_styles',
            y='playtime_hours',
            color='steam_deck_status',
            size='hltb_all_styles',
            hover_name='name',
            color_discrete_map={
                'Verified': '#2ecc71',
                'Playable': '#f39c12',
                'Unknown': '#95a5a6',
                'Unsupported': '#e74c3c'
            },
            labels={
                'hltb_all_styles': 'Duração HLTB (All Styles)',
                'playtime_hours': 'Horas Jogadas',
                'steam_deck_status': 'Steam Deck'
            }
        )
        
        # Linha diagonal (y=x) - "completei exatamente"
        max_val = max(hltb_data['hltb_all_styles'].max(), hltb_data['playtime_hours'].max())
        fig_hltb.add_trace(go.Scatter(
            x=[0, max_val],
            y=[0, max_val],
            mode='lines',
            name='Limite de conclusão',
            line=dict(color='rgba(255,255,255,0.3)', dash='dash')
        ))
        
        fig_hltb.update_layout(height=500)
        st.plotly_chart(fig_hltb, width='stretch')
    else:
        st.info("Nenhum jogo com dados HLTB encontrado")

with chart_col8:
    # Distribuição por categoria de duração
    hltb_categories = filtered_df[filtered_df['hltb_all_styles'] > 0].copy()
    if not hltb_categories.empty:
        def duration_category(hours):
            if hours < 5:
                return "Muito Curta (<5h)"
            elif hours < 15:
                return "Curta (5-15h)"
            elif hours < 30:
                return "Média (15-30h)"
            elif hours < 60:
                return "Longa (30-60h)"
            else:
                return "Muito Longa (>60h)"
        
        hltb_categories['duration_cat'] = hltb_categories['hltb_all_styles'].apply(duration_category)
        cat_order = ["Muito Curta (<5h)", "Curta (5-15h)", "Média (15-30h)", "Longa (30-60h)", "Muito Longa (>60h)"]
        
        cat_counts = hltb_categories['duration_cat'].value_counts()
        cat_counts = cat_counts.reindex([c for c in cat_order if c in cat_counts.index])
        
        cat_colors = {
            "Muito Curta (<5h)": '#2ecc71',
            "Curta (5-15h)": '#3498db',
            "Média (15-30h)": '#f39c12',
            "Longa (30-60h)": '#e67e22',
            "Muito Longa (>60h)": '#e74c3c'
        }
        
        fig_cat = px.bar(
            x=cat_counts.index,
            y=cat_counts.values,
            color=cat_counts.index,
            color_discrete_map=cat_colors,
            labels={'x': 'Categoria', 'y': 'Quantidade', 'color': 'Duração'}
        )
        
        fig_cat.update_layout(height=500, showlegend=False)
        st.plotly_chart(fig_cat, width='stretch')
    else:
        st.info("Nenhum jogo com dados HLTB encontrado")

# ==================== TABELA DE DADOS ====================

st.markdown("---")
st.subheader("📋 Lista de Jogos")

# Ordenar por horas
sort_by = st.selectbox(
    "Ordenar por:",
    ["playtime_hours", "name", "protondb_score", "metacritic_score", "steam_deck_status"],
    index=0
)

ascending = st.checkbox("Ordem crescente", value=False)

display_df = filtered_df.sort_values(sort_by, ascending=ascending)

# Selecionar colunas para exibir
display_columns = st.multiselect(
    "Colunas para exibir:",
    ['name', 'playtime_hours', 'steam_deck_status', 'protondb_tier', 'protondb_score', 'metacritic_score', 'hltb_main_story', 'hltb_all_styles', 'is_backlog', 'categories'],
    default=['name', 'playtime_hours', 'steam_deck_status', 'protondb_tier', 'metacritic_score']
)

if display_columns:
    st.dataframe(
        display_df[display_columns].reset_index(drop=True),
        width='stretch',
        height=600
    )

# ==================== EXPORTAR ====================

st.markdown("---")
st.subheader("📥 Exportar Dados")

csv_export = display_df.to_csv(index=False)
st.download_button(
    label="Baixar CSV",
    data=csv_export,
    file_name="steam_games_filtered.csv",
    mime="text/csv"
)

# ==================== FOOTER ====================

st.markdown("---")
st.markdown(
    """
    **Steam Games Dashboard** | Dados extraídos via Steam API + ProtonDB API + HowLongToBeat | 
    [GitHub](https://github.com/seu-usuario/analise_steam)
    """
)
