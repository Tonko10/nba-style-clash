import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

# 1. Workspace UI & Custom CSS
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
    div[data-testid="stMetric"]:hover { 
        transform: translateY(-3px); border-color: #006BB6; animation: pulsate 1.5s infinite; 
    }
    
    .tech-label { 
        color: #4CAF50; font-family: monospace; font-size: 12px; margin-bottom: 15px; 
        padding: 4px 8px; background: rgba(76, 175, 80, 0.1); border-radius: 4px; display: inline-block;
    }
    </style>
""", unsafe_allow_html=True)

# 2. Live Data Pipeline
TARGET_URL = "https://www.basketball-reference.com/boxscores/202405020PHI.html"

@st.cache_data(ttl=3600)
def fetch_bball_ref_data(url):
    # Full browser user-agent required to bypass 403 anti-bot blocks
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'}
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        return None
        
    tables = pd.read_html(response.text)
    
    for i in range(len(tables)):
        if isinstance(tables[i].columns, pd.MultiIndex):
            tables[i].columns = tables[i].columns.get_level_values(-1)
            
    basic_tables = [t for t in tables if 'Starters' in t.columns and 'PTS' in t.columns and 'USG%' not in t.columns]
    adv_tables = [t for t in tables if 'Starters' in t.columns and 'USG%' in t.columns and 'TS%' in t.columns]
    
    if len(basic_tables) < 2 or len(adv_tables) < 2:
        return None
        
    away_merged = pd.merge(basic_tables[0][['Starters', 'PTS', 'AST', 'TRB', 'TOV']], adv_tables[0][['Starters', 'USG%', 'TS%']], on='Starters')
    away_merged['Team'] = 'Away Team'
    
    home_merged = pd.merge(basic_tables[-1][['Starters', 'PTS', 'AST', 'TRB', 'TOV']], adv_tables[-1][['Starters', 'USG%', 'TS%']], on='Starters')
    home_merged['Team'] = 'Home Team'
    
    all_players = pd.concat([away_merged, home_merged])
    all_players = all_players[all_players['Starters'] != 'Reserves'].dropna(subset=['PTS'])
    all_players = all_players.rename(columns={'Starters': 'PLAYER_NAME', 'TRB': 'REB', 'TOV': 'TO', 'USG%': 'USG_PCT', 'TS%': 'TS_PCT'})
    
    numeric_cols = ['PTS', 'AST', 'REB', 'TO', 'USG_PCT', 'TS_PCT']
    all_players[numeric_cols] = all_players[numeric_cols].apply(pd.to_numeric, errors='coerce')
    
    return all_players

with st.spinner("Executing Pandas HTML Scraper..."):
    player_stats = fetch_bball_ref_data(TARGET_URL)

# 3. Application Frontend
st.title("🏀 NBA Analytics Workspace")
st.markdown("<div class='tech-label'>► ARCHITECTURE: Python | Streamlit | Pandas Web Scraping | Glassmorphism CSS</div>", unsafe_allow_html=True)

if player_stats is None:
    st.error("Scraper failed. Verify the target URL.")
    st.stop()

tab1, tab2, tab3 = st.tabs(["📈 Momentum Flow", "🎯 Efficiency Engine", "👑 Impact Metrics"])

with tab1:
    st.markdown("<div class='tech-label'>► VISUALIZATION: Plotly Graph Objects (go.Scatter) with Bi-directional Splitting</div>", unsafe_allow_html=True)
    st.subheader("Dynamic Lead Tracker")
    
    minutes = np.linspace(0, 48, 25)
    lead_margin = [0, 8, 4, 7, -2, 3, 0, -3, -10, -5, -8, -4, -4, -5, -7, 1, -4, -2, 7, 9, 4, 9, 3, 7, 6]
    
    pos_lead = [max(0, m) for m in lead_margin]
    neg_lead = [min(0, m) for m in lead_margin]
    
    fig_flow = go.Figure()
    fig_flow.add_trace(go.Scatter(x=minutes, y=pos_lead, fill='tozeroy', mode='lines', line=dict(color='#66BB6A', width=2), fillcolor='rgba(102, 187, 106, 0.7)', name='Away Lead'))
    fig_flow.add_trace(go.Scatter(x=minutes, y=neg_lead, fill='tozeroy', mode='lines', line=dict(color='#5C6BC0', width=2), fillcolor='rgba(92, 107, 192, 0.7)', name='Home Lead'))
    
    fig_flow.add_hline(y=0, line_width=1, line_color="rgba(255, 255, 255, 0.3)")
    fig_flow.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(title="Game Minute"), yaxis=dict(title="Lead Margin"), hovermode="x unified", showlegend=False, height=400)
    st.plotly_chart(fig_flow, use_container_width=True)

with tab2:
    st.markdown("<div class='tech-label'>► DATA PIPELINE: Live Pandas Scraper → Dataframe Cleansing → Plotly Express Mapping</div>", unsafe_allow_html=True)
    st.subheader("Volume vs. Efficiency Matrix")
    
    col_filter, col_scatter = st.columns([1, 3])
    with col_filter:
        st.write("#### Parameters")
        min_pts = st.slider("Minimum Points Scored", 0, 40, 10)
        
    with col_scatter:
        filtered_df = player_stats[player_stats['PTS'] >= min_pts].copy()
        filtered_df['TS_PCT'] *= 100
            
        fig_scatter = px.scatter(filtered_df, x="USG_PCT", y="TS_PCT", size="PTS", color="Team", text="PLAYER_NAME")
        fig_scatter.add_vline(x=20, line_dash="dash", line_color="gray", annotation_text="Avg Usage")
        fig_scatter.add_hline(y=57.5, line_dash="dash", line_color="gray", annotation_text="Avg TS%")
        
        fig_scatter.update_traces(textposition='top center')
        fig_scatter.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis_title="Usage Rate (USG%)", yaxis_title="True Shooting (TS%)", height=450)
        st.plotly_chart(fig_scatter, use_container_width=True)

with tab3:
    st.markdown("<div class='tech-label'>► UI COMPONENT: Streamlit Metric Columns with CSS Keyframe Animations</div>", unsafe_allow_html=True)
    st.subheader("King James Impact Overview")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("AST/TO Ratio", "7.0", "Elite distribution")
    m2.metric("Total Rebounds", "9", "Board control")
    m3.metric("True Shooting", "44.8%", "Volume inefficiency")
    m4.metric("Plus/Minus (+/-)", "-2", "Net rating impact")
    
    st.divider()
    
    col_text, col_chart = st.columns([1, 1], gap="large")
    with col_text:
        st.markdown("""
        ### Playmaking & Ball Security
        Operating as a half-court facilitator, LeBron anchored the offense through elite ball security rather than high-volume scoring.
        *   **Distribution:** A phenomenal 7-to-1 assist-to-turnover ratio stabilized the offense.
        *   **Board Control:** 9 total rebounds limited second-chance points.
        """)
        
    with col_chart:
        playmaking_data = pd.DataFrame({'Stat': ['Assists', 'Turnovers', 'Steals', 'Blocks'], 'Value': [7, 1, 1, 1]})
        fig_bar = px.bar(playmaking_data, x='Value', y='Stat', text='Value', orientation='h', color='Stat', color_discrete_sequence=['#FDB927', '#E0E0E0', '#552583', '#006BB6'])
        fig_bar.update_traces(textposition='inside', textfont=dict(size=14, color='black'))
        fig_bar.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False), yaxis=dict(title=""), showlegend=False, height=250, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig_bar, use_container_width=True)
