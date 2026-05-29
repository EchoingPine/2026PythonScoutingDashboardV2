import streamlit as st
import dbcalc

st.title("Home")

st.header("Refresh DB Values")
if st.button("Refresh"):
    dbcalc.calculate_metrics()
    st.success("Database values refreshed")