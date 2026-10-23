"""
Model Performance Page

Model comparison and metrics visualization.

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
    st.set_page_config(page_title="Model Performance", layout="wide")

    st.title("🤖 Model Performance")
    st.markdown("Comparison of forecasting models and their metrics")

    # Load evaluation results
    eval_file = Path("outputs/model_evaluation.json")

    if not eval_file.exists():
        st.warning("Model evaluation results not found. Please run scripts/evaluate.py first.")
        st.info("Execute: `python scripts/evaluate.py`")
        return

    with open(eval_file) as f:
        results = json.load(f)

    # Display model metrics
    st.subheader("📊 Model Metrics Comparison")

    # Prepare data for comparison
    metrics_data = []
    for model, metrics in results.items():
        metrics_data.append({
            'Model': model,
            'RMSE': metrics.get('rmse', 0),
            'MAE': metrics.get('mae', 0),
            'MAPE': metrics.get('mape', 0),
            'R²': metrics.get('r2', 0)
        })

    metrics_df = pd.DataFrame(metrics_data)

    # Display table
    st.dataframe(metrics_df, use_container_width=True)

    st.markdown("---")

    # Visualizations
    col1, col2 = st.columns(2)

    # RMSE comparison
    with col1:
        fig = go.Figure(data=[
            go.Bar(x=metrics_df['Model'], y=metrics_df['RMSE'], marker_color='steelblue')
        ])
        fig.update_layout(
            title="Root Mean Squared Error (RMSE)",
            xaxis_title="Model",
            yaxis_title="RMSE",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

    # MAPE comparison
    with col2:
        fig = go.Figure(data=[
            go.Bar(x=metrics_df['Model'], y=metrics_df['MAPE'], marker_color='coral')
        ])
        fig.update_layout(
            title="Mean Absolute Percentage Error (MAPE)",
            xaxis_title="Model",
            yaxis_title="MAPE (%)",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    col1, col2 = st.columns(2)

    # MAE comparison
    with col1:
        fig = go.Figure(data=[
            go.Bar(x=metrics_df['Model'], y=metrics_df['MAE'], marker_color='lightgreen')
        ])
        fig.update_layout(
            title="Mean Absolute Error (MAE)",
            xaxis_title="Model",
            yaxis_title="MAE",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

    # R² comparison
    with col2:
        fig = go.Figure(data=[
            go.Bar(x=metrics_df['Model'], y=metrics_df['R²'], marker_color='purple')
        ])
        fig.update_layout(
            title="R² Score",
            xaxis_title="Model",
            yaxis_title="R²",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Model rankings
    st.subheader("🏆 Model Rankings")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Best RMSE", metrics_df.loc[metrics_df['RMSE'].idxmin(), 'Model'])
    with col2:
        st.metric("Best MAPE", metrics_df.loc[metrics_df['MAPE'].idxmin(), 'Model'])
    with col3:
        st.metric("Best R²", metrics_df.loc[metrics_df['R²'].idxmax(), 'Model'])

    st.markdown("---")

    # Key insights
    st.subheader("💡 Model Analysis")

    best_model = metrics_df.loc[metrics_df['RMSE'].idxmin()]
    worst_model = metrics_df.loc[metrics_df['RMSE'].idxmax()]

    st.markdown(f"""
    **Best Model (by RMSE)**: {best_model['Model']}
    - RMSE: {best_model['RMSE']:.4f}
    - MAPE: {best_model['MAPE']:.2f}%
    - R²: {best_model['R²']:.4f}

    **Baseline Model**: {worst_model['Model']}
    - RMSE: {worst_model['RMSE']:.4f}
    - MAPE: {worst_model['MAPE']:.2f}%
    - R²: {worst_model['R²']:.4f}

    **Improvement**:
    - RMSE reduced by {(1 - best_model['RMSE']/worst_model['RMSE'])*100:.1f}%
    - MAPE reduced by {(1 - best_model['MAPE']/worst_model['MAPE'])*100:.1f}%
    """)


if __name__ == "__main__":
    main()
