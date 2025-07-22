import asyncio
import hmac
import os
from datetime import datetime, timedelta

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from streamlit_extras.grid import grid

from panels.distinct_paths import get_distinct_paths
from panels.distinct_users import get_distinct_users
from panels.durations import get_durations
from panels.response_codes import get_reponse_codes_table

users = asyncio.run(get_distinct_users())
users = [u for u in users if u]


def check_password():
    # Do not require password for non-user-sepcific dashboard.
    fixed_user = os.environ.get("FIXED_USER", None)
    if not fixed_user:
        return True

    def password_entered():
        # If you use .streamlit/secrets.toml, replace os.environ.get with st.secrets["STREAMLIT_PASSWORD"]
        if hmac.compare_digest(
            st.session_state["password"], os.environ.get("FIXED_USER_PASSWORD", "")
        ):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated.
    if st.session_state.get("password_correct", False):
        return True

    st.info(f"Please enter the password")
    # Show input for password.
    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False


if not check_password():
    st.stop()


st.set_page_config(
    page_title="Compass user dashboard",
    page_icon="logo.svg",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Compass user dashboard")


col1, col2 = st.columns(2)
with col1:
    fixed_user = os.environ.get("FIXED_USER", None)
    if fixed_user:
        print("user fixed")
        options = [fixed_user]
    else:
        options = sorted(list(users))
    user_email = st.selectbox(label="email", options=options, index=0)
with col2:
    date_range = st.date_input(
        label="Select date range",
        value=[datetime.today() - timedelta(days=14), datetime.today()],
        help="This is the range of dates you want to get data for.",
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

        durations = asyncio.run(get_durations(min_datetime, max_datetime, user_email))
        distinct_paths = set(endpoint_stats["url_path"])

    cols = st.columns(4)
    cols[0].metric("Total requests", df_response_codes.num_seen.sum())
    cols[1].metric(
        "Error rate",
        f"{round(df_response_codes[df_response_codes.response_code != 200].num_seen.sum() / df_response_codes.num_seen.sum() * 100, 1)} %",
    )
    data = np.concatenate(durations["durations"].values)
    p90 = np.percentile(data, 90)
    p50 = np.percentile(data, 50)
    cols[2].metric("90 percentile response time", f"{int(p90)} ms")
    cols[3].metric("50 percentile response time", f"{int(p50)} ms")
    # cols[3].metric(
    #     "Total cost",
    #     f"{df_response_codes[df_response_codes.response_code == '200'].num_seen.sum() * 0.50} $",
    # )

    st.markdown("---")

    cols = st.columns(2)
    cols[0].subheader("Overall Stats")
    cols[0].dataframe(df_response_codes)
    cols[1].subheader("Endpoint stats")
    url_path = cols[1].selectbox(label="endpoint", options=distinct_paths)
    cols[1].dataframe(df_response_codes[df_response_codes.url_path == url_path])

    st.markdown("---")
    st.subheader("Response times")

    # Sample box plot data
    # data = [10, 20, 15, 17, 13, 22, 18, 19, 25]

    # Create a Plotly figure
    st.markdown("### Overall")

    data = np.concatenate(durations["durations"].values)
    p95 = np.percentile(data, 95)
    trace = go.Box(
        x=data,
        name="",
        boxpoints="all",
        jitter=0.5,
        pointpos=0.0,
        marker_color="green" if p95 < 500 else "red",  # Color of box
    )

    layout = go.Layout(title=None, xaxis=dict(title=f"Overall [ms]"))
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

    # Layout
    fig.update_layout(
        annotations=annotations,
        margin=dict(t=10, b=10),
        yaxis=dict(showticklabels=False),
    )

    fig.update_layout(
        margin=dict(t=10, b=10),  # top and bottom margin minimized
        height=250,  # optional: control overall height
    )

    # Display in Streamlit without the menu bar
    st.plotly_chart(
        fig, key="overall", use_container_width=True, config={"displayModeBar": False}
    )

    st.markdown("### Per route")
    my_grid = grid(4, 4, vertical_align="bottom")
    for path in distinct_paths:
        data = durations[durations.url_path == path]["durations"]
        data = list(durations[durations.url_path == path]["durations"].values)[0]
        p50 = np.percentile(data, 50)
        p95 = np.percentile(data, 95)
        trace = go.Box(
            x=data,
            name="",
            boxpoints="all",
            jitter=0.5,
            pointpos=0.0,
            marker_color="green" if p95 < 500 else "red",  # Color of box
        )

        p05 = np.percentile(data, 5)

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
