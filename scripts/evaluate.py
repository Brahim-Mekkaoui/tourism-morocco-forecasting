#!/usr/bin/env python
"""
Model Evaluation Script

Loads trained models and evaluates them on test data.
Generates comparison metrics and validation results.

Usage:
    python scripts/evaluate.py

Author: MEKKAOUI Brahim
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json

from src.config import get_config
from src.logger import get_logger
from src.data.loaders import DataLoader
from src.data.cleaners import DataCleaner
from src.data.validators import DataValidator
from src.features.google_trends import GoogleTrendsFeatures
from src.features.engineering import FeatureEngineer
from src.models.sarima import SARIMAModel
from src.models.sarimax import SARIMAXModel
from src.evaluation.metrics import MetricsCalculator
from src.evaluation.validation import TemporalValidator
from src.utils import save_csv, save_json, ensure_directory

logger = get_logger(__name__)


def main():
    """Evaluate all trained models."""
    logger.info("=" * 80)
    logger.info("MODEL EVALUATION")
    logger.info("=" * 80)

    config = get_config()
    ensure_directory("outputs")

    try:
        # Load data
        logger.info("\nLoading data...")
        data_loader = DataLoader()
        manar_data, google_trends = data_loader.load_all_data()

        arrivals = manar_data.get('arrivals_total')
        if arrivals is None:
            raise ValueError("Could not load arrivals")

        # Clean data
        cleaner = DataCleaner()
        arrivals_clean = cleaner.clean_manar_data(arrivals, 'arrivals_total')
        google_trends_clean = cleaner.clean_google_trends_data(google_trends)

        # Convert and align
        if isinstance(arrivals_clean, pd.DataFrame):
            arrivals_target = arrivals_clean.iloc[:, 0]
        else:
            arrivals_target = arrivals_clean

        if not isinstance(arrivals_target.index, pd.DatetimeIndex):
            arrivals_target.index = pd.to_datetime(arrivals_target.index)

        if not isinstance(google_trends_clean.index, pd.DatetimeIndex):
            google_trends_clean.index = pd.to_datetime(google_trends_clean.index)

        common_start = max(arrivals_target.index.min(), google_trends_clean.index.min())
        common_end = min(arrivals_target.index.max(), google_trends_clean.index.max())

        arrivals_aligned = arrivals_target.loc[common_start:common_end]
        gt_aligned = google_trends_clean.loc[common_start:common_end]

        logger.info(f"Data loaded: {len(arrivals_aligned)} observations")

        # Engineer features
        logger.info("\nEngineering features...")
        gt_features = GoogleTrendsFeatures()
        X_pca, pca_model = FeatureEngineer().apply_pca(gt_aligned, fit=True)

        # Split data
        logger.info("\nSplitting data...")
        split_idx = int(len(arrivals_aligned) * 0.8)
        y_train = arrivals_aligned.iloc[:split_idx]
        y_test = arrivals_aligned.iloc[split_idx:]
        X_train = X_pca.iloc[:split_idx]
        X_test = X_pca.iloc[split_idx:]

        logger.info(f"Train: {len(y_train)}, Test: {len(y_test)}")

        # Evaluate models
        metrics_calc = MetricsCalculator()
        results = {}

        logger.info("\n" + "=" * 80)
        logger.info("EVALUATING MODELS")
        logger.info("=" * 80)

        # SARIMA
        logger.info("\nSARIMA Evaluation...")
        try:
            sarima = SARIMAModel()
            sarima.fit(y_train)
            y_pred_sarima, _ = sarima.forecast(steps=len(y_test))
            y_pred_sarima = y_pred_sarima.iloc[:len(y_test)]

            metrics = metrics_calc.compute_all_metrics(y_test, y_pred_sarima, "SARIMA")
            results['SARIMA'] = metrics
            logger.info(f"  RMSE: {metrics['rmse']:.4f}, MAE: {metrics['mae']:.4f}, MAPE: {metrics['mape']:.2f}%")
        except Exception as e:
            logger.error(f"SARIMA evaluation failed: {e}")

        # SARIMAX+PCA
        logger.info("\nSARIMAX+PCA Evaluation...")
        try:
            sarimax_pca = SARIMAXModel(model_type='pca')
            sarimax_pca.fit(y_train, X_train)
            y_pred_pca, _ = sarimax_pca.forecast(steps=len(y_test), exog_future=X_test)
            y_pred_pca = y_pred_pca.iloc[:len(y_test)]

            metrics = metrics_calc.compute_all_metrics(y_test, y_pred_pca, "SARIMAX+PCA")
            results['SARIMAX+PCA'] = metrics
            logger.info(f"  RMSE: {metrics['rmse']:.4f}, MAE: {metrics['mae']:.4f}, MAPE: {metrics['mape']:.2f}%")
        except Exception as e:
            logger.error(f"SARIMAX+PCA evaluation failed: {e}")

        # SARIMAX+PLS
        logger.info("\nSARIMAX+PLS Evaluation...")
        try:
            fe = FeatureEngineer()
            X_pls, pls_model = fe.apply_pls(X_pca, arrivals_aligned, fit=True)
            X_pls_train = X_pls.iloc[:split_idx]
            X_pls_test = X_pls.iloc[split_idx:]

            sarimax_pls = SARIMAXModel(model_type='pls')
            sarimax_pls.fit(y_train, X_pls_train)
            y_pred_pls, _ = sarimax_pls.forecast(steps=len(y_test), exog_future=X_pls_test)
            y_pred_pls = y_pred_pls.iloc[:len(y_test)]

            metrics = metrics_calc.compute_all_metrics(y_test, y_pred_pls, "SARIMAX+PLS")
            results['SARIMAX+PLS'] = metrics
            logger.info(f"  RMSE: {metrics['rmse']:.4f}, MAE: {metrics['mae']:.4f}, MAPE: {metrics['mape']:.2f}%")
        except Exception as e:
            logger.error(f"SARIMAX+PLS evaluation failed: {e}")

        # Save results
        logger.info("\n" + "=" * 80)
        logger.info("SAVING RESULTS")
        logger.info("=" * 80)

        results_df = pd.DataFrame(results).T
        save_csv(results_df, "outputs/model_evaluation_results.csv")
        save_json({k: v for k, v in results.items()}, "outputs/model_evaluation.json")

        logger.info(f"\n✓ Results saved to outputs/")
        logger.info("\nModel Comparison:")
        logger.info(results_df)

        return True

    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
