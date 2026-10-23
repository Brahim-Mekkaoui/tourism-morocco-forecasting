"""
Crisis Analysis Page

Impact of major events (COVID-19, earthquakes) on tourism.

Author: MEKKAOUI Brahim
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.analysis.crisis import CrisisAnalyzer
from src.logger import get_logger

logger = get_logger(__name__)


def main():
    """Main page content."""
    st.set_page_config(page_title="Crisis Analysis", layout="wide")

    st.title("🚨 Crisis Analysis")
    st.markdown("Impact of major events on Moroccan tourism")

    # Load data
    if 'manar_data' not in st.session_state:
        st.error("Data not loaded.")
        return

    manar_data = st.session_state.manar_data
    arrivals = manar_data.get('arrivals_total')

    if arrivals is None:
        st.error("Arrivals data not available")
        return

    # Initialize analyzer
    analyzer = CrisisAnalyzer()

    # Analyze all crises
    st.subheader("📊 Crisis Impact Analysis")

    # Select crisis
    crisis_options = list(analyzer.CRISIS_PERIODS.keys())
    selected_crisis = st.selectbox("Select Crisis to Analyze", crisis_options)

    # Analyze selected crisis
    analysis = analyzer.analyze_crisis_impact(arrivals, selected_crisis)

    # Display crisis info
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader(f"📅 {analysis['description']}")
        st.info(f"Period: {analysis['period']}")

    with col2:
        impact_pct = analysis['impact_pct']
        recovery_pct = analysis['recovery_pct']

        st.metric("Impact (%)", f"{impact_pct:+.1f}%", delta=f"vs pre-crisis")
        st.metric("Recovery (%)", f"{recovery_pct:+.1f}%", delta=f"vs pre-crisis")

    st.markdown("---")

    # Comparison chart
    st.subheader("📈 Pre/During/Post Crisis Comparison")

    comparison_data = {
        'Period': ['Pre-Crisis', 'During Crisis', 'Post-Crisis'],
        'Mean': [
            analysis['pre_crisis']['mean'],
            analysis['during_crisis']['mean'],
            analysis['post_crisis']['mean']
        ],
        'Count': [
            analysis['pre_crisis']['count'],
            analysis['during_crisis']['count'],
            analysis['post_crisis']['count']
        ]
    }

    fig = go.Figure(data=[
        go.Bar(
            x=comparison_data['Period'],
            y=comparison_data['Mean'],
            marker_color=['green', 'red', 'blue'],
            text=[f"{v:,.0f}" for v in comparison_data['Mean']],
            textposition='auto'
        )
    ])

    fig.update_layout(
        title=f"Average Arrivals: {selected_crisis}",
        xaxis_title="Period",
        yaxis_title="Average Monthly Arrivals",
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Detailed statistics
    st.subheader("📊 Detailed Statistics")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Pre-Crisis Period**")
        st.metric("Mean", f"{analysis['pre_crisis']['mean']:,.0f}")
        st.metric("Std Dev", f"{analysis['pre_crisis']['std']:,.0f}")
        st.metric("Range", f"{analysis['pre_crisis']['min']:,.0f} - {analysis['pre_crisis']['max']:,.0f}")
        st.metric("Months", f"{analysis['pre_crisis']['count']}")

    with col2:
        st.markdown("**During Crisis Period**")
        st.metric("Mean", f"{analysis['during_crisis']['mean']:,.0f}")
        st.metric("Std Dev", f"{analysis['during_crisis']['std']:,.0f}")
        st.metric("Range", f"{analysis['during_crisis']['min']:,.0f} - {analysis['during_crisis']['max']:,.0f}")
        st.metric("Months", f"{analysis['during_crisis']['count']}")

    with col3:
        st.markdown("**Post-Crisis Period**")
        st.metric("Mean", f"{analysis['post_crisis']['mean']:,.0f}")
        st.metric("Std Dev", f"{analysis['post_crisis']['std']:,.0f}")
        st.metric("Range", f"{analysis['post_crisis']['min']:,.0f} - {analysis['post_crisis']['max']:,.0f}")
        st.metric("Months", f"{analysis['post_crisis']['count']}")

    st.markdown("---")

    # All crises summary
    st.subheader("🌍 All Crises Summary")

    all_analyses = analyzer.analyze_all_crises(arrivals)
    summary_table = analyzer.get_crisis_summary(all_analyses)

    st.dataframe(summary_table, use_container_width=True)

    st.markdown("---")

    # Structural breaks
    st.subheader("🔍 Structural Breaks Detection")

    breaks = analyzer.detect_structural_breaks(arrivals, window_size=12)

    if breaks:
        breaks_df = pd.DataFrame(breaks)
        st.dataframe(breaks_df, use_container_width=True)
    else:
        st.info("No significant structural breaks detected")

    st.markdown("---")

    # Anomalies
    st.subheader("⚠️ Anomalies Detected")

    anomalies = analyzer.identify_anomalies(arrivals, threshold=2.5)

    if len(anomalies) > 0:
        st.dataframe(anomalies, use_container_width=True)
    else:
        st.info("No anomalies detected (threshold: 2.5 standard deviations)")

    st.markdown("---")

    # Key insights
    st.subheader("💡 Analysis Insights")

    st.markdown(f"""
    **Crisis**: {analysis['description']}

    **Impact**: Tourism arrivals decreased by {abs(analysis['impact_pct']):.1f}% during the crisis period
    compared to pre-crisis levels.

    **Recovery**: Post-crisis arrivals are {recovery_pct:+.1f}% compared to pre-crisis baseline,
    indicating {'full recovery' if recovery_pct > -5 else 'partial recovery' if recovery_pct > -50 else 'continued impact'}.

    **Duration**: The crisis lasted for {analysis['during_crisis']['count']} months
    with {analysis['post_crisis']['count']} months of observed recovery data.
    """)


if __name__ == "__main__":
    main()
