import streamlit as st
import json
import plotly.graph_objects as go
import sqlite3
import pandas as pd
from pathlib import Path

if 'selected_team_number' not in st.session_state:
    st.session_state.selected_team_number = 1

team_number = st.sidebar.number_input(
    "Team Number",
    min_value=1,
    step=1,
    value=int(st.session_state.selected_team_number),
    key="team_number_input",
)

st.session_state.selected_team_number = int(team_number)

page_config_path = Path(__file__).with_suffix('.json')
with page_config_path.open('r', encoding='utf-8') as config_file:
    page_config = json.load(config_file)

conn = sqlite3.connect('ScoutingData.db')
cursor = conn.cursor()

data = cursor.execute('SELECT * FROM quant WHERE "Team Number" = ?', (team_number,))
quant_data = pd.DataFrame(data.fetchall(), columns=[desc[0] for desc in cursor.description])

graph_config = page_config.get('graph', {})
trace_config = graph_config.get('traces', [])

fig = go.Figure()

for trace in trace_config:
    data_series = trace.get('data_series')
    trace_type = trace.get('type', 'scatter')
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

if 'Total O Perf' in quant_data.columns and not quant_data.empty:
    y_axis_max = quant_data['Total O Perf'].max() * 1.2
else:
    y_axis_max = 14



fig.update_layout(
    title=f"Team {team_number} Performance Over Matches",
    xaxis_title="Match Number",
    yaxis_title="Points / Fuel Shot",
    yaxis_range=[-5, y_axis_max],
)

st.markdown(f"# Team {team_number}")

st.markdown("Data Over Matches")

st.plotly_chart(fig, use_container_width=True)

st.dataframe(quant_data)
