"""
Temporal Validation Module

Proper temporal validation for time series models.
Prevents data leakage by using rolling window and walk-forward validation.

Methods:
- Rolling Window: Fixed-size test windows
- Walk-Forward: Expanding training window

Author: MEKKAOUI Brahim
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from src.logger import get_logger
from src.config import get_config
from src.evaluation.metrics import MetricsCalculator

logger = get_logger(__name__)


class TemporalValidator:
    """
    Temporal validation for time series forecasting models.

    Prevents temporal data leakage by properly splitting data
    respecting the time dimension.

    Methods:
    - Rolling Window: Test on fixed-size windows with fixed train size
    - Walk-Forward: Test on expanding windows (train grows over time)
    """

    def __init__(self):
        """Initialize temporal validator."""
        self.config = get_config()
        self.logger = logger
        self.metrics_calc = MetricsCalculator()
        self.validation_results = {}

    def rolling_window_validation(
        self,
        df: pd.DataFrame,
        target_column: str,
        model_func,
        window_size: int = 12,
        step_size: int = 1,
        min_train_size: int = 24
    ) -> Dict:
        """
        Perform rolling window temporal validation.

        Test windows slide forward with fixed train/test size.
        Prevents look-ahead bias.

        Args:
            df: DataFrame with datetime index
            target_column: Name of target column
            model_func: Function that takes (y_train, X_train, y_test, X_test)
                       and returns (y_pred, model_info)
            window_size: Size of test window
            step_size: Step between test windows
            min_train_size: Minimum training set size

        Returns:
            Dictionary with validation results
        """
        self.logger.info(
            f"Rolling window validation: window_size={window_size}, "
            f"step_size={step_size}, min_train_size={min_train_size}"
        )

        if len(df) < min_train_size + window_size:
            raise ValueError(
                f"Dataset too small ({len(df)}) for validation "
                f"(need {min_train_size + window_size})"
            )

        results = {
            'predictions': [],
            'actuals': [],
            'metrics_per_window': [],
            'dates': []
        }

        window_count = 0
        for i in range(min_train_size, len(df) - window_size, step_size):
            # Split data
            train_df = df.iloc[:i].copy()
            test_df = df.iloc[i:i + window_size].copy()

            y_train = train_df[target_column]
            y_test = test_df[target_column]

            # Get exogenous variables if available
            X_train = train_df.drop(target_column, axis=1)
            X_test = test_df.drop(target_column, axis=1)

            try:
                # Train and predict
                y_pred, info = model_func(y_train, X_train, y_test, X_test)

                # Store results
                results['predictions'].extend(y_pred)
                results['actuals'].extend(y_test.values)
                results['dates'].extend(test_df.index)

                # Calculate metrics for this window
                window_metrics = self.metrics_calc.compute_all_metrics(
                    y_test, pd.Series(y_pred, index=y_test.index),
                    f"Window {window_count}"
                )
                results['metrics_per_window'].append(window_metrics)

                window_count += 1

            except Exception as e:
                self.logger.warning(f"Error in window {i}: {e}")
                continue

        # Aggregate metrics across windows
        results['mean_metrics'] = self._aggregate_metrics(results['metrics_per_window'])
        results['window_count'] = window_count

        self.validation_results['rolling_window'] = results

        self.logger.info(f"Rolling window validation complete: {window_count} windows")

        return results

    def walk_forward_validation(
        self,
        df: pd.DataFrame,
        target_column: str,
        model_func,
        initial_train_size: int = 24,
        step_size: int = 1,
        test_size: int = 1
    ) -> Dict:
        """
        Perform walk-forward temporal validation.

        Training window expands over time, test window slides forward.
        More realistic for online learning scenarios.

        Args:
            df: DataFrame with datetime index
            target_column: Name of target column
            model_func: Function that takes (y_train, X_train, y_test, X_test)
                       and returns (y_pred, model_info)
            initial_train_size: Initial training set size
            step_size: Step size for rolling
            test_size: Test window size

        Returns:
            Dictionary with validation results
        """
        self.logger.info(
            f"Walk-forward validation: initial_train_size={initial_train_size}, "
            f"test_size={test_size}"
        )

        if len(df) < initial_train_size + test_size:
            raise ValueError(
                f"Dataset too small ({len(df)}) for validation "
                f"(need {initial_train_size + test_size})"
            )

        results = {
            'predictions': [],
            'actuals': [],
            'metrics_per_step': [],
            'dates': []
        }

        step_count = 0
        for i in range(initial_train_size, len(df) - test_size + 1, step_size):
            # Split data (expanding window)
            train_df = df.iloc[:i].copy()
            test_df = df.iloc[i:i + test_size].copy()

            y_train = train_df[target_column]
            y_test = test_df[target_column]

            # Get exogenous variables if available
            X_train = train_df.drop(target_column, axis=1)
            X_test = test_df.drop(target_column, axis=1)

            try:
                # Train and predict
                y_pred, info = model_func(y_train, X_train, y_test, X_test)

                # Store results
                results['predictions'].extend(y_pred)
                results['actuals'].extend(y_test.values)
                results['dates'].extend(test_df.index)

                # Calculate metrics
                step_metrics = self.metrics_calc.compute_all_metrics(
                    y_test, pd.Series(y_pred, index=y_test.index),
                    f"Step {step_count}"
                )
                results['metrics_per_step'].append(step_metrics)

                step_count += 1

            except Exception as e:
                self.logger.warning(f"Error at step {i}: {e}")
                continue

        # Aggregate metrics
        results['mean_metrics'] = self._aggregate_metrics(results['metrics_per_step'])
        results['step_count'] = step_count

        self.validation_results['walk_forward'] = results

        self.logger.info(f"Walk-forward validation complete: {step_count} steps")

        return results

    @staticmethod
    def _aggregate_metrics(metrics_list: List[Dict]) -> Dict:
        """
        Aggregate metrics across multiple validation steps.

        Args:
            metrics_list: List of metric dictionaries

        Returns:
            Dictionary with mean and std of metrics
        """
        if not metrics_list:
            return {}

        metrics_df = pd.DataFrame(metrics_list)

        aggregated = {
            'mean': metrics_df.mean().to_dict(),
            'std': metrics_df.std().to_dict(),
            'min': metrics_df.min().to_dict(),
            'max': metrics_df.max().to_dict(),
        }

        return aggregated

    def get_validation_report(self, method: str = 'rolling_window') -> Dict:
        """
        Get validation report.

        Args:
            method: 'rolling_window' or 'walk_forward'

        Returns:
            Validation results dictionary
        """
        if method not in self.validation_results:
            raise ValueError(f"No validation results for method: {method}")

        results = self.validation_results[method]

        report = {
            'method': method,
            'num_tests': len(results['predictions']),
            'mean_metrics': results['mean_metrics'],
        }

        return report
