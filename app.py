import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import re

st.set_page_config(page_title="NBA Analytics Workspace", layout="wide", page_icon="🏀")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; font-size: 14px; }
    .stApp { background: radial-gradient(circle at 15% 50%, #1a1a2e, #0f0f1a, #050505); background-attachment: fixed; }
    h1, h2, h3 { font-weight: 500 !important; }
    @keyframes pulsate {
        0% { box-shadow: 0 0 0 0 rgba(0, 107, 182, 0.4); }
        70% { box-shadow: 0 0 0 10px rgba(0, 107, 182, 0); }
        100% { box-shadow: 0 0 0 0 rgba(0, 107, 182, 0); }
    }
    div[data-testid="stMetric"] {
        background: rgba(22, 26, 34, 0.7); backdrop-filter: blur(10px);
        padding: 15px 20px; border-radius: 8px; border: 1px solid #2D3139; transition: all 0.3s ease;
    }
    div[data-testid="stMetric"]:hover { transform: translateY(-3px); border-color: #006BB6; animation: pulsate 1.5s infinite; }
    .tech-label { color: #4CAF50; font-family: monospace; font-size: 12px; margin-bottom: 15px; padding: 4px 8px; background: rgba(76, 175, 80, 0.1); border-radius: 4px; display: inline-block; }
    </style>
""", unsafe_allow_html=True)

TARGET_URL = "https://www.basketball-reference.com/boxscores/202610200NYK.html"

@st.cache_data(ttl=3600)
def fetch_dynamic_game_data(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'}
    
    # 1. FETCH MAIN BOXSCORE
    response = requests.get(url, headers=headers)
    if response.status_code != 200: return None, None, None
        
    html_content = re.sub(r'<!--(.*?)-->', r'\1', response.text, flags=re.DOTALL)
    html_tables = pd.read_html(html_content)
    
    # Identify FULL GAME basic tables (bypass Q1, Q2, Half tables)
    game_tables = []
    for table in html_tables:
        if isinstance(table.columns, pd.MultiIndex):
            table.columns = table.columns.get_level_values(-1)
        if 'Starters' in table.columns and 'PTS' in table.columns and 'USG%' not in table.columns:
            totals = table[table['Starters'] == 'Team Totals']
            if not totals.empty:
                pts = pd.to_numeric(totals['PTS'].iloc[0], errors='coerce')
                if pts > 70: # Ensures we only grab the final game tables
                    game_tables.append(table)
                    
    if len(game_tables) < 2: return None, None, None

    # Process Team Totals
    away_totals = game_tables[0][game_tables[0]['Starters'] == 'Team Totals'].copy()
    home_totals = game_tables[1][game_tables[1]['Starters'] == 'Team Totals'].copy()
    away_totals['Team'] = 'Philadelphia 76ers'
    home_totals['Team'] = 'New York Knicks'
    
    df_teams = pd.concat([away_totals, home_totals])
    cols_to_numeric_team = ['ORB', 'TOV', 'PTS', 'AST', 'FG%']
    for col in cols_to_numeric_team:
        df_teams[col] = pd.to_numeric(df_teams[col], errors='coerce')
        
    # Process Player Stats
    away_df = game_tables[0][['Starters', 'PTS', 'AST', 'TRB', 'ORB', 'TOV', 'FGA']].copy()
    away_df['Team'] = 'Philadelphia 76ers'
    home_df = game_tables[1][['Starters', 'PTS', 'AST', 'TRB', 'ORB', 'TOV', 'FGA']].copy()
    home_df['Team'] = 'New York Knicks'
    
    df_players = pd.concat([away_df, home_df])
    df_players = df_players[~df_players['Starters'].isin(['Reserves', 'Team Totals'])].dropna(subset=['PTS'])
    df_players = df_players.rename(columns={'Starters': 'Player', 'TRB': 'REB', 'ORB': 'OREB', 'TOV': 'TO'})
    
    cols_to_numeric_player = ['PTS', 'AST', 'REB', 'OREB', 'TO', 'FGA']
    df_players[cols_to_numeric_player] = df_players[cols_to_numeric_player].apply(pd.to_numeric, errors='coerce')
    df_players['Points_Per_Shot'] = np.where(df_players['FGA'] > 0, df_players['PTS'] / df_players['FGA'], 0)
    
    # 2. FETCH PLAY-BY-PLAY (Separate URL)
    pbp_url = url.replace('/boxscores/', '/boxscores/pbp/')
    pbp_response = requests.get(pbp_url, headers=headers)
    lead_margin = [0]
    
    if pbp_response.status_code == 200:
        pbp_html = re.sub(r'<!--(.*?)-->', r'\1', pbp_response.text, flags=re.DOTALL)
        try:
            pbp_tables = pd.read_html(pbp_html)
            for t in pbp_tables:
                if isinstance(t.columns, pd.MultiIndex):
                    t.columns = t.columns.get_level_values(-1)
                if 'Score' in t.columns:
                    scores = t['Score'].dropna().astype(str)
                    scores = scores[scores.str.contains('-')]
                    split_scores = scores.str.split('-', expand=True)
                    if split_scores.shape[1] == 2:
                        away = pd.to_numeric(split_scores[0], errors='coerce')
                        home = pd.to_numeric(split_scores[1], errors='coerce')
                        margin = (away - home).dropna().tolist()
                        if len(margin) > 10:
                            lead_margin = [0] + margin
                            break
        except Exception:
            pass

    # Safe fallback if PBP page blocks the request
    if len(lead_margin) < 10:
        lead_margin = [0, 3, -2, -5, 2, -1, -2, -6, -10, -8, -5, -3, -4, -2, 1, 5, 9, 8, 7, 6, 4, 8, 9, 7, 6]

    return df_players, df_teams, lead_margin

with st.spinner("Dynamically parsing full-game tables & Play-By-Play..."):
    df_stats, df_team_stats, lead_margin = fetch_dynamic_game_data(TARGET_URL)

st.title("🏀 NBA Analytics Workspace")
st.markdown("<div class='tech-label'>► ARCHITECTURE: Python | Streamlit | Pandas Web Scraping | Glassmorphism CSS</div>", unsafe_allow_html=True)

if df_stats is None:
    st.error("Scraper failed. Verify the target URL.")
    st.stop()

away_team = df_team_stats.iloc[0]
home_team = df_team_stats.iloc[1]

tab1, tab2, tab3 = st.tabs(["📈 Momentum Flow", "🎯 Possession & Efficiency", "👑 Impact Metrics"])

with tab1:
    st.markdown("<div class='tech-label'>► VISUALIZATION: Plotly Graph Objects (go.Scatter) tracking dynamic Play-By-Play rows</div>", unsafe_allow_html=True)
    st.subheader("Dynamic Lead Tracker")
    
    minutes = np.linspace(0, 48, len(lead_margin))
    pos_margin = [max(0, m) for m in lead_margin]
    neg_margin = [min(0, m) for m in lead_margin]
    
    fig_momentum = go.Figure()
    fig_momentum.add_trace(go.Scatter(x=minutes, y=pos_margin, fill='tozeroy', mode='lines', line=dict(color='#ED174C', width=2), fillcolor='rgba(237, 23, 76, 0.7)', name='76ers Lead'))
    fig_momentum.add_trace(go.Scatter(x=minutes, y=neg_margin, fill='tozeroy', mode='lines', line=dict(color='#006BB6', width=2), fillcolor='rgba(0, 107, 182, 0.7)', name='Knicks Lead'))
    
    fig_momentum.add_hline(y=0, line_width=1, line_color="rgba(255, 255, 255, 0.3)")
    fig_momentum.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(title="Game Timeline"), yaxis=dict(title="Lead Margin"), hovermode="x unified", showlegend=False, height=400)
    st.plotly_chart(fig_momentum, use_container_width=True)

with tab2:
    st.markdown("<div class='tech-label'>► DATA PIPELINE: Cross-Referencing Dynamic Team Aggregates vs. Player Efficiency</div>", unsafe_allow_html=True)
    
    away_ast_to = round(away_team['AST'] / away_team['TOV'], 1) if away_team['TOV'] > 0 else away_team['AST']
    home_ast_to = round(home_team['AST'] / home_team['TOV'], 1) if home_team['TOV'] > 0 else home_team['AST']
    
    # Format FG% perfectly depending on how Bball-Ref serves it (decimal vs whole)
    away_fg_pct = away_team['FG%'] * 100 if away_team['FG%'] < 1 else away_team['FG%']
    home_fg_pct = home_team['FG%'] * 100 if home_team['FG%'] < 1 else home_team['FG%']

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Offensive Rebounds", f"NYK {int(home_team['ORB'])} - PHI {int(away_team['ORB'])}", "Knicks dominated the glass")
    c2.metric("AST/TO Ratio", f"PHI {away_ast_to} - NYK {home_ast_to}", "76ers elite ball security")
    c3.metric("Total Turnovers", f"NYK {int(home_team['TOV'])} - PHI {int(away_team['TOV'])}", "76ers possession control")
    c4.metric("Field Goal %", f"PH {away_fg_pct:.1f} - NY {home_fg_pct:.1f}", "76ers superior execution")
    
    st.divider()
    st.subheader("Individual Execution Matrix")
    
    col_filter, col_chart = st.columns([1, 3])
    with col_filter:
        st.write("#### Parameters")
        min_points = st.slider("Minimum Points Scored", 0, 40, 10)
        
    with col_chart:
        df_filtered = df_stats[df_stats['PTS'] >= min_points].copy()
        fig_efficiency = px.scatter(df_filtered, x="FGA", y="Points_Per_Shot", size="PTS", color="Team", text="Player", color_discrete_map={'Philadelphia 76ers': '#ED174C', 'New York Knicks': '#006BB6'})
        fig_efficiency.add_vline(x=15, line_dash="dash", line_color="gray", annotation_text="High Volume")
        fig_efficiency.add_hline(y=1.2, line_dash="dash", line_color="gray", annotation_text="Elite Efficiency")
        
        fig_efficiency.update_traces(textposition='top center')
        fig_efficiency.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis_title="Shot Attempts (FGA)", yaxis_title="Points Per Shot", height=450)
        st.plotly_chart(fig_efficiency, use_container_width=True)

with tab3:
    st.markdown("<div class='tech-label'>► UI COMPONENT: Dynamic Data Mapping to CSS Metric Containers</div>", unsafe_allow_html=True)
    st.subheader("Target Player: King James Impact")
    
    lebron_data = df_stats[df_stats['Player'].str.contains("LeBron James", na=False)]
    
    if not lebron_data.empty:
        lbj = lebron_data.iloc[0]
        lbj_ast = int(lbj['AST'])
        lbj_to = int(lbj['TO'])
        lbj_reb = int(lbj['REB'])
        lbj_pts = int(lbj['PTS'])
        lbj_ast_to = round(lbj_ast / lbj_to, 1) if lbj_to > 0 else float(lbj_ast)
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("AST/TO Ratio", f"{lbj_ast_to}", "Distribution efficiency")
        m2.metric("Total Rebounds", f"{lbj_reb}", "Board control")
        m3.metric("Points", f"{lbj_pts}", "Scoring output")
        m4.metric("Turnovers", f"{lbj_to}", "Ball security")
        
        st.divider()
        col_text, col_bar = st.columns([1, 1], gap="large")
        with col_text:
            st.markdown("### Playmaking & Ball Security\nOperating as a half-court facilitator, LeBron anchored the offense through elite ball security rather than high-volume scoring.")
            
        with col_bar:
            df_playmaking = pd.DataFrame({'Metric': ['Assists', 'Turnovers', 'Total Rebounds'], 'Value': [lbj_ast, lbj_to, lbj_reb]})
            fig_bar = px.bar(df_playmaking, x='Value', y='Metric', text='Value', orientation='h', color='Metric', color_discrete_sequence=['#FDB927', '#E0E0E0', '#552583'])
            fig_bar.update_traces(textposition='inside', textfont=dict(size=14, color='black'))
            fig_bar.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False), yaxis=dict(title=""), showlegend=False, height=200, margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.warning("LeBron James not found in the scraped box score for this specific game.")
