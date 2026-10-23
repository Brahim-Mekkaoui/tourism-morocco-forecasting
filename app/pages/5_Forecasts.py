"""
Forecasts Page

Multi-horizon forecasts with confidence intervals.

Author: MEKKAOUI Brahim
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def main():
    """Main page content."""
    st.set_page_config(page_title="Forecasts", layout="wide")

    st.title("🔮 Forecasts")
    st.markdown("Multi-horizon predictions with confidence intervals")

    # Check if forecasts exist
    forecast_file = Path("outputs/forecasts.json")

    if not forecast_file.exists():
        st.warning("Forecasts not generated yet. Please run scripts/forecast.py first.")
        st.info("Execute: `python scripts/forecast.py --horizons 1 3 6 12`")
        return

    # Load forecasts
    with open(forecast_file) as f:
        forecasts = json.load(f)

    st.subheader("📊 Available Forecasts")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Horizons Generated", len(forecasts))
    with col2:
        st.metric("Forecast Horizons", ", ".join([f"{h}M" for h in sorted(forecasts.keys())]))
    with col3:
        st.metric("Model", "SARIMAX+PCA")

    st.markdown("---")

    # Select horizon
    st.subheader("🎯 Select Forecast Horizon")

    horizons = sorted([int(h) for h in forecasts.keys()])
    selected_horizon = st.selectbox(
        "Months Ahead",
        horizons,
        format_func=lambda x: f"{x} Month(s)"
    )

    # Get forecast data
    horizon_key = str(selected_horizon)
    forecast_data = forecasts[horizon_key]

    # Create visualization
    st.subheader(f"📈 {selected_horizon}-Month Forecast")

    # Convert to pandas series
    import pandas as pd
    forecast_values = forecast_data['forecast']
    lower_ci = forecast_data['lower_ci']
    upper_ci = forecast_data['upper_ci']
    dates = pd.to_datetime(forecast_data['index'])

    # Create figure
    fig = go.Figure()

    # Forecast line
    fig.add_trace(go.Scatter(
        x=dates,
        y=forecast_values,
        mode='lines+markers',
        name='Forecast',
        line=dict(color='blue', width=2),
        marker=dict(size=8)
    ))

    # Confidence interval
    fig.add_trace(go.Scatter(
        x=dates,
        y=upper_ci,
        fill=None,
        mode='lines',
        line_color='rgba(0,0,255,0)',
        showlegend=False
    ))

    fig.add_trace(go.Scatter(
        x=dates,
        y=lower_ci,
        fill='tonexty',
        mode='lines',
        line_color='rgba(0,0,255,0)',
        name='95% Confidence Interval',
        fillcolor='rgba(0,0,255,0.2)'
    ))

    fig.update_layout(
        title=f"SARIMAX+PCA - {selected_horizon} Month Forecast",
        xaxis_title="Date",
        yaxis_title="Number of Arrivals",
        hovermode='x unified',
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Summary statistics
    st.subheader("📊 Forecast Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Mean Forecast", f"{sum(forecast_values)/len(forecast_values):,.0f}")
    with col2:
        st.metric("Min Forecast", f"{min(forecast_values):,.0f}")
    with col3:
        st.metric("Max Forecast", f"{max(forecast_values):,.0f}")
    with col4:
        st.metric("Std Deviation", f"{pd.Series(forecast_values).std():,.0f}")

    st.markdown("---")

    # Forecast table
    st.subheader("📋 Detailed Forecast")

    forecast_table = pd.DataFrame({
        'Date': dates.strftime('%Y-%m-%d'),
        'Forecast': [f"{v:,.0f}" for v in forecast_values],
        'Lower CI': [f"{v:,.0f}" for v in lower_ci],
        'Upper CI': [f"{v:,.0f}" for v in upper_ci]
    })

    st.dataframe(forecast_table, use_container_width=True)

    st.markdown("---")

    # All horizons comparison
    st.subheader("📊 All Horizons Summary")

    all_horizons_data = []
    for h in horizons:
        h_key = str(h)
        h_data = forecasts[h_key]
        all_horizons_data.append({
            'Horizon (Months)': h,
            'Mean': f"{sum(h_data['forecast'])/len(h_data['forecast']):,.0f}",
            'Min': f"{min(h_data['forecast']):,.0f}",
            'Max': f"{max(h_data['forecast']):,.0f}",
            'Range': f"{max(h_data['forecast'])-min(h_data['forecast']):,.0f}"
        })

    all_horizons_df = pd.DataFrame(all_horizons_data)
    st.dataframe(all_horizons_df, use_container_width=True)

    st.markdown("---")

    # Key insights
    st.subheader("💡 Forecast Insights")

    st.markdown(f"""
    - **Forecast Horizon**: {selected_horizon} month(s) ahead
    - **Mean Expected Value**: {sum(forecast_values)/len(forecast_values):,.0f} arrivals
    - **Forecast Range**: {min(forecast_values):,.0f} to {max(forecast_values):,.0f}
    - **Confidence Level**: 95%
    - **Model**: SARIMAX+PCA (best performing model)

    The forecast is based on:
    - Historical arrivals patterns
    - Google Trends search signals (53 terms)
    - Seasonal components
    - PCA-reduced feature space (3 components)
    """)


if __name__ == "__main__":
    main()
