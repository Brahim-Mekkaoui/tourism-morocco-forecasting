#!/usr/bin/env python
"""
Main Training Pipeline

Orchestrates the complete training workflow:
1. Load MANAR data
2. Load Google Trends data
3. Prepare and validate data
4. Engineer features (PCA, PLS)
5. Train models (SARIMA, SARIMAX+PCA, SARIMAX+PLS)
6. Select best model
7. Save models and results

Usage:
    python scripts/train.py

Author: MEKKAOUI Brahim
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Tuple

from src.config import get_config
from src.logger import get_logger
from src.data.loaders import DataLoader
from src.data.cleaners import DataCleaner
from src.data.validators import DataValidator
from src.features.google_trends import GoogleTrendsFeatures
from src.features.engineering import FeatureEngineer
from src.models.sarima import SARIMAModel
from src.models.sarimax import SARIMAXModel
from src.models.selector import ModelSelector
from src.evaluation.metrics import MetricsCalculator
from src.utils import (
    ensure_directory,
    time_series_split,
    save_csv,
    save_json
)

logger = get_logger(__name__)


def load_and_prepare_data() -> Tuple[pd.Series, pd.DataFrame]:
    """
    Load and prepare data from MANAR and Google Trends.

    Returns:
        Tuple of (target series, exogenous features DataFrame)
    """
    logger.info("=" * 80)
    logger.info("STEP 1: Loading Data")
    logger.info("=" * 80)

    config = get_config()

    # Load data
    data_loader = DataLoader()
    manar_data, google_trends = data_loader.load_all_data()

    logger.info(f"Loaded {len(manar_data)} MANAR datasets")
    logger.info(f"Google Trends shape: {google_trends.shape}")

    # Get arrivals as target
    arrivals = manar_data.get('arrivals_total')
    if arrivals is None:
        raise ValueError("Could not load arrivals data")

    # Clean data
    logger.info("\n" + "=" * 80)
    logger.info("STEP 2: Cleaning Data")
    logger.info("=" * 80)

    cleaner = DataCleaner()
    arrivals_clean = cleaner.clean_manar_data(arrivals, 'arrivals_total')
    google_trends_clean = cleaner.clean_google_trends_data(google_trends)

    logger.info(f"Cleaned arrivals shape: {arrivals_clean.shape}")
    logger.info(f"Cleaned Google Trends shape: {google_trends_clean.shape}")

    # Validate data
    logger.info("\n" + "=" * 80)
    logger.info("STEP 3: Validating Data Quality")
    logger.info("=" * 80)

    validator = DataValidator()

    # Convert arrivals to Series if DataFrame
    if isinstance(arrivals_clean, pd.DataFrame):
        arrivals_target = arrivals_clean.iloc[:, 0]
    else:
        arrivals_target = arrivals_clean

    validator.validate_temporal_data(
        arrivals_target.to_frame(),
        name="Arrivals",
        freq='MS'  # Month Start frequency
    )

    # Align by date
    logger.info("Aligning datasets by date...")

    # Ensure datetime index
    if not isinstance(arrivals_target.index, pd.DatetimeIndex):
        arrivals_target.index = pd.to_datetime(arrivals_target.index)

    if not isinstance(google_trends_clean.index, pd.DatetimeIndex):
        google_trends_clean.index = pd.to_datetime(google_trends_clean.index)

    # Get common date range
    common_start = max(arrivals_target.index.min(), google_trends_clean.index.min())
    common_end = min(arrivals_target.index.max(), google_trends_clean.index.max())

    arrivals_aligned = arrivals_target.loc[common_start:common_end]
    gt_aligned = google_trends_clean.loc[common_start:common_end]

    logger.info(f"Common date range: {common_start} to {common_end}")
    logger.info(f"Arrivals shape after alignment: {arrivals_aligned.shape}")
    logger.info(f"Google Trends shape after alignment: {gt_aligned.shape}")

    return arrivals_aligned, gt_aligned


def engineer_features(gt_data: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Engineer features using PCA and PLS.

    Args:
        gt_data: Google Trends DataFrame

    Returns:
        Tuple of (PCA features, PLS features)
    """
    logger.info("\n" + "=" * 80)
    logger.info("STEP 4: Feature Engineering")
    logger.info("=" * 80)

    # Initialize feature engineer
    feature_engineer = FeatureEngineer()

    logger.info("Applying PCA (53 terms → 3 components)...")
    gt_pca, pca_model = feature_engineer.apply_pca(gt_data, fit=True)
    logger.info(f"PCA features shape: {gt_pca.shape}")

    # For now, we'll need a target for PLS (will use in training)
    logger.info(f"Feature engineering complete")

    return gt_pca, feature_engineer


