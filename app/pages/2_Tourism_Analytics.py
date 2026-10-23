"""
Tourism Analytics Page

Historical trends and patterns in tourism data.

Author: MEKKAOUI Brahim
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import sys
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.logger import get_logger

logger = get_logger(__name__)


def main():
    """Main page content."""
    st.set_page_config(page_title="Tourism Analytics", layout="wide")

    st.title("📈 Tourism Analytics")
    st.markdown("Historical trends and patterns in Moroccan tourism")

    # Load data
    if 'manar_data' not in st.session_state:
        st.error("Data not loaded. Please reload the main dashboard.")
        return

    manar_data = st.session_state.manar_data

    # Sidebar filters
    st.sidebar.header("Filters")

    # Get available metrics
    available_metrics = list(manar_data.keys())
    selected_metric = st.sidebar.selectbox("Select Metric", available_metrics)

    data = manar_data[selected_metric]

    if data is None:
        st.error(f"Data for {selected_metric} not available")
        return

    # Main content
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader(f"📊 {selected_metric}")

    with col2:
        date_range = st.selectbox(
            "Time Period",
            ["All Time", "Last 12 Months", "Last 24 Months"],
            key="date_range"
        )

    # Filter data based on date range
    if date_range == "Last 12 Months":
        data_to_plot = data.iloc[-12:]
    elif date_range == "Last 24 Months":
        data_to_plot = data.iloc[-24:]
    else:
        data_to_plot = data

    # Time series plot
    st.subheader("Time Series")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=data_to_plot.index,
        y=data_to_plot.values,
        mode='lines+markers',
        name=selected_metric,
        line=dict(color='#1f77b4', width=2),
        marker=dict(size=6),
        fill='tozeroy'
    ))
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Value",
        hovermode='x unified',
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Statistics
    st.subheader("📊 Statistics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Mean", f"{data_to_plot.mean():,.0f}")
    with col2:
        st.metric("Median", f"{data_to_plot.median():,.0f}")
    with col3:
        st.metric("Std Dev", f"{data_to_plot.std():,.0f}")
    with col4:
        st.metric("Latest", f"{data_to_plot.iloc[-1]:,.0f}")

    st.markdown("---")

    # Monthly decomposition
    st.subheader("📅 Monthly Pattern")

    # Extract month from index
    if hasattr(data.index, 'month'):
        monthly_pattern = data.groupby(data.index.month).mean()
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

        fig = go.Figure(data=[
            go.Bar(x=months, y=monthly_pattern.values, marker_color='steelblue')
        ])
        fig.update_layout(
            title="Average by Month",
            xaxis_title="Month",
            yaxis_title="Average Value",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Growth rate
    st.subheader("📈 Growth Rate")

    growth = data_to_plot.pct_change() * 100

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=growth.index,
        y=growth.values,
        mode='lines+markers',
        name='Growth Rate (%)',
        line=dict(color='#ff7f0e', width=2),
        marker=dict(size=6)
    ))
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Growth Rate (%)",
        hovermode='x unified',
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Summary statistics table
    st.subheader("📋 Summary Statistics")

    summary_data = {
        'Metric': [
            'Count',
            'Mean',
            'Std Dev',
            'Min',
            '25%',
            'Median',
            '75%',
            'Max'
        ],
        'Value': [
            f"{len(data_to_plot)}",
            f"{data_to_plot.mean():,.2f}",
            f"{data_to_plot.std():,.2f}",
            f"{data_to_plot.min():,.2f}",
            f"{data_to_plot.quantile(0.25):,.2f}",
            f"{data_to_plot.median():,.2f}",
            f"{data_to_plot.quantile(0.75):,.2f}",
            f"{data_to_plot.max():,.2f}"
        ]
    }

    summary_df = pd.DataFrame(summary_data)
    st.dataframe(summary_df, use_container_width=True)


if __name__ == "__main__":
    main()
