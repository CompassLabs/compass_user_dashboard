import asyncio
from io import StringIO
import numpy as np
import polars as pl
from logfire.query_client import AsyncLogfireQueryClient
from panels.response_codes import get_reponse_codes_table
from panels.distinct_paths import get_distinct_paths
import streamlit as st
from datetime import datetime, timedelta
from streamlit_extras.grid import grid
import plotly.graph_objects as go

st.set_page_config(
    page_title="Compass user dashboard",
    page_icon="logo.svg",
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

    with st.spinner("Analyzing user data"):
        df_response_codes = asyncio.run(
            get_reponse_codes_table(min_datetime, max_datetime, user_email)
        )
        endpoint_stats = asyncio.run(
            get_distinct_paths(min_datetime, max_datetime, user_email)
        )
        distinct_paths = set(endpoint_stats["url_path"])

    cols = st.columns(4)
    cols[0].metric("Total requests", df_response_codes.num_seen.sum())
    cols[1].metric(
        "Error rate",
        f"{round(df_response_codes[df_response_codes.response_code != '200'].num_seen.sum() / df_response_codes.num_seen.sum() * 100, 1)} %",
    )
    cols[2].metric("95 percentile response", "200 ms")
    cols[3].metric(
        "Total cost",
        f"{df_response_codes[df_response_codes.response_code == '200'].num_seen.sum() * 0.50} $",
    )

    st.markdown("---")

    cols = st.columns(2)
    cols[0].subheader("Overall Stats")
    cols[0].dataframe(df_response_codes)
    cols[1].subheader("Endpoint stats")
    cols[1].selectbox(label="endpoint", options=distinct_paths)
    cols[1].dataframe(df_response_codes)

    st.markdown("---")
    st.subheader("Response times")

    # Sample box plot data
    # data = [10, 20, 15, 17, 13, 22, 18, 19, 25]

    # Create a Plotly figure
    st.markdown("### Overall")

    data = endpoint_stats["duration"]
    trace = go.Box(
        x=data,
        name="",
        boxpoints="all",
        jitter=0.5,
        pointpos=0.0,
    )

    layout = go.Layout(title=None, xaxis=dict(title=f"Overall [ms]"))
    fig = go.Figure(data=trace, layout=layout)

    p95 = np.percentile(data, 95)
    annotations = [
        dict(
            x=p95,
            y="aaa",
            text=f"p95={round(p95, 1)}",
            showarrow=True,
            arrowhead=1,
            ax=0,
            ay=-20,
        ),
    ]

    # Layout
    fig.update_layout(
        annotations=annotations,
        margin=dict(t=10, b=10),
        height=200,
        yaxis=dict(showticklabels=False),
    )

    fig.update_layout(
        margin=dict(t=10, b=10),  # top and bottom margin minimized
        height=150,  # optional: control overall height
    )

    # Display in Streamlit without the menu bar
    st.plotly_chart(
        fig, key="overall", use_container_width=True, config={"displayModeBar": False}
    )

    st.markdown("### Per route")
    my_grid = grid(4, 4, vertical_align="bottom")
    for path in distinct_paths:
        data = endpoint_stats[endpoint_stats.url_path == path]["duration"]
        trace = go.Box(
            x=data,
            name="",
            boxpoints="all",
            jitter=0.5,
            pointpos=0.0,
        )

        p05 = np.percentile(data, 5)
        p50 = np.percentile(data, 50)
        p95 = np.percentile(data, 95)

        layout = go.Layout(title=None, xaxis=dict(title=f"{path} [ms]"))
        fig = go.Figure(data=trace, layout=layout)

        annotations = [
            dict(
                x=p95,
                y="aaa",
                text=f"p95={round(p95, 1)}",
                showarrow=True,
                arrowhead=1,
                ax=0,
                ay=-20,
            ),
        ]

        fig.update_layout(
            annotations=annotations,
            margin=dict(t=10, b=10),  # top and bottom margin minimized
            height=150,  # optional: control overall height
        )

        # Display in Streamlit without the menu bar
        my_grid.plotly_chart(
            fig, key=path, use_container_width=True, config={"displayModeBar": False}
        )

    # my_grid.plotly_chart(fig, key="1",  use_container_width=True, config={"displayModeBar": False})
    # my_grid.plotly_chart(fig, key="2",  use_container_width=True, config={"displayModeBar": False})
    # my_grid.plotly_chart(fig, key="3",  use_container_width=True, config={"displayModeBar": False})
    # my_grid.plotly_chart(fig, key="4",  use_container_width=True, config={"displayModeBar": False})
    # my_grid.dataframe(df_response_codes)
    # my_grid.dataframe(df_response_codes)
    # my_grid.dataframe(df_response_codes)
    # my_grid.dataframe(df_response_codes)
    # my_grid.dataframe(df_response_codes)
    # my_grid.dataframe(df_response_codes)
    # my_grid.dataframe(df_response_codes)
