"""
Google Trends Analysis Page

Search trend analysis and correlation with tourism metrics.

Author: MEKKAOUI Brahim
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.logger import get_logger

logger = get_logger(__name__)


def main():
    """Main page content."""
    st.set_page_config(page_title="Google Trends Analysis", layout="wide")

    st.title("🔍 Google Trends Analysis")
    st.markdown("Search trend indicators and correlation with tourism metrics")

    # Load data
    if 'google_trends' not in st.session_state:
        st.error("Google Trends data not loaded.")
        return

    google_trends = st.session_state.google_trends

    if google_trends is None or len(google_trends) == 0:
        st.error("Google Trends data is empty")
        return

    st.subheader("📊 Google Trends Overview")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Number of Terms", len(google_trends.columns))
    with col2:
        st.metric("Data Points", len(google_trends))
    with col3:
        st.metric("Date Range", f"{google_trends.index[0].strftime('%Y-%m-%d')} to {google_trends.index[-1].strftime('%Y-%m-%d')}")

    st.markdown("---")

    # Top trends
    st.subheader("🔝 Top Search Terms (Latest Month)")

    latest_trends = google_trends.iloc[-1].nlargest(10)

    fig = go.Figure(data=[
        go.Bar(x=latest_trends.values, y=latest_trends.index, orientation='h', marker_color='steelblue')
    ])
    fig.update_layout(
        title="Top 10 Search Terms",
        xaxis_title="Search Interest",
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Trend over time
    st.subheader("📈 Trend Evolution")

    col1, col2 = st.columns([3, 1])

    with col2:
        selected_terms = st.multiselect(
            "Select Terms to Plot",
            google_trends.columns.tolist(),
            default=google_trends.columns.tolist()[:5]
        )

    with col1:
        if selected_terms:
            fig = go.Figure()
            for term in selected_terms:
                fig.add_trace(go.Scatter(
                    x=google_trends.index,
                    y=google_trends[term],
                    mode='lines',
                    name=term
                ))

            fig.update_layout(
                title="Selected Terms Over Time",
                xaxis_title="Date",
                yaxis_title="Search Interest",
                hovermode='x unified',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Correlation analysis
    st.subheader("📊 Correlation Analysis")

    # Get arrivals from session
    if 'manar_data' in st.session_state:
        manar_data = st.session_state.manar_data
        arrivals = manar_data.get('arrivals_total')

        if arrivals is not None:
            # Align data
            common_index = arrivals.index.intersection(google_trends.index)
            arrivals_aligned = arrivals.loc[common_index]
            gt_aligned = google_trends.loc[common_index]

            # Calculate correlations
            correlations = {}
            for col in gt_aligned.columns:
                corr = arrivals_aligned.corr(gt_aligned[col])
                correlations[col] = corr

            # Sort by absolute correlation
            corr_df = pd.Series(correlations).abs().sort_values(ascending=False)

            col1, col2 = st.columns(2)

            with col1:
                st.metric("Top Correlated Term", corr_df.index[0])
                st.metric("Correlation Strength", f"{abs(correlations[corr_df.index[0]]):.3f}")

            with col2:
                st.metric("Average Correlation", f"{pd.Series(correlations).abs().mean():.3f}")
                st.metric("Max Correlation", f"{pd.Series(correlations).abs().max():.3f}")

            st.markdown("---")

            # Top correlations
            st.subheader("🔗 Top Correlated Terms")

            top_corr = pd.Series(correlations).sort_values(ascending=False).head(15)

            fig = go.Figure(data=[
                go.Bar(x=top_corr.values, y=top_corr.index, orientation='h', marker_color='darkblue')
            ])
            fig.update_layout(
                title="Top 15 Terms Correlated with Arrivals",
                xaxis_title="Correlation Coefficient",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Statistics
    st.subheader("📈 Trends Statistics")

    stats_data = {
        'Metric': [
            'Total Terms',
            'Average Interest',
            'Max Interest',
            'Min Interest',
            'Std Deviation'
        ],
        'Value': [
            f"{len(google_trends.columns)}",
            f"{google_trends.mean().mean():.2f}",
            f"{google_trends.max().max():.2f}",
            f"{google_trends.min().min():.2f}",
            f"{google_trends.std().mean():.2f}"
        ]
    }

    stats_df = pd.DataFrame(stats_data)
    st.dataframe(stats_df, use_container_width=True)


if __name__ == "__main__":
    main()
