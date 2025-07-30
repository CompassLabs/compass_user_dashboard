import asyncio
from datetime import datetime, timedelta

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from streamlit_extras.grid import grid

from panels.api_key_for_user import get_api_key_for_user
from panels.distinct_paths import get_distinct_paths
from panels.distinct_users import get_distinct_users
from panels.durations import get_durations
from panels.response_codes import get_reponse_codes_table

users = asyncio.run(get_distinct_users())
users = [u for u in users if u]


if not st.session_state.get("password_correct", False):

    def password_entered(email: str, api_key: str):
        expected_api_key = asyncio.run(get_api_key_for_user(email))
        if expected_api_key == api_key:
            st.session_state["password_correct"] = True
            st.session_state["email"] = email
            st.rerun()
        else:
            st.session_state["password_correct"] = False
            st.error("API key incorrect")

    email_input = st.text_input("Email", key="email_input")
    api_key_input = st.text_input("API key", type="password", key="password")
    if api_key_input:
        password_entered(email_input, api_key_input)

else:
    st.set_page_config(
        page_title="Compass user dashboard",
        page_icon="logo.svg",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("Compass user dashboard")
    st.text("Use this dashboard to track your usage of the Compass API.")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        options = [st.session_state.get("email", "")]
        if st.session_state.get("email", "").endswith("compasslabs.ai"):
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

            durations = asyncio.run(
                get_durations(min_datetime, max_datetime, user_email)
            )
            distinct_paths = set(endpoint_stats["url_path"])

        cols = st.columns(5)
        cols[0].metric(
            "Total requests",
            df_response_codes.num_seen.sum(),
            help="Total requests the user has sent. Including both successful and unsuccesful ones.",
        )
        cols[1].metric(
            "400 Error rate",
            f"{round(df_response_codes[(df_response_codes.response_code > 399) & (df_response_codes.response_code < 500)].num_seen.sum() / df_response_codes.num_seen.sum() * 100, 1)} %",
            help="These are errors relating to bad requests. For example not following the endpoint specification. Also requests that are impossible, e.g. transferring tokens the user does not have.",
        )
        cols[2].metric(
            "500 Error rate",
            f"{round(df_response_codes[df_response_codes.response_code > 499].num_seen.sum() / df_response_codes.num_seen.sum() * 100, 1)} %",
            help="These are server errors occuring on Compass Labs side.",
        )
        data = np.concatenate(durations["durations"].values)
        p90 = np.percentile(data, 90)
        p50 = np.percentile(data, 50)
        cols[3].metric("90 percentile response time", f"{int(p90)} ms")
        cols[4].metric("50 percentile response time", f"{int(p50)} ms")
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
            marker_color="gray",  # Color of box
            # marker_color="green" if p95 < 500 else "red",  # Color of box
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
            fig,
            key="overall",
            use_container_width=True,
            config={"displayModeBar": False},
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
                marker_color="gray",  # Color of box
                # marker_color="green" if p95 < 500 else "red",  # Color of box
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
                fig,
                key=path,
                use_container_width=True,
                config={"displayModeBar": False},
            )
