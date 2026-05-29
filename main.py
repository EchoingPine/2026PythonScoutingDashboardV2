import streamlit as st

st.set_page_config(
    page_title="Scouting Dashboard",
    page_icon=":material/analytics:",
    layout="wide",
    initial_sidebar_state="expanded",
)

pg = st.navigation([
    st.Page("pages/00_home_page.py", title="Home", icon=":material/analytics:"),
    st.Page("pages/01_single_team.py", title="Single Team", icon=":material/analytics:"),
    st.Page("pages/02_compare.py", title="Compare Teams", icon=":material/analytics:"),
    st.Page("pages/03_averages.py", title="Averages", icon=":material/analytics:"),
    st.Page(
        "pages/08_strategy_board.py",
        title="Strategy Board",
        icon=":material/open_in_new:"
    ),
])
pg.run()

st.logo(image="assets/inverse polarity logo magnet.png", size="large")