def train_models(
    y: pd.Series,
    X_pca: pd.DataFrame,
    feature_engineer: FeatureEngineer
) -> Tuple[Dict, ModelSelector]:
    """
    Train SARIMA and SARIMAX models.

    Args:
        y: Target variable (arrivals)
        X_pca: PCA features
        feature_engineer: Feature engineer instance

    Returns:
        Tuple of (models dict, model selector)
    """
    logger.info("\n" + "=" * 80)
    logger.info("STEP 5: Training Models")
    logger.info("=" * 80)

    config = get_config()
    metrics_calc = MetricsCalculator()

    # Split data
    train_size = config.get('models.train_test_split', 0.8)
    y_train, y_test = time_series_split(y.to_frame(), train_size)
    X_train = X_pca.loc[y_train.index]
    X_test = X_pca.loc[y_test.index]

    y_train = y_train.iloc[:, 0]
    y_test = y_test.iloc[:, 0]

    logger.info(f"Train set: {len(y_train)} observations")
    logger.info(f"Test set: {len(y_test)} observations")

    models_trained = {}
    model_selector = ModelSelector()

    # 1. SARIMA baseline
    logger.info("\nTraining SARIMA baseline...")
    try:
        sarima = SARIMAModel()
        sarima.fit(y_train)

        # Forecast
        y_pred_sarima, _ = sarima.forecast(steps=len(y_test))
        y_pred_sarima = y_pred_sarima.iloc[:len(y_test)]

        # Evaluate
        metrics = metrics_calc.compute_all_metrics(y_test, y_pred_sarima, "SARIMA")
        model_selector.register_model("SARIMA", sarima.results, "sarima")
        model_selector.compute_metrics(y_test, y_pred_sarima, "SARIMA")

        models_trained['sarima'] = sarima
        logger.info("SARIMA training complete")
    except Exception as e:
        logger.error(f"Error training SARIMA: {e}")

    # 2. SARIMAX + PCA
    logger.info("\nTraining SARIMAX + PCA...")
    try:
        sarimax_pca = SARIMAXModel(model_type='pca')
        sarimax_pca.fit(y_train, X_train)

        # Forecast
        y_pred_pca, _ = sarimax_pca.forecast(steps=len(y_test), exog_future=X_test)
        y_pred_pca = y_pred_pca.iloc[:len(y_test)]

        # Evaluate
        metrics = metrics_calc.compute_all_metrics(y_test, y_pred_pca, "SARIMAX+PCA")
        model_selector.register_model("SARIMAX+PCA", sarimax_pca.results, "sarimax_pca")
        model_selector.compute_metrics(y_test, y_pred_pca, "SARIMAX+PCA")

        models_trained['sarimax_pca'] = sarimax_pca
        logger.info("SARIMAX+PCA training complete")
    except Exception as e:
        logger.error(f"Error training SARIMAX+PCA: {e}")

    # 3. SARIMAX + PLS
    logger.info("\nTraining SARIMAX + PLS...")
    try:
        # Apply PLS with target
        X_pls, pls_model = feature_engineer.apply_pls(X_pca, y, fit=True)
        X_pls_train = X_pls.loc[y_train.index]
        X_pls_test = X_pls.loc[y_test.index]

        sarimax_pls = SARIMAXModel(model_type='pls')
        sarimax_pls.fit(y_train, X_pls_train)

        # Forecast
        y_pred_pls, _ = sarimax_pls.forecast(steps=len(y_test), exog_future=X_pls_test)
        y_pred_pls = y_pred_pls.iloc[:len(y_test)]

        # Evaluate
        metrics = metrics_calc.compute_all_metrics(y_test, y_pred_pls, "SARIMAX+PLS")
        model_selector.register_model("SARIMAX+PLS", sarimax_pls.results, "sarimax_pls")
        model_selector.compute_metrics(y_test, y_pred_pls, "SARIMAX+PLS")

        models_trained['sarimax_pls'] = sarimax_pls
        logger.info("SARIMAX+PLS training complete")
    except Exception as e:
        logger.error(f"Error training SARIMAX+PLS: {e}")

    return models_trained, model_selector


def main():
    """Main training pipeline."""
    logger.info("\n" + "=" * 80)
    logger.info("TOURISM MOROCCO FORECASTING PIPELINE")
    logger.info("=" * 80 + "\n")

    try:
        # Create output directories
        ensure_directory("models")
        ensure_directory("outputs")
        ensure_directory("logs")

        # Load and prepare data
        y, X_gt = load_and_prepare_data()

        # Engineer features
        X_pca, feature_engineer = engineer_features(X_gt)

        # Train models
        models, selector = train_models(y, X_pca, feature_engineer)

        # Select best model
        logger.info("\n" + "=" * 80)
        logger.info("STEP 6: Model Selection")
        logger.info("=" * 80)

        best_model_name, best_metrics = selector.select_best()
        logger.info(f"\n✓ Best Model: {best_model_name}")
        logger.info(f"  RMSE: {best_metrics['rmse']:.4f}")
        logger.info(f"  MAE: {best_metrics['mae']:.4f}")
        logger.info(f"  MAPE: {best_metrics['mape']:.2f}%")

        # Save models
        logger.info("\n" + "=" * 80)
        logger.info("STEP 7: Saving Models and Results")
        logger.info("=" * 80)

        for name, model in models.items():
            try:
                model.save(f"models/{name}_model.joblib")
            except Exception as e:
                logger.warning(f"Could not save {name}: {e}")

        # Save feature transformers
        feature_engineer.save_transformers("models")

        # Save selection results
        selection_summary = selector.summarize_selection()
        save_json(selection_summary, "outputs/model_selection_results.json")

        logger.info("\n" + "=" * 80)
        logger.info("✓ TRAINING PIPELINE COMPLETE")
        logger.info("=" * 80 + "\n")

        return True

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
