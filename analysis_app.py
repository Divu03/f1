import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- Configuration ---
st.set_page_config(page_title="F1 Performance Analysis (2018-2024)", layout="wide")

# --- 1. Load Data ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('f1_race_data_2018_2024.csv')
        df['Position'] = pd.to_numeric(df['Position'], errors='coerce')
        df['GridPosition'] = pd.to_numeric(df['GridPosition'], errors='coerce')
        df['Points'] = pd.to_numeric(df['Points'], errors='coerce')
        df['Win'] = df['Position'].apply(lambda x: 1 if x == 1 else 0)
        df['DNF'] = df['Position'].isna().astype(int)
        return df
    except FileNotFoundError:
        return None

df = load_data()

# --- 2. Header ---
st.title("🏎️ F1 Performance Analysis (2018-2024)")
st.markdown("""
This dashboard analyzes the key factors that determine race outcomes in Formula 1. 
We explore the impact of **Qualifying Performance**, **Team Strength**, and **Weather Conditions**.
""")

if df is None:
    st.error("Data file `f1_race_data_2018_2024.csv` not found. Please run your data collection script first!")
    st.stop()

# --- 3. Sidebar Filters ---
st.sidebar.header("Filters")
selected_years = st.sidebar.multiselect(
    "Select Seasons",
    options=sorted(df['Year'].unique()),
    default=sorted(df['Year'].unique())
)

filtered_df = df[df['Year'].isin(selected_years)]

# --- 4. Analysis Tabs ---
tab1, tab2, tab3 = st.tabs(["🏁 Qualifying Impact", "🏆 Team Dominance", "🌧️ Weather Chaos"])

with tab1:
    st.header("How important is Qualifying?")
    col1, col2 = st.columns(2)
    with col1:
        winners = filtered_df[filtered_df['Position'] == 1]
        win_grid_counts = winners['GridPosition'].value_counts().reset_index()
        win_grid_counts.columns = ['Grid Position', 'Wins']
        fig_pie = px.pie(win_grid_counts, values='Wins', names='Grid Position', title="Starting Position of Race Winners")
        st.plotly_chart(fig_pie, use_container_width=True)
    with col2:
        finishers = filtered_df.dropna(subset=['Position', 'GridPosition'])
        fig_scatter = px.density_heatmap(
            finishers, x="GridPosition", y="Position", 
            nbinsx=20, nbinsy=20, color_continuous_scale="Viridis",
            title="Heatmap: Start Position vs. Finish Position"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

with tab2:
    st.header("Constructor Points Analysis")
    team_points = filtered_df.groupby(['Year', 'TeamName'])['Points'].sum().reset_index()
    fig_teams = px.bar(team_points, x="Year", y="Points", color="TeamName", title="Points by Team", barmode='group')
    st.plotly_chart(fig_teams, use_container_width=True)

with tab3:
    st.header("The Rain Factor")
    wet_races = filtered_df[filtered_df['Rainfall'] == True]
    dry_races = filtered_df[filtered_df['Rainfall'] == False]
    dnf_wet = wet_races['DNF'].mean() * 100
    dnf_dry = dry_races['DNF'].mean() * 100
    dnf_data = pd.DataFrame({'Condition': ['Dry', 'Wet'], 'DNF Rate (%)': [dnf_dry, dnf_wet]})
    fig_dnf = px.bar(dnf_data, x='Condition', y='DNF Rate (%)', color='Condition')
    st.plotly_chart(fig_dnf, use_container_width=True)