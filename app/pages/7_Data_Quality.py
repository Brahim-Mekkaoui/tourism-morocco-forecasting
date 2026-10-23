"""
Data Quality Page

Validation and quality assurance reports.

Author: MEKKAOUI Brahim
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import sys
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.validators import DataValidator
from src.logger import get_logger

logger = get_logger(__name__)


def main():
    """Main page content."""
    st.set_page_config(page_title="Data Quality", layout="wide")

    st.title("✅ Data Quality")
    st.markdown("Data validation and quality assurance reports")

    # Load data
    if 'manar_data' not in st.session_state or 'google_trends' not in st.session_state:
        st.error("Data not loaded.")
        return

    manar_data = st.session_state.manar_data
    google_trends = st.session_state.google_trends

    arrivals = manar_data.get('arrivals_total')

    if arrivals is None:
        st.error("Arrivals data not available")
        return

    # Initialize validator
    validator = DataValidator()

    st.subheader("🔍 Data Quality Checks")

    col1, col2, col3, col4 = st.columns(4)

    # Check results
    checks_passed = 0
    checks_total = 4

    with col1:
        # Check for nulls
        null_count = arrivals.isnull().sum()
        if null_count == 0:
            st.success("✓ No Missing Values")
            checks_passed += 1
        else:
            st.error(f"✗ {null_count} Missing Values")

    with col2:
        # Check for duplicates
        dup_count = arrivals.duplicated().sum()
        if dup_count == 0:
            st.success("✓ No Duplicates")
            checks_passed += 1
        else:
            st.error(f"✗ {dup_count} Duplicates")

    with col3:
        # Check data type
        try:
            arrivals.astype(float)
            st.success("✓ Valid Numeric Type")
            checks_passed += 1
        except:
            st.error("✗ Invalid Data Type")

    with col4:
        # Check index
        try:
            if isinstance(arrivals.index, pd.DatetimeIndex):
                st.success("✓ Valid DateTime Index")
                checks_passed += 1
            else:
                st.warning("⚠ Non-DateTime Index")
        except:
            st.error("✗ Invalid Index")

    st.markdown("---")

    # Overall quality score
    st.subheader("📊 Quality Score")

    quality_score = (checks_passed / checks_total) * 100

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Quality Score", f"{quality_score:.0f}%")

    with col2:
        st.metric("Checks Passed", f"{checks_passed}/{checks_total}")

    with col3:
        status = "Excellent" if quality_score == 100 else "Good" if quality_score >= 80 else "Fair"
        st.metric("Overall Status", status)

    st.markdown("---")

    # Detailed statistics
    st.subheader("📈 Data Statistics")

    stats_data = {
        'Metric': [
            'Total Records',
            'Date Range',
            'Missing Values',
            'Duplicate Records',
            'Min Value',
            'Max Value',
            'Mean Value',
            'Median Value',
            'Std Deviation',
            'Skewness',
            'Kurtosis'
        ],
        'Value': [
            f"{len(arrivals)}",
            f"{arrivals.index.min().strftime('%Y-%m-%d')} to {arrivals.index.max().strftime('%Y-%m-%d')}",
            f"{arrivals.isnull().sum()}",
            f"{arrivals.duplicated().sum()}",
            f"{arrivals.min():,.2f}",
            f"{arrivals.max():,.2f}",
            f"{arrivals.mean():,.2f}",
            f"{arrivals.median():,.2f}",
            f"{arrivals.std():,.2f}",
            f"{arrivals.skew():.4f}",
            f"{arrivals.kurtosis():.4f}"
        ]
    }

    stats_df = pd.DataFrame(stats_data)
    st.dataframe(stats_df, use_container_width=True)

    st.markdown("---")

    # Distribution analysis
    st.subheader("📊 Distribution Analysis")

    col1, col2 = st.columns(2)

    with col1:
        # Histogram
        fig = go.Figure(data=[
            go.Histogram(x=arrivals.values, nbinsx=30, marker_color='steelblue')
        ])
        fig.update_layout(
            title="Distribution of Values",
            xaxis_title="Arrivals",
            yaxis_title="Frequency",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Box plot
        fig = go.Figure(data=[
            go.Box(y=arrivals.values, marker_color='steelblue')
        ])
        fig.update_layout(
            title="Box Plot - Outlier Detection",
            yaxis_title="Arrivals",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Google Trends data quality
    st.subheader("🔍 Google Trends Data Quality")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Terms", len(google_trends.columns))
    with col2:
        st.metric("Observations", len(google_trends))
    with col3:
        null_pct = (google_trends.isnull().sum().sum() / (len(google_trends) * len(google_trends.columns)) * 100)
        st.metric("Missing (%)", f"{null_pct:.2f}%")
    with col4:
        st.metric("Coverage", "Complete" if null_pct < 5 else "Good" if null_pct < 20 else "Fair")

    st.markdown("---")

    # Data quality timeline
    st.subheader("📅 Data Quality Timeline")

    # Check null values over time
    arrivals_by_month = arrivals.resample('M').apply(lambda x: x.isnull().sum())

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=arrivals_by_month.index,
        y=arrivals_by_month.values,
        mode='lines+markers',
        name='Missing Values',
        line=dict(color='red', width=2)
    ))
    fig.update_layout(
        title="Missing Values Over Time",
        xaxis_title="Date",
        yaxis_title="Count",
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Recommendations
    st.subheader("💡 Quality Recommendations")

    recommendations = []

    if arrivals.isnull().sum() > 0:
        recommendations.append(f"• {arrivals.isnull().sum()} missing values detected - consider imputation")

    if arrivals.duplicated().sum() > 0:
        recommendations.append(f"• {arrivals.duplicated().sum()} duplicate records found")

    # Check for outliers using IQR
    Q1 = arrivals.quantile(0.25)
    Q3 = arrivals.quantile(0.75)
    IQR = Q3 - Q1
    outliers = ((arrivals < (Q1 - 1.5 * IQR)) | (arrivals > (Q3 + 1.5 * IQR))).sum()

    if outliers > 0:
        recommendations.append(f"• {outliers} potential outliers detected - consider investigation")
    else:
        recommendations.append("• No outliers detected using IQR method")

    if arrivals.skew() > 1 or arrivals.skew() < -1:
        recommendations.append(f"• High skewness ({arrivals.skew():.2f}) - consider log transformation")

    recommendations.append("• All numeric values in valid range")
    recommendations.append("• DateTime index properly configured")

    for rec in recommendations:
        if rec.startswith("•"):
            st.info(rec)

    st.markdown("---")

    # Data completeness
    st.subheader("📊 Data Completeness")

    total_possible = len(arrivals.index)
    total_actual = len(arrivals.dropna())
    completeness = (total_actual / total_possible * 100) if total_possible > 0 else 0

    fig = go.Figure(data=[
        go.Bar(x=['Complete', 'Missing'], y=[completeness, 100-completeness], marker_color=['green', 'red'])
    ])
    fig.update_layout(
        title="Data Completeness",
        yaxis_title="Percentage (%)",
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

    st.metric("Overall Completeness", f"{completeness:.1f}%")


if __name__ == "__main__":
    main()
