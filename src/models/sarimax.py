"""
SARIMAX Model Module

Seasonal ARIMA with eXogenous variables (SARIMAX) model.
Uses Google Trends data as exogenous variables to improve forecasts.

Supports both PCA-reduced and PLS-reduced Google Trends data.

Configuration: (1,1,1)(1,1,1,12)
- Order: (p=1, d=1, q=1)
- Seasonal order: (P=1, D=1, Q=1, s=12)
- Exogenous variables: PCA components or PLS components from Google Trends

Author: MEKKAOUI Brahim
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
from statsmodels.tsa.statespace.sarimax import SARIMAX
from src.logger import get_logger
from src.config import get_config
from src.utils import save_joblib, load_joblib

logger = get_logger(__name__)


class SARIMAXModel:
    """
    SARIMA with eXogenous variables (SARIMAX) model.

    Incorporates exogenous variables (Google Trends data) to improve
    tourist arrival forecasts.

    Supports two configurations:
    1. SARIMAX + PCA: Uses PCA-reduced Google Trends features
    2. SARIMAX + PLS: Uses PLS-reduced Google Trends features

    Attributes:
        order (tuple): ARIMA order (p, d, q)
        seasonal_order (tuple): Seasonal ARIMA order (P, D, Q, s)
        model_type (str): 'pca' or 'pls'
        model: Fitted SARIMAX model instance
        results: Model fitting results
    """

    def __init__(
        self,
        order: Tuple[int, int, int] = (1, 1, 1),
        seasonal_order: Tuple[int, int, int, int] = (1, 1, 1, 12),
        model_type: str = 'pca'
    ):
        """
        Initialize SARIMAX model.

        Args:
            order: ARIMA order (p, d, q)
            seasonal_order: Seasonal ARIMA order (P, D, Q, s)
            model_type: 'pca' or 'pls' for exogenous variable type
        """
        self.order = order
        self.seasonal_order = seasonal_order
        self.model_type = model_type
        self.model = None
        self.results = None
        self.logger = logger
        self.config = get_config()

        if model_type not in ['pca', 'pls']:
            raise ValueError(f"Invalid model_type: {model_type}. Must be 'pca' or 'pls'")

    def fit(
        self,
        y: pd.Series,
        X: pd.DataFrame,
        **kwargs
    ) -> Dict:
        """
        Fit SARIMAX model with exogenous variables.

        Args:
            y: Target time series (tourist arrivals)
            X: Exogenous variables DataFrame (PCA/PLS components)
            **kwargs: Additional arguments for SARIMAX.fit()

        Returns:
            Dictionary with model diagnostics

        Raises:
            ValueError: If data shapes don't match
        """
        if len(y) != len(X):
            raise ValueError(
                f"Target and exogenous variables have different lengths: "
                f"{len(y)} vs {len(X)}"
            )

        self.logger.info(
            f"Fitting SARIMAX{self.order}{self.seasonal_order} "
            f"with {self.model_type.upper()} exogenous variables "
            f"({X.shape[1]} features) on {len(y)} observations"
        )

        try:
            # Create model with exogenous variables
            self.model = SARIMAX(
                y,
                exog=X,
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

            self.logger.info(
                f"Model fitted successfully. AIC={diagnostics['aic']:.2f}, "
                f"BIC={diagnostics['bic']:.2f}"
            )

            return diagnostics

        except Exception as e:
            self.logger.error(f"Error fitting SARIMAX model: {e}")
            raise

    def forecast(
        self,
        steps: int = 12,
        exog_future: Optional[pd.DataFrame] = None,
        confidence_level: float = 0.95
    ) -> Tuple[pd.Series, pd.DataFrame]:
        """
        Generate forecast for future periods.

        Args:
            steps: Number of periods to forecast
            exog_future: Future exogenous variables (required for SARIMAX)
            confidence_level: Confidence interval level (0.68 or 0.95)

        Returns:
            Tuple of (forecast series, confidence intervals DataFrame)

        Raises:
            ValueError: If model not fitted or exogenous data missing
        """
        if self.results is None:
            raise ValueError("Model not fitted yet. Call fit() first.")

        if exog_future is None:
            raise ValueError(
                "Future exogenous variables required for SARIMAX forecasting. "
                "Provide exog_future parameter."
            )

        if len(exog_future) != steps:
            raise ValueError(
                f"exog_future has {len(exog_future)} rows but {steps} steps requested"
            )

        self.logger.info(
            f"Generating {steps}-step forecast with SARIMAX+{self.model_type.upper()}"
        )

        try:
            # Get forecast
            forecast_result = self.results.get_forecast(
                steps=steps,
                exog=exog_future
            )
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

        self.logger.info(f"Saving SARIMAX+{self.model_type.upper()} model to {filepath}")
        save_joblib(self.results, filepath)

    @staticmethod
    def load(filepath: str, model_type: str = 'pca') -> 'SARIMAXModel':
        """
        Load fitted model from file.

        Args:
            filepath: Path to saved model
            model_type: 'pca' or 'pls'

        Returns:
            SARIMAXModel instance with loaded results
        """
        logger.info(f"Loading SARIMAX+{model_type.upper()} model from {filepath}")

        results = load_joblib(filepath)

        # Create model instance
        model = SARIMAXModel(model_type=model_type)
        model.results = results

        return model
