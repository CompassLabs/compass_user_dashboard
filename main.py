import asyncio
from io import StringIO

import polars as pl
from logfire.query_client import AsyncLogfireQueryClient
from panels.response_codes import get_reponse_codes_table
import streamlit as st
from datetime import datetime, timedelta

st.title('Cyber dashboard')

min_datetime, max_datetime =st.date_input(label='Select date range', value=[datetime.today()-timedelta(days=1), datetime.today()])

df = asyncio.run(get_reponse_codes_table(min_datetime, max_datetime))


st.dataframe(df)
