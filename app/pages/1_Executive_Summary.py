"""
Executive Summary Page

Key KPIs and high-level overview of tourism metrics.

Author: MEKKAOUI Brahim
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config import get_config
from src.logger import get_logger

logger = get_logger(__name__)


def create_kpi_card(label, value, unit="", change=None, color="blue"):
    """Create a KPI display card."""
    col1, col2 = st.columns([3, 1])

    with col1:
        st.metric(
            label=label,
            value=f"{value:,.0f}" if isinstance(value, (int, float)) else value,
            delta=change
        )


def main():
    """Main page content."""
    st.set_page_config(page_title="Executive Summary", layout="wide")

    st.title("📊 Executive Summary")
    st.markdown("High-level KPIs and overview of tourism performance")

    # Load data
    if 'manar_data' not in st.session_state:
        st.error("Data not loaded. Please reload the main dashboard.")
        return

    manar_data = st.session_state.manar_data

    # Get arrivals data
    arrivals = manar_data.get('arrivals_total')
    if arrivals is None:
        st.error("Arrivals data not available")
        return

    # Create two-column layout
    col1, col2, col3, col4 = st.columns(4)

    # KPI 1: Total Arrivals
    with col1:
        st.metric(
            "Total Arrivals",
            f"{arrivals.sum():,.0f}",
            f"{(arrivals.iloc[-12:].sum() / arrivals.iloc[-24:-12].sum() - 1)*100:+.1f}% YoY"
        )

    # KPI 2: Latest Month
    with col2:
        st.metric(
            "Latest Month",
            f"{arrivals.iloc[-1]:,.0f}",
            f"{(arrivals.iloc[-1] / arrivals.iloc[-2] - 1)*100:+.1f}% MoM"
        )

    # KPI 3: Average
    with col3:
        st.metric(
            "Average Monthly",
            f"{arrivals.mean():,.0f}",
            f"±{arrivals.std():,.0f}"
        )

    # KPI 4: Data Coverage
    with col4:
        st.metric(
            "Data Points",
            f"{len(arrivals)}",
            "Month(s)"
        )

    st.markdown("---")

    # Trends
    st.subheader("📈 Trends")

    col1, col2 = st.columns(2)

    # Monthly arrivals trend
    with col1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=arrivals.index,
            y=arrivals.values,
            mode='lines',
            name='Monthly Arrivals',
            line=dict(color='#1f77b4', width=2),
            fill='tozeroy'
        ))
        fig.update_layout(
            title="Tourist Arrivals Trend",
            xaxis_title="Month",
            yaxis_title="Number of Arrivals",
            hovermode='x unified',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

    # Year-over-year comparison
    with col2:
        # Get latest 12 months and previous 12 months
        latest_12 = arrivals.iloc[-12:].values
        previous_12 = arrivals.iloc[-24:-12].values
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

        fig = go.Figure(data=[
            go.Bar(name='Previous Year', x=months, y=previous_12, marker_color='lightblue'),
            go.Bar(name='Current Year', x=months, y=latest_12, marker_color='darkblue')
        ])
        fig.update_layout(
            title="Year-over-Year Comparison",
            xaxis_title="Month",
            yaxis_title="Number of Arrivals",
            barmode='group',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Performance Metrics
    st.subheader("📊 Performance Metrics")

    # Calculate statistics
    stats_data = {
        'Metric': [
            'Minimum Monthly',
            'Maximum Monthly',
            'Median Monthly',
            'Standard Deviation',
            'Coefficient of Variation',
            'Growth Rate (Last 12M)'
        ],
        'Value': [
            f"{arrivals.min():,.0f}",
            f"{arrivals.max():,.0f}",
            f"{arrivals.median():,.0f}",
            f"{arrivals.std():,.0f}",
            f"{arrivals.std()/arrivals.mean()*100:.1f}%",
            f"{(arrivals.iloc[-1]/arrivals.iloc[-13]**(1/12) - 1)*100:+.1f}%"
        ]
    }

    stats_df = pd.DataFrame(stats_data)
    st.dataframe(stats_df, use_container_width=True)

    st.markdown("---")

    # Recent Performance
    st.subheader("📅 Recent Performance")

    # Last 12 months
    last_12_months = arrivals.tail(12)
    recent_df = pd.DataFrame({
        'Month': last_12_months.index.strftime('%B %Y'),
        'Arrivals': last_12_months.values,
        'Change (%)': last_12_months.pct_change() * 100
    })

    st.dataframe(recent_df, use_container_width=True)

    st.markdown("---")

    # Model Status
    st.subheader("🤖 Model Status")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.info("""
        **Best Model**: SARIMAX+PCA

        - RMSE: 0.86
        - MAE: 0.72
        - MAPE: 13.23%
        """)

    with col2:
        st.warning("""
        **Alternative Model**: SARIMAX+PLS

        - RMSE: 0.88
        - MAE: 0.74
        - MAPE: 15.87%
        """)

    with col3:
        st.warning("""
        **Baseline Model**: SARIMA

        - RMSE: 1.00
        - MAE: 0.85
        - MAPE: 33.07%
        """)

    st.markdown("---")

    # Key Insights
    st.subheader("💡 Key Insights")

    st.markdown(f"""
    1. **Total Arrivals**: Morocco has received {arrivals.sum():,.0f} total arrivals across {len(arrivals)} months

    2. **Recent Trend**: The latest month shows {arrivals.iloc[-1]:,.0f} arrivals, representing
       a {(arrivals.iloc[-1]/arrivals.iloc[-2]-1)*100:+.1f}% change from the previous month

    3. **Seasonal Pattern**: Average monthly arrivals is {arrivals.mean():,.0f} with a standard deviation
       of {arrivals.std():,.0f}, indicating {arrivals.std()/arrivals.mean()*100:.1f}% variability

    4. **Growth**: The 12-month rolling growth rate is {(arrivals.iloc[-1]/arrivals.iloc[-13]**(1/12) - 1)*100:+.1f}%

    5. **Forecast Accuracy**: The best model (SARIMAX+PCA) achieves 13.23% MAPE,
       a 60% improvement over the baseline SARIMA model
    """)


if __name__ == "__main__":
    main()
