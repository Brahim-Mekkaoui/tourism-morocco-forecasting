"""
Metrics Calculation Module

Computes performance metrics for forecasting models.
- RMSE: Root Mean Squared Error
- MAE: Mean Absolute Error
- MAPE: Mean Absolute Percentage Error
- R²: Coefficient of Determination

Author: MEKKAOUI Brahim
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from src.logger import get_logger
from src.config import get_config

logger = get_logger(__name__)


class MetricsCalculator:
    """
    Calculate performance metrics for time series forecasts.

    Metrics:
    - RMSE: Root Mean Squared Error (penalizes large errors)
    - MAE: Mean Absolute Error (scale-dependent)
    - MAPE: Mean Absolute Percentage Error (scale-independent %)
    - R²: Coefficient of Determination (variance explained)
    """

    def __init__(self):
        """Initialize metrics calculator."""
        self.logger = logger
        self.config = get_config()

    @staticmethod
    def rmse(y_true: pd.Series, y_pred: pd.Series) -> float:
        """
        Calculate Root Mean Squared Error.

        RMSE = sqrt(mean((y_true - y_pred)²))

        Args:
            y_true: Actual values
            y_pred: Predicted values

        Returns:
            RMSE value
        """
        # Remove NaN values
        valid_idx = ~(y_true.isnull() | y_pred.isnull())
        y_t = y_true[valid_idx].values
        y_p = y_pred[valid_idx].values

        if len(y_t) == 0:
            return np.nan

        return np.sqrt(np.mean((y_t - y_p) ** 2))

    @staticmethod
    def mae(y_true: pd.Series, y_pred: pd.Series) -> float:
        """
        Calculate Mean Absolute Error.

        MAE = mean(|y_true - y_pred|)

        Args:
            y_true: Actual values
            y_pred: Predicted values

        Returns:
            MAE value
        """
        valid_idx = ~(y_true.isnull() | y_pred.isnull())
        y_t = y_true[valid_idx].values
        y_p = y_pred[valid_idx].values

        if len(y_t) == 0:
            return np.nan

        return np.mean(np.abs(y_t - y_p))

    @staticmethod
    def mape(y_true: pd.Series, y_pred: pd.Series) -> float:
        """
        Calculate Mean Absolute Percentage Error.

        MAPE = mean(|y_true - y_pred| / |y_true|) * 100

        Args:
            y_true: Actual values
            y_pred: Predicted values

        Returns:
            MAPE value (in percent)
        """
        valid_idx = ~(y_true.isnull() | y_pred.isnull())
        y_t = y_true[valid_idx].values
        y_p = y_pred[valid_idx].values

        if len(y_t) == 0:
            return np.nan

        # Avoid division by zero
        denominator = np.abs(y_t) + 1e-10
        return np.mean(np.abs((y_t - y_p) / denominator)) * 100

    @staticmethod
    def r2(y_true: pd.Series, y_pred: pd.Series) -> float:
        """
        Calculate R² (Coefficient of Determination).

        R² = 1 - (SS_res / SS_tot)

        Args:
            y_true: Actual values
            y_pred: Predicted values

        Returns:
            R² value (0-1, higher is better)
        """
        valid_idx = ~(y_true.isnull() | y_pred.isnull())
        y_t = y_true[valid_idx].values
        y_p = y_pred[valid_idx].values

        if len(y_t) == 0:
            return np.nan

        ss_res = np.sum((y_t - y_p) ** 2)
        ss_tot = np.sum((y_t - y_t.mean()) ** 2)

        if ss_tot == 0:
            return np.nan

        return 1 - (ss_res / ss_tot)

    def compute_all_metrics(
        self,
        y_true: pd.Series,
        y_pred: pd.Series,
        model_name: str = "Model"
    ) -> Dict[str, float]:
        """
        Compute all metrics at once.

        Args:
            y_true: Actual values
            y_pred: Predicted values
            model_name: Model name for logging

        Returns:
            Dictionary with all metrics
        """
        metrics = {
            'rmse': self.rmse(y_true, y_pred),
            'mae': self.mae(y_true, y_pred),
            'mape': self.mape(y_true, y_pred),
            'r2': self.r2(y_true, y_pred),
        }

        self.logger.info(
            f"{model_name} - RMSE: {metrics['rmse']:.4f}, "
            f"MAE: {metrics['mae']:.4f}, MAPE: {metrics['mape']:.2f}%, "
            f"R²: {metrics['r2']:.4f}"
        )

        return metrics

    def compute_normalized_metrics(
        self,
        y_true: pd.Series,
        y_pred: pd.Series,
        model_name: str = "Model"
    ) -> Dict[str, float]:
        """
        Compute normalized metrics (relative to baseline).

        Useful for comparing across different scales.

        Args:
            y_true: Actual values
            y_pred: Predicted values
            model_name: Model name for logging

        Returns:
            Dictionary with normalized metrics
        """
        # Normalize by standard deviation of actual values
        std_y = y_true.std()

        if std_y == 0:
            return {}

        metrics = {
            'rmse_normalized': self.rmse(y_true, y_pred) / std_y,
            'mae_normalized': self.mae(y_true, y_pred) / std_y,
            'mape': self.mape(y_true, y_pred),  # Already normalized
            'r2': self.r2(y_true, y_pred),
        }

        return metrics
