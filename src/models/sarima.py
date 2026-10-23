"""
SARIMA Model Module

Seasonal ARIMA (Autoregressive Integrated Moving Average) model.
Baseline model without exogenous variables.

Configuration: (1,1,1)(1,1,1,12)
- Order: (p=1, d=1, q=1)
- Seasonal order: (P=1, D=1, Q=1, s=12) where s=12 (monthly seasonality)

Author: MEKKAOUI Brahim
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from statsmodels.tsa.statespace.sarimax import SARIMAX
from src.logger import get_logger
from src.config import get_config
from src.utils import save_joblib, load_joblib

logger = get_logger(__name__)


class SARIMAModel:
    """
    Seasonal ARIMA (SARIMA) model for time series forecasting.

    Forecasts tourist arrivals without exogenous variables.
    Uses only historical arrivals data to make predictions.

    Attributes:
        order (tuple): ARIMA order (p, d, q)
        seasonal_order (tuple): Seasonal ARIMA order (P, D, Q, s)
        model: Fitted SARIMAX model instance
        results: Model fitting results
    """

    def __init__(
        self,
        order: Tuple[int, int, int] = (1, 1, 1),
        seasonal_order: Tuple[int, int, int, int] = (1, 1, 1, 12)
    ):
        """
        Initialize SARIMA model.

        Args:
            order: ARIMA order (p, d, q)
            seasonal_order: Seasonal ARIMA order (P, D, Q, s)
        """
        self.order = order
        self.seasonal_order = seasonal_order
        self.model = None
        self.results = None
        self.logger = logger
        self.config = get_config()

    def fit(
        self,
        y: pd.Series,
        **kwargs
    ) -> Dict:
        """
        Fit SARIMA model to time series data.

        Args:
            y: Time series data (1D)
            **kwargs: Additional arguments for SARIMAX.fit()

        Returns:
            Dictionary with model diagnostics
        """
        self.logger.info(
            f"Fitting SARIMA{self.order}{self.seasonal_order} on {len(y)} observations"
        )

        try:
            # Create model
            self.model = SARIMAX(
                y,
                order=self.order,
                seasonal_order=self.seasonal_order,
                enforce_stationarity=self.config.get(
                    'models.sarimax.enforce_stationarity', False
                ),
                enforce_invertibility=self.config.get(
                    'models.sarimax.enforce_invertibility', False
                )
            )

            # Fit model
            fit_kwargs = {
                'method_kwargs': {'maxiter': 200},
                'disp': False
            }
            fit_kwargs.update(kwargs)

            self.results = self.model.fit(**fit_kwargs)

            # Get diagnostics
            diagnostics = {
                'aic': self.results.aic,
                'bic': self.results.bic,
                'sses': self.results.sses,
                'sse': self.results.sse,
            }

            self.logger.info(f"Model fitted successfully. AIC={diagnostics['aic']:.2f}")

            return diagnostics

        except Exception as e:
            self.logger.error(f"Error fitting SARIMA model: {e}")
            raise

    def forecast(
        self,
        steps: int = 12,
        confidence_level: float = 0.95
    ) -> Tuple[pd.Series, pd.DataFrame]:
        """
        Generate forecast for future periods.

        Args:
            steps: Number of periods to forecast
            confidence_level: Confidence interval level (0.68 or 0.95)

        Returns:
            Tuple of (forecast series, confidence intervals DataFrame)

        Raises:
            ValueError: If model not fitted yet
        """
        if self.results is None:
            raise ValueError("Model not fitted yet. Call fit() first.")

        self.logger.info(f"Generating {steps}-step forecast")

        try:
            # Get forecast
            forecast_result = self.results.get_forecast(steps=steps)
            forecast = forecast_result.summary_frame(alpha=1-confidence_level)

            # Extract components
            forecast_values = forecast['mean']
            ci_lower = forecast['mean_ci_lower']
            ci_upper = forecast['mean_ci_upper']

            self.logger.info(f"Forecast generated: {forecast_values[-1]:.2f} (last value)")

            # Create confidence interval DataFrame
            ci_df = pd.DataFrame({
                'lower': ci_lower,
                'upper': ci_upper
            })

            return forecast_values, ci_df

        except Exception as e:
            self.logger.error(f"Error generating forecast: {e}")
            raise

    def get_residuals(self) -> pd.Series:
        """
        Get model residuals.

        Returns:
            Series of residuals

        Raises:
            ValueError: If model not fitted yet
        """
        if self.results is None:
            raise ValueError("Model not fitted yet. Call fit() first.")

        return self.results.resid

    def get_diagnostics(self) -> Dict:
        """
        Get model diagnostics.

        Returns:
            Dictionary with AIC, BIC, and other metrics
        """
        if self.results is None:
            raise ValueError("Model not fitted yet. Call fit() first.")

        return {
            'aic': self.results.aic,
            'bic': self.results.bic,
            'loglikelihood': self.results.llf,
            'nobs': self.results.nobs,
        }

    def summary(self) -> str:
        """
        Get model summary.

        Returns:
            String representation of model summary
        """
        if self.results is None:
            raise ValueError("Model not fitted yet. Call fit() first.")

        return str(self.results.summary())

    def save(self, filepath: str) -> None:
        """
        Save fitted model.

        Args:
            filepath: Path to save model
        """
        if self.results is None:
            raise ValueError("Model not fitted yet. Call fit() first.")

        self.logger.info(f"Saving SARIMA model to {filepath}")
        save_joblib(self.results, filepath)

    @staticmethod
    def load(filepath: str) -> 'SARIMAModel':
        """
        Load fitted model from file.

        Args:
            filepath: Path to saved model

        Returns:
            SARIMAModel instance with loaded results
        """
        logger.info(f"Loading SARIMA model from {filepath}")

        results = load_joblib(filepath)

        # Create model instance
        model = SARIMAModel()
        model.results = results

        return model
