"""
Nowcasting Module

Provides real-time or near-real-time forecasts using latest available data.
Combines multiple data sources for high-frequency predictions.

Author: MEKKAOUI Brahim
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
from datetime import datetime, timedelta
from src.logger import get_logger

logger = get_logger(__name__)


class NowcastingEngine:
    """
    Generate nowcasts (current period predictions) using:
    - Latest arrivals data
    - Current Google Trends signals
    - Real-time indicators
    """

    def __init__(self, lookback_days: int = 7):
        """
        Initialize nowcasting engine.

        Args:
            lookback_days: Days to look back for trend analysis
        """
        self.lookback_days = lookback_days
        self.logger = logger
        self.latest_nowcast = None

    def calculate_google_trends_signal(
        self,
        gt_data: pd.DataFrame,
        lookback_days: int = 7
    ) -> Dict:
        """
        Calculate nowcasting signal from Google Trends.

        Args:
            gt_data: Google Trends DataFrame
            lookback_days: Days to analyze

        Returns:
            Dictionary with trend signals
        """
        if len(gt_data) == 0:
            raise ValueError("Empty Google Trends data")

        # Get latest data
        latest = gt_data.iloc[-1:]
        previous = gt_data.iloc[max(0, -lookback_days):-1]

        # Calculate change
        latest_mean = latest.mean().mean()
        previous_mean = previous.mean().mean() if len(previous) > 0 else latest_mean

        trend_change = ((latest_mean - previous_mean) / previous_mean * 100) if previous_mean != 0 else 0

        # Identify top trends
        top_cols = gt_data.iloc[-1:].nlargest(5, axis=1).columns.tolist()

        return {
            'latest_mean': latest_mean,
            'previous_mean': previous_mean,
            'trend_change_pct': trend_change,
            'trend_direction': 'up' if trend_change > 0 else 'down',
            'top_trends': top_cols
        }

    def calculate_historical_momentum(
        self,
        arrivals: pd.Series,
        periods: int = 3
    ) -> Dict:
        """
        Calculate momentum from historical data.

        Args:
            arrivals: Historical arrivals data
            periods: Number of periods to analyze

        Returns:
            Dictionary with momentum metrics
        """
        if len(arrivals) < periods:
            raise ValueError(f"Need at least {periods} periods of data")

        # Get latest periods
        latest_periods = arrivals.iloc[-periods:]

        # Calculate growth rate
        growth_rates = latest_periods.pct_change().dropna()
        avg_growth = growth_rates.mean()
        momentum = avg_growth * 100

        # Trend direction
        trend_direction = 'up' if avg_growth > 0 else 'down'

        # Volatility
        volatility = growth_rates.std()

        return {
            'momentum_pct': momentum,
            'trend_direction': trend_direction,
            'volatility': volatility,
            'latest_value': latest_periods.iloc[-1],
            'previous_value': latest_periods.iloc[0]
        }

    def combine_signals(
        self,
        arrivals_momentum: Dict,
        gt_signal: Dict,
        arrivals_weight: float = 0.6,
        gt_weight: float = 0.4
    ) -> Dict:
        """
        Combine multiple nowcasting signals.

        Args:
            arrivals_momentum: Momentum from arrivals data
            gt_signal: Google Trends signal
            arrivals_weight: Weight for arrivals signal
            gt_weight: Weight for GT signal

        Returns:
            Combined nowcast signal
        """
        # Normalize signals to 0-100 scale
        arrivals_norm = (arrivals_momentum['momentum_pct'] + 50)  # Center around 50
        gt_norm = (gt_signal['trend_change_pct'] + 50)  # Center around 50

        # Combine signals
        combined_signal = (arrivals_norm * arrivals_weight +
                          gt_norm * gt_weight)

        return {
            'combined_signal': combined_signal,
            'arrivals_momentum': arrivals_momentum['momentum_pct'],
            'gt_trend': gt_signal['trend_change_pct'],
            'forecast_direction': 'positive' if combined_signal > 50 else 'negative',
            'confidence': min(abs(combined_signal - 50) / 50, 1.0)
        }

    def generate_nowcast(
        self,
        arrivals: pd.Series,
        gt_data: pd.DataFrame,
        forecast_model=None,
        steps: int = 1
    ) -> Dict:
        """
        Generate nowcast for current/next period.

        Args:
            arrivals: Historical arrivals data
            gt_data: Google Trends data
            forecast_model: Optional trained forecast model
            steps: Steps ahead to forecast (default 1)

        Returns:
            Nowcast with confidence intervals
        """
        logger.info("Generating nowcast...")

        # Calculate signals
        momentum = self.calculate_historical_momentum(arrivals, periods=3)
        gt_signal = self.calculate_google_trends_signal(gt_data, lookback_days=7)

        # Combine signals
        combined = self.combine_signals(momentum, gt_signal)

        # Generate point forecast
        latest_value = arrivals.iloc[-1]
        growth_rate = momentum['momentum_pct'] / 100
        nowcast_value = latest_value * (1 + growth_rate)

        # Calculate confidence interval (±15%)
        lower_ci = nowcast_value * 0.85
        upper_ci = nowcast_value * 1.15

        # Build nowcast
        nowcast = {
            'generated_at': datetime.now().isoformat(),
            'period': f"Current + {steps}",
            'forecast_value': nowcast_value,
            'lower_ci': lower_ci,
            'upper_ci': upper_ci,
            'latest_actual': latest_value,
            'signals': {
                'momentum': momentum,
                'google_trends': gt_signal,
                'combined': combined
            }
        }

        self.latest_nowcast = nowcast
        logger.info(f"✓ Nowcast generated: {nowcast_value:.2f}")

        return nowcast

    def get_nowcast_interpretation(self) -> str:
        """
        Get human-readable interpretation of latest nowcast.

        Returns:
            Interpretation text
        """
        if self.latest_nowcast is None:
            return "No nowcast available"

        signals = self.latest_nowcast['signals']
        combined = signals['combined']
        forecast = self.latest_nowcast['forecast_value']
        actual = self.latest_nowcast['latest_actual']

        direction = "INCREASING" if combined['forecast_direction'] == 'positive' else "DECREASING"
        confidence = combined['confidence']
        change_pct = (forecast - actual) / actual * 100

        interpretation = f"""
        NOWCAST INTERPRETATION
        =====================

        Forecast Direction: {direction}
        Confidence Level: {confidence * 100:.1f}%

        Expected Value: {forecast:.2f}
        Latest Actual: {actual:.2f}
        Expected Change: {change_pct:+.1f}%

        Key Signals:
        - Arrivals Momentum: {signals['momentum']['momentum_pct']:+.2f}%
        - Google Trends Trend: {signals['google_trends']['trend_change_pct']:+.2f}%
        - Top Search Terms: {', '.join(signals['google_trends']['top_trends'][:3])}
        """

        return interpretation

    def update_with_new_data(
        self,
        new_arrivals: pd.Series,
        new_gt_data: pd.DataFrame
    ) -> Dict:
        """
        Update nowcast with new data.

        Args:
            new_arrivals: New arrivals data point(s)
            new_gt_data: New Google Trends data

        Returns:
            Updated nowcast
        """
        logger.info("Updating nowcast with new data...")

        return self.generate_nowcast(
            arrivals=new_arrivals,
            gt_data=new_gt_data
        )

    def get_summary_table(self, nowcast: Dict) -> pd.DataFrame:
        """
        Create summary table of nowcast.

        Args:
            nowcast: Nowcast dictionary

        Returns:
            Summary DataFrame
        """
        signals = nowcast['signals']

        summary = pd.DataFrame({
            'Metric': [
                'Forecast Value',
                'Lower CI (85%)',
                'Upper CI (115%)',
                'Latest Actual',
                'Arrivals Momentum (%)',
                'Google Trends Trend (%)',
                'Combined Signal',
                'Forecast Direction',
                'Confidence Level'
            ],
            'Value': [
                f"{nowcast['forecast_value']:.2f}",
                f"{nowcast['lower_ci']:.2f}",
                f"{nowcast['upper_ci']:.2f}",
                f"{nowcast['latest_actual']:.2f}",
                f"{signals['momentum']['momentum_pct']:+.2f}%",
                f"{signals['google_trends']['trend_change_pct']:+.2f}%",
                f"{signals['combined']['combined_signal']:.2f}",
                signals['combined']['forecast_direction'].upper(),
                f"{signals['combined']['confidence']*100:.1f}%"
            ]
        })

        return summary
