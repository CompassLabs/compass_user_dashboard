import asyncio
from io import StringIO

import polars as pl
from logfire.query_client import AsyncLogfireQueryClient
from panels.response_codes import get_reponse_codes_table
import streamlit as st
from datetime import datetime, timedelta


st.set_page_config(
    page_title="Compass user dashboard",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Compass user dashboard")


col1, col2 = st.columns(2)
with col1:
    user_email = st.text_input(label="email", value="aidar@compasslabs.ai")
with col2:
    date_range = st.date_input(
        label="Select date range",
        value=[datetime.today() - timedelta(days=1), datetime.today()],
    )
st.markdown("---")


if len(date_range) == 2:
    min_datetime, max_datetime = date_range

    cols = st.columns(4)
    cols[1].metric("Error rate", "0.01%")
    cols[0].metric("Total requests", "541")
    cols[2].metric("95 percentile response", "200 ms")
    cols[3].metric("Total cost", "5.3 $")

    st.markdown("---")

    cols = st.columns(2)
    with st.spinner("Analyzing user data"):
        df = asyncio.run(
            get_reponse_codes_table(min_datetime, max_datetime, user_email)
        )

        cols[0].subheader("Table 0")
        cols[0].dataframe(df)

        cols[1].subheader("Table 1")
        cols[1].dataframe(df)
