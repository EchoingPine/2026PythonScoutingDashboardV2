import streamlit as st
import pandas as pd
import sqlite3
import json
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

st.title("Averages")

page_config_path = Path(__file__).with_suffix('.json')
with page_config_path.open('r', encoding='utf-8') as config_file:
    page_config = json.load(config_file)

conn = sqlite3.connect('ScoutingData.db')
cursor = conn.cursor()

columns_config = page_config.get("columns", {})
auto_columns = columns_config.get("auto_columns", [])
teleop_columns = columns_config.get("teleop_columns", [])
total_columns = columns_config.get("total_columns", [])


data = cursor.execute('SELECT * FROM quant')
quant_data = pd.DataFrame(data.fetchall(), columns=[desc[0] for desc in cursor.description])

averages_df = quant_data.groupby('Team Number').mean(numeric_only=True).reset_index()

averages_df.drop(columns='Match Number', errors='ignore', inplace=True)
averages_df.drop(columns='Team Match Number', errors='ignore', inplace=True)

ordered_columns = ['Team Number']
for column_group in (auto_columns, teleop_columns, total_columns):
    for column in column_group:
        if column in averages_df.columns and column not in ordered_columns:
            ordered_columns.append(column)

for column in averages_df.columns:
    if column not in ordered_columns:
        ordered_columns.append(column)

averages_df = averages_df[ordered_columns]

to_sql = averages_df.copy()

metric_columns = [column for column in averages_df.columns if column != 'Team Number']

styled_averages = (averages_df.style
                   .format("{:.2f}", subset=metric_columns)
                   .background_gradient(subset=auto_columns, cmap='Blues')
                   .background_gradient(subset=teleop_columns, cmap='Oranges')
                   .background_gradient(subset=total_columns, cmap='Greens')
                   )

st.dataframe(styled_averages, use_container_width=True)

to_sql.to_sql('averages', conn, if_exists='replace', index=False)