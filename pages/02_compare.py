import streamlit as st
import pandas as pd
import sqlite3
import json
from pathlib import Path
import plotly.graph_objects as go

page_config_path = Path(__file__).with_suffix('.json')
with page_config_path.open('r', encoding='utf-8') as config_file:
    page_config = json.load(config_file)

conn = sqlite3.connect('ScoutingData.db')
cursor = conn.cursor()

team_shown_value = page_config.get('team_shown_value')
team_total_calculation = page_config.get('team_total_calculation', {})

graph_config = page_config.get('graph', {})
trace_config = graph_config.get('traces', [])

if 'team_numbers' not in st.session_state:
    st.session_state.team_numbers = [1, 1, 1]
    st.session_state.team_numbers_red = [1, 1, 1]
    st.session_state.team_numbers_blue = [1, 1, 1]

if 'show_legend' not in st.session_state:
    st.session_state.show_legend = True

num_inputs = len(st.session_state.team_numbers)

st.sidebar.header("Red")

for i in range(1, num_inputs + 1):
    val = st.sidebar.number_input(
        f"Team Number {i}",
        min_value=1,
        step=1,
        value=int(st.session_state.team_numbers_red[i - 1]),
        key=f"team_number_input_red_{i}",
    )
    # keep the persistent list in sync with the widget value
    st.session_state.team_numbers_red[i - 1] = int(val)

st.sidebar.header("Blue")

for i in range(1, num_inputs + 1):
    val = st.sidebar.number_input(
        f"Team Number {i}",
        min_value=1,
        step=1,
        value=int(st.session_state.team_numbers_blue[i - 1]),
        key=f"team_number_input_blue_{i}",
    )
    # keep the persistent list in sync with the widget value
    st.session_state.team_numbers_blue[i - 1] = int(val)

st.sidebar.header("Graph Options")
show_legend = st.sidebar.checkbox("Show Legend", value=st.session_state.show_legend)

st.header(":red[Red Alliance]")

red_total = 0.0

cols = st.columns(3)
for i, team_number in enumerate(st.session_state.team_numbers_red):
    with cols[i]:
        st.subheader(f":red[Team {team_number}]")
        try:
            data = cursor.execute(f'SELECT "{team_shown_value}" FROM averages WHERE "Team Number" = ?', (team_number,))
            df = pd.DataFrame(data.fetchall(), columns=[desc[0] for desc in cursor.description])
            if df.empty:
                st.write(":red[No data]")
            else:
                styled_df = df.style.format("{:.2f}", subset=[team_shown_value]).map(
                    lambda value: 'background-color: #ff3434; color: white' if pd.notna(value) and float(value) > 0 else '',
                    subset=[team_shown_value],
                )
                st.dataframe(styled_df, use_container_width=True)
        except Exception as e:
            st.write(f"Error loading data: {e}")
        # capture team total for predicted alliance score
        try:
            team_total = 0.0
            if not df.empty and team_shown_value in df.columns:
                team_value = pd.to_numeric(df[team_shown_value].iat[0], errors='coerce')
                team_total = float(team_value) if pd.notna(team_value) else 0.0
        except Exception:
            team_total = 0.0
        red_total += team_total
        
st.subheader(f":red[Predicted Red Score]")
st.metric(label='', value=f":red[{red_total:.1f}]")

st.markdown('---')
st.header(":blue[Blue Alliance]")

blue_total = 0.0

cols = st.columns(3)
for i, team_number in enumerate(st.session_state.team_numbers_blue):
    with cols[i]:
        st.subheader(f":blue[Team {team_number}]")
        try:
            data = cursor.execute(f'SELECT "{team_shown_value}" FROM averages WHERE "Team Number" = ?', (team_number,))
            df = pd.DataFrame(data.fetchall(), columns=[desc[0] for desc in cursor.description])
            if df.empty:
                st.write(":blue[No data]")
            else:
                styled_df = df.style.format("{:.2f}", subset=[team_shown_value]).map(
                    lambda value: 'background-color: #346aff; color: white' if pd.notna(value) and float(value) > 0 else '',
                    subset=[team_shown_value],
                )
                st.dataframe(styled_df, use_container_width=True)
        except Exception as e:
            st.write(f"Error loading data: {e}")
        # capture team total for predicted alliance score
        try:
            team_total = 0.0
            if not df.empty and team_shown_value in df.columns:
                team_value = pd.to_numeric(df[team_shown_value].iat[0], errors='coerce')
                team_total = float(team_value) if pd.notna(team_value) else 0.0
        except Exception:
            team_total = 0.0
        blue_total += team_total

st.subheader(f":blue[Predicted Blue Score]")
st.metric(label='', value=f":blue[{blue_total:.1f}]")


graph_team_numbers = st.session_state.team_numbers_red + st.session_state.team_numbers_blue

# Render graphs in rows of three columns
for batch_start in range(0, len(graph_team_numbers), 3):
    cols = st.columns(3)
    for col_idx in range(3):
        idx = batch_start + col_idx
        if idx >= len(graph_team_numbers):
            break
        graph_team_number = graph_team_numbers[idx]

        data = cursor.execute('SELECT * FROM quant WHERE "Team Number" = ?', (graph_team_number,))
        quant_data = pd.DataFrame(data.fetchall(), columns=[desc[0] for desc in cursor.description])

        fig = go.Figure()

        for trace in trace_config:
            data_series = trace.get('data_series')
            mode = trace.get('mode', 'lines+markers')

            if data_series not in quant_data.columns:
                continue

            fig.add_trace(
                go.Scatter(
                    x=quant_data['Team Match Number'] if 'Team Match Number' in quant_data.columns else list(range(1, len(quant_data) + 1)),
                    y=quant_data[data_series],
                    mode=mode,
                    line=dict(shape='spline'),
                    name=data_series,
                )
            )

        if 'Total Fuel Shot' in quant_data.columns and not quant_data.empty:
            y_axis_max = quant_data['Total Fuel Shot'].max() * 1.2
        else:
            y_axis_max = 1

        fig.update_layout(
            title=f"Team {graph_team_number} Performance Over Matches",
            xaxis_title="Match Number",
            yaxis_title="Points / Fuel Shot",
            yaxis_range=[-5, y_axis_max],
            showlegend=show_legend,
        )

        try:
            with cols[col_idx]:
                st.plotly_chart(fig, use_container_width=True)
        except st.errors.StreamlitDuplicateElementId:
            continue