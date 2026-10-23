"""
Forecast Engine Module

Orchestrates forecasting across different horizons.
Generates predictions with confidence intervals for multiple timeframes.

Author: MEKKAOUI Brahim
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from src.logger import get_logger
from src.config import get_config

logger = get_logger(__name__)


class ForecastEngine:
    """
    Main forecasting engine.

    Generates predictions using fitted models.
    Supports multiple forecast horizons with confidence intervals.

    Attributes:
        model: Fitted forecasting model
        config: Configuration instance
    """

    def __init__(self, model):
        """
        Initialize forecast engine with a fitted model.

        Args:
            model: Fitted SARIMA or SARIMAX model instance
        """
        self.model = model
        self.config = get_config()
        self.logger = logger
        self.forecasts = {}

    def forecast_horizons(
        self,
        horizons: Optional[List[int]] = None,
        exog_future: Optional[pd.DataFrame] = None
    ) -> Dict[int, Tuple[pd.Series, pd.DataFrame]]:
        """
        Generate forecasts for multiple horizons.

        Args:
            horizons: List of forecast horizons (default from config)
            exog_future: Future exogenous variables (for SARIMAX)

        Returns:
            Dictionary mapping horizons to (forecast, confidence intervals)
        """
        if horizons is None:
            horizons = self.config.get('forecasting.horizons', [1, 3, 6, 12])

        self.logger.info(f"Generating forecasts for horizons: {horizons}")

        forecasts = {}

        for horizon in horizons:
            try:
                # Prepare exogenous data for this horizon if needed
                exog_h = None
                if exog_future is not None:
                    if len(exog_future) >= horizon:
                        exog_h = exog_future.iloc[:horizon]
                    else:
                        self.logger.warning(
                            f"Insufficient exogenous data for horizon {horizon}"
                        )

                # Generate forecast
                forecast, ci = self.model.forecast(
                    steps=horizon,
                    exog_future=exog_h if exog_h is not None else None
                )

                forecasts[horizon] = (forecast, ci)

                self.logger.info(
                    f"Forecast for {horizon} months: {forecast.iloc[-1]:.2f}"
                )

            except Exception as e:
                self.logger.error(f"Error forecasting {horizon} months: {e}")
                continue

        self.forecasts = forecasts
        return forecasts

    def get_forecast_table(
        self,
        horizons: Optional[List[int]] = None,
        confidence_level: float = 0.95
    ) -> pd.DataFrame:
        """
        Get forecast summary as a table.

        Args:
            horizons: Forecast horizons to include
            confidence_level: Confidence interval level

        Returns:
            DataFrame with forecast values and intervals
        """
        if horizons is None:
            horizons = list(self.forecasts.keys())

        forecast_data = []

        for horizon in horizons:
            if horizon not in self.forecasts:
                continue

            forecast, ci = self.forecasts[horizon]

            # Get last forecast value
            pred_value = forecast.iloc[-1]
            ci_lower = ci.iloc[-1]['lower']
            ci_upper = ci.iloc[-1]['upper']

            forecast_data.append({
                'Horizon (months)': horizon,
                'Forecast': pred_value,
                'Lower CI': ci_lower,
                'Upper CI': ci_upper,
                'Confidence': f"{confidence_level*100:.0f}%"
            })

        forecast_df = pd.DataFrame(forecast_data)

        return forecast_df

    def update_forecast(
        self,
        new_data: pd.Series,
        exog_new: Optional[pd.DataFrame] = None,
        refit: bool = True
    ) -> None:
        """
        Update forecasts with new data.

        Args:
            new_data: New target variable observations
            exog_new: New exogenous variables
            refit: Whether to refit the model
        """
        self.logger.info(f"Updating forecast with {len(new_data)} new observations")

        if refit:
            try:
                # Refit model with new data
                self.model.fit(new_data, exog_new)
                self.logger.info("Model refitted with new data")
            except Exception as e:
                self.logger.error(f"Error refitting model: {e}")
                raise

    def generate_prediction_intervals(
        self,
        forecast: pd.Series,
        residuals: pd.Series,
        confidence_level: float = 0.95
    ) -> pd.DataFrame:
        """
        Generate prediction intervals from residuals.

        Args:
            forecast: Forecast values
            residuals: Model residuals
            confidence_level: Confidence level

        Returns:
            DataFrame with prediction intervals
        """
        # Estimate forecast error from residuals
        residual_std = residuals.std()

        # Z-score for normal distribution
        z_score = {
            0.68: 1.0,
            0.95: 1.96,
            0.99: 2.576
        }.get(confidence_level, 1.96)

        # Prediction interval (wider than confidence interval)
        margin = z_score * residual_std * np.sqrt(1 + 1/len(residuals))

        pi_df = pd.DataFrame({
            'forecast': forecast,
            'lower': forecast - margin,
            'upper': forecast + margin
        })

        return pi_df

    def summary(self) -> str:
        """
        Get summary of forecasts.

        Returns:
            String summary
        """
        if not self.forecasts:
            return "No forecasts generated yet"

        summary = "Forecast Summary:\n"
        summary += f"Total horizons: {len(self.forecasts)}\n"
        summary += f"Horizons: {list(self.forecasts.keys())}\n"

        return summary
