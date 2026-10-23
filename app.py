import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="NBA Style Clash", layout="wide", page_icon="🏀")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Google Sans', sans-serif;
        scroll-behavior: smooth;
    }
    
    .stApp {
        animation: fadeIn 0.8s cubic-bezier(0.16, 1, 0.3, 1);
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: rgba(255, 255, 255, 0.05);
        padding: 5px;
        border-radius: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        border-radius: 8px;
        font-size: 16px;
        font-weight: 500;
        border: none !important;
        padding: 0 20px;
        transition: all 0.3s ease;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(255, 255, 255, 0.15) !important;
        color: white !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.03);
        padding: 20px;
        border-radius: 12px;
        border-left: 4px solid #FDB927;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(253, 185, 39, 0.2);
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏀 NBA Style Clash: 76ers vs. Knicks")
st.markdown("**Opening Night Deep Dive (Oct 20, 2026) | Final Score: PHI 106 - 100 NYK**")
st.divider()

tab1, tab2, tab3 = st.tabs(["📊 Team Dynamics", "⛹️‍♂️ Key Performers", "👑 King James Impact"])

with tab1:
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.subheader("Playstyle Radar")
        categories = ['Perimeter Scoring', 'Paint Dominance', 'Playmaking (Ast)', 'Ball Security (Low TO)', 'Rebounding']
        sixers_data = [85, 45, 75, 80, 45] 
        knicks_data = [65, 85, 60, 65, 95] 

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=sixers_data + [sixers_data[0]], theta=categories + [categories[0]],
            fill='toself', name='Philadelphia 76ers',
            line_color='#006BB6', fillcolor='rgba(0, 107, 182, 0.4)'
        ))
        fig_radar.add_trace(go.Scatterpolar(
            r=knicks_data + [knicks_data[0]], theta=categories + [categories[0]],
            fill='toself', name='New York Knicks',
            line_color='#F58426', fillcolor='rgba(245, 132, 38, 0.4)'
        ))
        fig_radar.update_layout(
            template='plotly_dark',
            font=dict(color='white'),
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100], gridcolor='rgba(255,255,255,0.2)'),
                angularaxis=dict(gridcolor='rgba(255,255,255,0.2)')
            ),
            showlegend=True, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=40, r=40, t=40, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    with col2:
        st.subheader("Momentum Timeline")
        timeline_data = pd.DataFrame({
            'Quarter': ['Q1', 'Q2', 'Q3', 'Q4'],
            '76ers': [28, 54, 82, 106],
            'Knicks': [31, 52, 78, 100]
        })
        
        fig_line = px.line(timeline_data, x='Quarter', y=['76ers', 'Knicks'], 
                           color_discrete_map={'76ers': '#006BB6', 'Knicks': '#F58426'})
        
        fig_line.update_traces(line_shape='spline', line=dict(width=4), mode='lines+markers', marker=dict(size=8))
        fig_line.update_layout(
            template='plotly_dark',
            font=dict(color='white'),
            hovermode="x unified",
            yaxis_title="Total Points", xaxis_title="",
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
            legend=dict(title=None, orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_line, use_container_width=True)

with tab2:
    st.subheader("Box Score Highlights")
    
    player_data = pd.DataFrame({
        'Player': ['Tyrese Maxey', 'LeBron James', 'Jalen Brunson', 'Karl-Anthony Towns', 'Andre Drummond'],
        'Team': ['76ers', '76ers', 'Knicks', 'Knicks', 'Knicks'],
        'PTS': [28, 14, 25, 22, 12],
        'REB': [4, 9, 3, 14, 16],
        'AST': [6, 7, 8, 2, 1],
        'MIN': [36, 31, 38, 34, 28]
    })
    
    st.dataframe(
        player_data,
        column_config={
            "PTS": st.column_config.ProgressColumn(
                "Points", help="Total points scored", format="%d", min_value=0, max_value=30
            ),
            "REB": st.column_config.NumberColumn("Rebounds", format="%d"),
            "AST": st.column_config.NumberColumn("Assists", format="%d"),
        },
        use_container_width=True,
        hide_index=True
    )
    
    st.info("💡 **Analytics Takeaway:** While Towns and Drummond absolutely crushed the glass (30 combined rebounds), Maxey's perimeter efficiency and ball security neutralized the rebounding deficit.")

with tab3:
    st.subheader("👑 Year 24: High-IQ Basketball")
    st.write("The box score doesn't tell the whole story. LeBron no longer needs 30 points to control the tempo of a close game.")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Clutch Assists (Q4)", "4", "+2 vs rest of team")
    col2.metric("Defensive Rebounds", "8", "Neutralized Knicks 2nd chances")
    col3.metric("Plus/Minus (+/-)", "+12", "Team-high impact")
    
    st.divider()
    
    col_text, col_chart = st.columns([1, 1], gap="large")
    with col_text:
        st.markdown("""
        ### Why this matters:
        When New York trapped Tyrese Maxey in the 4th quarter, the 76ers used LeBron as the primary hub at the high-post. 
        
        *   **9 Total Rebounds:** Crucial for stopping the Knicks' heavy offensive rebounding in the final 5 minutes.
        *   **7 Assists:** 4 of these came in clutch situations (score within 3 points).
        *   **Leadership:** Veteran poise that completely slowed the game down when the momentum was shifting to New York.
        """)
    
    with col_chart:
        lbj_stats = pd.DataFrame({
            'Stat': ['Points', 'Rebounds', 'Assists'],
            'Value': [14, 9, 7]
        })
        fig_bar = px.bar(lbj_stats, x='Value', y='Stat', text='Value', orientation='h',
                         color='Stat', color_discrete_sequence=['#FDB927', '#552583', '#E0E0E0'])
        fig_bar.update_traces(textposition='inside', textfont=dict(size=16, color='black'))
        fig_bar.update_layout(
            template='plotly_dark',
            font=dict(color='white'),
            showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, visible=False), yaxis=dict(title="")
        )
        st.plotly_chart(fig_bar, use_container_width=True)
