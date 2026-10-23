"""
Streamlit Dashboard - Main Application

Tourism Morocco Forecasting & Intelligence Dashboard
Multi-page application with 7 pages for analysis and forecasting.

Usage:
    streamlit run app/dashboard.py

Author: MEKKAOUI Brahim
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_config
from src.logger import get_logger
from src.data.loaders import DataLoader

logger = get_logger(__name__)


# Configure page
st.set_page_config(
    page_title="Tourism Morocco Dashboard",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding-top: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    h1 {
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    h2 {
        color: #ff7f0e;
        border-bottom: 2px solid #ff7f0e;
        padding-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)


def load_data():
    """Load data from files."""
    try:
        data_loader = DataLoader()
        manar_data, google_trends = data_loader.load_all_data()
        return manar_data, google_trends
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None, None


def main():
    """Main dashboard application."""

    # Sidebar
    st.sidebar.title("🏨 Tourism Morocco Dashboard")
    st.sidebar.markdown("---")

    # About section
    st.sidebar.markdown("""
    ### About This Dashboard

    This dashboard provides comprehensive analysis and forecasting
    of Moroccan tourism metrics using:

    - **MANAR Data**: Official Ministry of Tourism statistics
    - **Google Trends**: Search trend indicators
    - **SARIMA/SARIMAX Models**: Time series forecasting

    ### Key Features

    ✓ Real-time KPIs
    ✓ Historical trends
    ✓ Forecasts with confidence intervals
    ✓ Crisis impact analysis
    ✓ Model performance comparison
    ✓ Data quality validation

    ---

    **Author**: MEKKAOUI Brahim
    **Supervisor**: KHTIRA Rachida
    **Institution**: ESI + DEPF
    **Date**: 2026-10-06
    """)

    # Load data
    with st.spinner("Loading data..."):
        manar_data, google_trends = load_data()

    if manar_data is None or google_trends is None:
        st.stop()

    # Store in session
    st.session_state.manar_data = manar_data
    st.session_state.google_trends = google_trends

    # Main title
    st.title("🏨 Tourism Morocco Forecasting & Intelligence Dashboard")

    # Display current date
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Dashboard Version", "1.0")
    with col2:
        st.metric("Data Source", "MANAR + Google Trends")
    with col3:
        st.metric("Update Frequency", "Monthly")

    st.markdown("---")

    # Page selection info
    st.info(
        """
        👈 Select a page from the sidebar to explore:

        1. **Executive Summary** - Key metrics and KPIs
        2. **Tourism Analytics** - Historical trends and patterns
        3. **Google Trends Analysis** - Search trends correlation
        4. **Model Performance** - Model comparison and metrics
        5. **Forecasts** - Multi-horizon predictions
        6. **Crisis Analysis** - Impact of major events
        7. **Data Quality** - Validation and quality reports
        """
    )

    st.markdown("---")

    # Display quick statistics
    st.subheader("📊 Quick Statistics")

    arrivals = manar_data.get('arrivals_total')
    if arrivals is not None:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Arrivals", f"{arrivals.sum():,.0f}")

        with col2:
            st.metric("Average Monthly", f"{arrivals.mean():,.0f}")

        with col3:
            st.metric("Latest Month", f"{arrivals.iloc[-1]:,.0f}")

        with col4:
            st.metric("Data Points", f"{len(arrivals)}")

    st.markdown("---")

    # Footer
    st.markdown("""
    <hr>
    <div style='text-align: center; color: gray; font-size: 12px;'>
        Tourism Morocco Forecasting Dashboard | © 2026 ESI + DEPF
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
