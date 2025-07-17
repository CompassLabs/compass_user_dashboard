import asyncio
from io import StringIO

import polars as pl
from logfire.query_client import AsyncLogfireQueryClient
from panels.response_codes import get_reponse_codes_table
import streamlit as st
from datetime import datetime, timedelta

st.title("Compass user dashboard")
user_email = st.text_input(label="email")

min_datetime, max_datetime = st.date_input(
    label="Select date range",
    value=[datetime.today() - timedelta(days=1), datetime.today()],
)


df = asyncio.run(get_reponse_codes_table(min_datetime, max_datetime, user_email))


st.dataframe(df)
