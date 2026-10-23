#!/usr/bin/env python
"""
Forecasting Script

Generate forecasts using trained models for multiple horizons.
Produces both point forecasts and confidence intervals.

Usage:
    python scripts/forecast.py --horizon 12 --output outputs/forecast.csv

Author: MEKKAOUI Brahim
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
import argparse

from src.config import get_config
from src.logger import get_logger
from src.data.loaders import DataLoader
from src.data.cleaners import DataCleaner
from src.features.engineering import FeatureEngineer
from src.models.sarima import SARIMAModel
from src.models.sarimax import SARIMAXModel
from src.forecasting.engine import ForecastEngine
from src.visualization.plots import PlotGenerator
from src.utils import save_csv, save_json, ensure_directory

logger = get_logger(__name__)


def load_latest_data():
    """Load and prepare latest data for forecasting."""
    logger.info("Loading latest data...")

    data_loader = DataLoader()
    manar_data, google_trends = data_loader.load_all_data()

    arrivals = manar_data.get('arrivals_total')
    if arrivals is None:
        raise ValueError("Could not load arrivals data")

    cleaner = DataCleaner()
    arrivals_clean = cleaner.clean_manar_data(arrivals, 'arrivals_total')
    google_trends_clean = cleaner.clean_google_trends_data(google_trends)

    # Convert to Series
    if isinstance(arrivals_clean, pd.DataFrame):
        arrivals_target = arrivals_clean.iloc[:, 0]
    else:
        arrivals_target = arrivals_clean

    # Ensure datetime index
    if not isinstance(arrivals_target.index, pd.DatetimeIndex):
        arrivals_target.index = pd.to_datetime(arrivals_target.index)

    if not isinstance(google_trends_clean.index, pd.DatetimeIndex):
        google_trends_clean.index = pd.to_datetime(google_trends_clean.index)

    # Align by date
    common_start = max(arrivals_target.index.min(), google_trends_clean.index.min())
    common_end = min(arrivals_target.index.max(), google_trends_clean.index.max())

    arrivals_aligned = arrivals_target.loc[common_start:common_end]
    gt_aligned = google_trends_clean.loc[common_start:common_end]

    logger.info(f"Data loaded: {len(arrivals_aligned)} observations")
    logger.info(f"Data range: {arrivals_aligned.index.min()} to {arrivals_aligned.index.max()}")

    return arrivals_aligned, gt_aligned


def generate_forecasts(y, X_gt, horizons=[1, 3, 6, 12], output_dir="outputs"):
    """
    Generate forecasts for multiple horizons.

    Args:
        y: Target variable (arrivals)
        X_gt: Google Trends features
        horizons: List of forecast horizons (months)
        output_dir: Directory to save results
    """
    logger.info("=" * 80)
    logger.info("FORECASTING")
    logger.info("=" * 80)

    ensure_directory(output_dir)

    # Load trained models
    logger.info("\nLoading trained models...")
    try:
        # Try to load SARIMAX+PCA (best model)
        best_model = SARIMAXModel(model_type='pca')
        best_model.load("models/sarimax_pca_model.joblib")
        model_name = "SARIMAX+PCA"
        logger.info(f"✓ Loaded {model_name}")
    except Exception as e:
        logger.warning(f"Could not load SARIMAX+PCA: {e}")
        try:
            best_model = SARIMAModel()
            best_model.load("models/sarima_model.joblib")
            model_name = "SARIMA"
            logger.info(f"✓ Loaded {model_name}")
        except Exception as e:
            logger.error(f"Could not load any model: {e}")
            return False

    # Load feature transformers for SARIMAX
    feature_engineer = FeatureEngineer()
    try:
        feature_engineer.load_transformers("models")
        logger.info("✓ Loaded feature transformers")
    except Exception as e:
        logger.warning(f"Could not load feature transformers: {e}")

    # Generate forecasts for each horizon
    results = {}

    for horizon in horizons:
        logger.info(f"\nGenerating {horizon}-month forecast...")

        try:
            if model_name == "SARIMAX+PCA":
                # Need exogenous features
                X_pca, _ = feature_engineer.apply_pca(X_gt, fit=False)

                # Use last available exogenous features
                X_future = pd.DataFrame(
                    np.repeat(X_pca.iloc[-1:].values, horizon, axis=0),
                    index=pd.date_range(start=X_pca.index[-1] + pd.DateOffset(months=1), periods=horizon, freq='MS'),
                    columns=X_pca.columns
                )

                forecast, conf_int = best_model.forecast(steps=horizon, exog_future=X_future)
            else:
                # SARIMA without exogenous variables
                forecast, conf_int = best_model.forecast(steps=horizon)

            # Store results
            results[horizon] = {
                'forecast': forecast.values.flatten().tolist(),
                'lower_ci': conf_int[:, 0].flatten().tolist(),
                'upper_ci': conf_int[:, 1].flatten().tolist(),
                'index': forecast.index.strftime('%Y-%m-%d').tolist()
            }

            logger.info(f"  ✓ Forecast generated")
            logger.info(f"    Mean: {forecast.mean():.2f}")
            logger.info(f"    Min: {forecast.min():.2f}, Max: {forecast.max():.2f}")

        except Exception as e:
            logger.error(f"  ✗ Error generating {horizon}-month forecast: {e}")

    # Save results
    logger.info("\nSaving results...")

    # Save to JSON
    save_json(results, f"{output_dir}/forecasts.json")
    logger.info(f"✓ Forecasts saved to {output_dir}/forecasts.json")

    # Create summary table
    forecast_summary = []
    for horizon, data in results.items():
        forecast_summary.append({
            'Horizon (Months)': horizon,
            'Mean Forecast': np.mean(data['forecast']),
            'Min Forecast': np.min(data['forecast']),
            'Max Forecast': np.max(data['forecast']),
            'Lower CI (95%)': np.mean(data['lower_ci']),
            'Upper CI (95%)': np.mean(data['upper_ci'])
        })

    forecast_df = pd.DataFrame(forecast_summary)
    save_csv(forecast_df, f"{output_dir}/forecast_summary.csv")
    logger.info(f"✓ Summary saved to {output_dir}/forecast_summary.csv")

    # Create visualization
    logger.info("\nGenerating visualizations...")
    try:
        plotter = PlotGenerator()

        # Plot each horizon
        for horizon in horizons:
            if horizon in results:
                data = results[horizon]

                forecast_series = pd.Series(
                    data['forecast'],
                    index=pd.to_datetime(data['index'])
                )
                ci_lower = pd.Series(
                    data['lower_ci'],
                    index=pd.to_datetime(data['index'])
                )
                ci_upper = pd.Series(
                    data['upper_ci'],
                    index=pd.to_datetime(data['index'])
                )

                # Create visualization with historical data
                fig = plotter.plot_forecast(
                    actual=y.tail(12),  # Last 12 months for context
                    forecast=forecast_series,
                    ci_lower=ci_lower,
                    ci_upper=ci_upper,
                    title=f"{model_name} - {horizon}-Month Forecast"
                )

                plotter.save_figure(fig, f"{output_dir}/forecast_{horizon}m.png")

        logger.info("✓ Visualizations saved")
    except Exception as e:
        logger.warning(f"Could not generate visualizations: {e}")

    logger.info("\n" + "=" * 80)
    logger.info("✓ FORECASTING COMPLETE")
    logger.info("=" * 80)

    return True


def main():
    """Main forecasting pipeline."""
    parser = argparse.ArgumentParser(description='Generate forecasts using trained models')
    parser.add_argument('--horizon', type=int, default=12, help='Forecast horizon in months')
    parser.add_argument('--horizons', type=int, nargs='+', help='Multiple forecast horizons')
    parser.add_argument('--output', type=str, default='outputs', help='Output directory')

    args = parser.parse_args()

    horizons = args.horizons if args.horizons else [args.horizon]

    logger.info("\n" + "=" * 80)
    logger.info("TOURISM MOROCCO FORECASTING")
    logger.info("=" * 80 + "\n")

    try:
        # Load data
        y, X_gt = load_latest_data()

        # Generate forecasts
        success = generate_forecasts(y, X_gt, horizons=horizons, output_dir=args.output)

        return success

    except Exception as e:
        logger.error(f"Forecasting failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
