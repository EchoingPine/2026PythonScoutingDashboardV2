import json
import os
import sqlite3
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd
import streamlit as st


ROOT = Path(__file__).parent
PAGE_CONFIG_PATH = ROOT / "page_configs.json"
COMPETITION_CONFIG_PATH = ROOT / "competitionconfig.json"
DB_PATH = ROOT / "ScoutingData.db"
LOCAL_SERVICE_ACCOUNT_PATH = ROOT / "data_reader_account.json"


def _streamlit_runtime_active() -> bool:
    try:
        from streamlit.runtime.scriptrunner_utils.script_run_context import get_script_run_ctx

        return get_script_run_ctx() is not None
    except Exception:
        return False


def cache_data(func=None, **kwargs):
    if func is None:
        def decorator(inner_func):
            if _streamlit_runtime_active():
                return st.cache_data(**kwargs)(inner_func)
            return inner_func

        return decorator

    if _streamlit_runtime_active():
        return st.cache_data(**kwargs)(func)

    return func


def cache_resource(func=None, **kwargs):
    if func is None:
        def decorator(inner_func):
            if _streamlit_runtime_active():
                return st.cache_resource(**kwargs)(inner_func)
            return inner_func

        return decorator

    if _streamlit_runtime_active():
        return st.cache_resource(**kwargs)(func)

    return func


def _get_streamlit_secret(name: str, default=None):
    if not _streamlit_runtime_active():
        return default

    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


@cache_data
def load_page_config() -> dict:
    with PAGE_CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_page_config(page_name: str) -> dict | None:
    config = load_page_config()
    return next((p for p in config.get("page_configs", []) if p.get("page_name") == page_name), None)


def get_navigation_config() -> list[dict]:
    config = load_page_config()
    return config.get("navigation", [])


@cache_data
def load_competition_config() -> dict:
    with COMPETITION_CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_active_competition() -> dict | None:
    config = load_competition_config()
    competitions = config.get("competitions", [])
    if not competitions:
        return None
    return competitions[0]


@cache_data
def load_service_account_info() -> dict | None:
    raw_secret = _get_streamlit_secret("gcp_service_account_json", "")
    if raw_secret:
        try:
            return json.loads(raw_secret)
        except json.JSONDecodeError:
            return None

    secret_table = _get_streamlit_secret("gcp_service_account")
    if isinstance(secret_table, dict) and secret_table:
        return dict(secret_table)

    if LOCAL_SERVICE_ACCOUNT_PATH.exists():
        with LOCAL_SERVICE_ACCOUNT_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)

    return None


def get_tba_api_key(explicit_key: str | None = None) -> str:
    if explicit_key:
        return explicit_key

    secret_key = _get_streamlit_secret("tba_api_key", "")
    if secret_key:
        return secret_key

    return os.getenv("TBA_API_KEY", "")


def get_gspread_client():
    import gspread
    from google.oauth2.service_account import Credentials

    service_account_info = load_service_account_info()
    if not service_account_info:
        raise RuntimeError(
            "Missing Google Sheets credentials. Set gcp_service_account_json in Streamlit secrets or keep data_reader_account.json locally."
        )

    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    credentials = Credentials.from_service_account_info(service_account_info, scopes=scopes)
    return gspread.authorize(credentials)


@cache_resource
def get_db_path() -> str:
    return str(DB_PATH)


@cache_data
def query_df(query: str, params: tuple = ()) -> pd.DataFrame:
    # Open a connection per call to avoid cross-thread connection reuse in Streamlit.
    with sqlite3.connect(get_db_path()) as conn:
        return pd.read_sql_query(query, conn, params=params)


def load_team_data(team_number: int) -> pd.DataFrame:
    query = 'SELECT * FROM quant WHERE "Team Number" = ?'
    return query_df(query, (team_number,))


def load_all_teams() -> list[int]:
    query = 'SELECT DISTINCT "Team Number" FROM quant ORDER BY "Team Number"'
    df = query_df(query)
    return df["Team Number"].tolist() if "Team Number" in df.columns else []


def _fetch_tba_json(url: str, tba_api_key: str | None) -> list[dict]:
    api_key = get_tba_api_key(tba_api_key)
    if not api_key:
        return []

    req = Request(url, headers={"X-TBA-Auth-Key": api_key})
    try:
        with urlopen(req, timeout=10) as response:
            payload = response.read().decode("utf-8")
            return json.loads(payload)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return []


@cache_data(ttl=120)
def fetch_tba_event_matches(event_key: str, tba_api_key: str | None = None) -> list[dict]:
    url = f"https://www.thebluealliance.com/api/v3/event/{event_key}/matches"
    return _fetch_tba_json(url, tba_api_key)


@cache_data(ttl=120)
def fetch_tba_event_matches_simple(event_key: str, tba_api_key: str | None = None) -> list[dict]:
    url = f"https://www.thebluealliance.com/api/v3/event/{event_key}/matches/simple"
    return _fetch_tba_json(url, tba_api_key)