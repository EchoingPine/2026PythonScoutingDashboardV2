import json
import pandas as pd
import numpy as np
import sqlite3
import re

from app_utils import get_active_competition, get_gspread_client, load_competition_config


def worksheet_to_dataframe(worksheet):
    values = worksheet.get_all_values()
    if not values:
        return pd.DataFrame()

    raw_headers = values[0]
    headers = []
    seen = {}

    for index, raw_header in enumerate(raw_headers):
        header = str(raw_header).strip() if raw_header is not None else ""
        if not header:
            header = f"Unnamed: {index + 1}"

        if header in seen:
            seen[header] += 1
            header = f"{header}.{seen[header]}"
        else:
            seen[header] = 0

        headers.append(header)

    return pd.DataFrame(values[1:], columns=headers)

def calculate_metrics():
    config = load_competition_config()
    active_competition = get_active_competition()
    if not active_competition:
        raise ValueError("No competitions found in competitionconfig.json")

    gc = get_gspread_client()
    spreadsheet = gc.open_by_key(active_competition['google_sheet_id'])
    qworksheet = spreadsheet.worksheet(active_competition['quant_worksheet_name'])
    qdf = worksheet_to_dataframe(qworksheet)

    conn = sqlite3.connect("ScoutingData.db")

    def calculate_derived_metrics(df, derived_metrics):
        for metric in derived_metrics:
            try:
                formula = metric['formula']
                referenced_columns = re.findall(r"'([^']+)'", formula)

                rename_map = {}
                normalized_formula = formula

                for col in referenced_columns:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

                        # Build a safe Python identifier from the column name
                        safe_name = re.sub(r'\W+', '_', col).strip('_')
                        rename_map[col] = safe_name

                        # Replace 'Column Name' in the formula with the safe name
                        normalized_formula = normalized_formula.replace(f"'{col}'", safe_name)

                # Evaluate on a temporarily renamed view — doesn't mutate df
                df_eval = df.rename(columns=rename_map)
                df[metric['id']] = df_eval.eval(normalized_formula, engine='python')

            except Exception as e:
                print(f"Error calculating {metric['id']}: {e}")

        return df

    derived_metrics = config.get('computed', [])

    print(derived_metrics)

    cdf = calculate_derived_metrics(qdf, derived_metrics)

    cdf.to_sql("quant", conn, if_exists="replace", index=False)

    try:
        if 'Team Number' in cdf.columns and 'Match Number' in cdf.columns:
            cdf['Match Number'] = pd.to_numeric(cdf['Match Number'], errors='coerce')

            cdf['Team Match Number'] = (
                cdf.groupby('Team Number')['Match Number']
                .rank(method='dense', ascending=True)
                .astype('Int64')
            )
        else:
            print("Warning: 'Team Number' or 'Match Number' column missing; skipping Team Match Number calculation")
    except Exception as e:
        print(f"Error computing Team Match Number: {e}")

    cdf.to_sql("quant", conn, if_exists="replace", index=False)

    pworksheet = spreadsheet.worksheet(active_competition['pit_worksheet_name'])
    pdf = worksheet_to_dataframe(pworksheet)
    pdf.to_sql("pit", conn, if_exists="replace", index=False)

calculate_metrics()