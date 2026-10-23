"""
Model Selector Module

Automatic model selection based on performance metrics.
Compares SARIMA, SARIMAX+PCA, and SARIMAX+PLS models.

Selection criteria (in order of priority):
1. RMSE (lower is better)
2. MAE (lower is better)
3. MAPE (lower is better)

Author: MEKKAOUI Brahim
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from src.logger import get_logger
from src.config import get_config

logger = get_logger(__name__)


class ModelSelector:
    """
    Automatic model selection from multiple candidates.

    Evaluates SARIMA, SARIMAX+PCA, and SARIMAX+PLS models
    and selects the best one based on specified metrics.

    Attributes:
        models (Dict): Dictionary of model names to results
        metrics (Dict): Computed metrics for each model
        best_model (str): Name of best performing model
        selection_criteria (List): Order of metric priority
    """

    def __init__(
        self,
        selection_criteria: Optional[List[str]] = None
    ):
        """
        Initialize model selector.

        Args:
            selection_criteria: List of metrics for selection priority.
                               Default: ['rmse', 'mae', 'mape']
        """
        self.models = {}
        self.metrics = {}
        self.best_model = None
        self.logger = logger
        self.config = get_config()

        if selection_criteria is None:
            selection_criteria = ['rmse', 'mae', 'mape']

        self.selection_criteria = selection_criteria

    def register_model(
        self,
        name: str,
        model_results: any,
        model_type: str = 'sarima'
    ) -> None:
        """
        Register a model for comparison.

        Args:
            name: Model identifier (e.g., 'SARIMA', 'SARIMAX+PCA', 'SARIMAX+PLS')
            model_results: Fitted model results object
            model_type: Type of model for reference
        """
        self.models[name] = {
            'results': model_results,
            'type': model_type
        }
        self.logger.info(f"Registered model: {name} ({model_type})")

    def compute_metrics(
        self,
        y_true: pd.Series,
        y_pred: pd.Series,
        model_name: str
    ) -> Dict[str, float]:
        """
        Compute performance metrics for a model.

        Args:
            y_true: Actual values
            y_pred: Predicted values
            model_name: Name of model

        Returns:
            Dictionary with computed metrics
        """
        # Remove NaN values
        valid_idx = ~(y_true.isnull() | y_pred.isnull())
        y_t = y_true[valid_idx]
        y_p = y_pred[valid_idx]

        if len(y_t) == 0:
            self.logger.error(f"No valid values for {model_name}")
            return {}

        # Calculate metrics
        residuals = y_t - y_p

        # RMSE (Root Mean Squared Error)
        rmse = np.sqrt(np.mean(residuals ** 2))

        # MAE (Mean Absolute Error)
        mae = np.mean(np.abs(residuals))

        # MAPE (Mean Absolute Percentage Error)
        # Avoid division by zero
        mape = np.mean(np.abs((y_t - y_p) / (np.abs(y_t) + 1e-10))) * 100

        # R-squared
        ss_res = np.sum(residuals ** 2)
        ss_tot = np.sum((y_t - y_t.mean()) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

        metrics = {
            'rmse': rmse,
            'mae': mae,
            'mape': mape,
            'r2': r2,
            'n': len(y_t)
        }

        self.metrics[model_name] = metrics

        self.logger.info(
            f"{model_name} metrics - RMSE: {rmse:.4f}, MAE: {mae:.4f}, "
            f"MAPE: {mape:.2f}%, R²: {r2:.4f}"
        )

        return metrics

    def select_best(self) -> Tuple[str, Dict]:
        """
        Select the best model based on selection criteria.

        Returns:
            Tuple of (best model name, its metrics)

        Raises:
            ValueError: If no models registered or metrics not computed
        """
        if not self.metrics:
            raise ValueError(
                "No metrics computed. Register models and compute metrics first."
            )

        self.logger.info(f"Selecting best model using criteria: {self.selection_criteria}")

        # Convert metrics to DataFrame for easier comparison
        metrics_df = pd.DataFrame(self.metrics).T

        # Score each model
        scores = pd.DataFrame(index=metrics_df.index)

        for i, criterion in enumerate(self.selection_criteria):
            if criterion not in metrics_df.columns:
                self.logger.warning(f"Criterion {criterion} not found in metrics")
                continue

            # Rank models (lower is better for rmse/mae/mape)
            if criterion.lower() in ['rmse', 'mae', 'mape']:
                ranks = metrics_df[criterion].rank()
            else:  # r2: higher is better
                ranks = metrics_df[criterion].rank(ascending=False)

            scores[f'{criterion}_rank'] = ranks

        # Calculate total rank
        total_ranks = scores.sum(axis=1)
        best_model_name = total_ranks.idxmin()

        self.best_model = best_model_name

        self.logger.info(f"Best model selected: {best_model_name}")
        self.logger.info(f"Ranking:\n{total_ranks.sort_values()}")

        return best_model_name, self.metrics[best_model_name]

    def get_model_comparison(self) -> pd.DataFrame:
        """
        Get comparison table of all models.

        Returns:
            DataFrame with metrics for all registered models
        """
        if not self.metrics:
            self.logger.warning("No metrics computed yet")
            return pd.DataFrame()

        comparison_df = pd.DataFrame(self.metrics).T

        # Sort by RMSE if available
        if 'rmse' in comparison_df.columns:
            comparison_df = comparison_df.sort_values('rmse')

        self.logger.info(f"Model Comparison:\n{comparison_df}")

        return comparison_df

    def summarize_selection(self) -> Dict:
        """
        Summarize model selection results.

        Returns:
            Dictionary with selection summary
        """
        if self.best_model is None:
            raise ValueError("No best model selected yet. Call select_best() first.")

        comparison = self.get_model_comparison()
        best_metrics = self.metrics[self.best_model]

        summary = {
            'best_model': self.best_model,
            'metrics': best_metrics,
            'all_models': list(self.models.keys()),
            'comparison': comparison.to_dict(),
            'selection_criteria': self.selection_criteria
        }

        self.logger.info(
            f"Selection Summary:\n"
            f"Best Model: {self.best_model}\n"
            f"Metrics: {best_metrics}"
        )

        return summary
