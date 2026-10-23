"""
Crisis Analysis Module

Analyzes impact of major events (COVID-19, earthquakes, etc.) on tourism.
Identifies structural breaks and anomalies in the data.

Author: MEKKAOUI Brahim
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, List
from datetime import datetime
from src.logger import get_logger

logger = get_logger(__name__)


class CrisisAnalyzer:
    """
    Analyze impact of crises on tourism metrics.

    Supports:
    - COVID-19 pandemic (2020-2021)
    - Earthquakes (September 2023)
    - Other major events
    """

    # Define crisis periods
    CRISIS_PERIODS = {
        'COVID-19': {
            'start': '2020-03-01',
            'end': '2021-12-31',
            'description': 'COVID-19 Pandemic'
        },
        'Earthquake_2023': {
            'start': '2023-09-08',
            'end': '2023-12-31',
            'description': 'Al Haouz Earthquake'
        },
        'Recovery_2024': {
            'start': '2024-01-01',
            'end': '2024-12-31',
            'description': 'Post-Crisis Recovery'
        }
    }

    def __init__(self):
        """Initialize crisis analyzer."""
        self.logger = logger
        self.crisis_data = {}

    def analyze_crisis_impact(
        self,
        data: pd.Series,
        crisis_name: str = 'COVID-19'
    ) -> Dict:
        """
        Analyze impact of a specific crisis.

        Args:
            data: Time series data
            crisis_name: Name of crisis to analyze

        Returns:
            Dictionary with impact metrics
        """
        if crisis_name not in self.CRISIS_PERIODS:
            raise ValueError(f"Crisis '{crisis_name}' not defined")

        crisis_info = self.CRISIS_PERIODS[crisis_name]
        start = pd.to_datetime(crisis_info['start'])
        end = pd.to_datetime(crisis_info['end'])

        # Get pre-crisis, during-crisis, and post-crisis data
        pre_crisis = data[data.index < start]
        during_crisis = data[(data.index >= start) & (data.index <= end)]
        post_crisis = data[data.index > end]

        # Calculate metrics
        pre_mean = pre_crisis.mean() if len(pre_crisis) > 0 else np.nan
        during_mean = during_crisis.mean() if len(during_crisis) > 0 else np.nan
        post_mean = post_crisis.mean() if len(post_crisis) > 0 else np.nan

        pre_std = pre_crisis.std() if len(pre_crisis) > 0 else np.nan
        during_std = during_crisis.std() if len(during_crisis) > 0 else np.nan
        post_std = post_crisis.std() if len(post_crisis) > 0 else np.nan

        # Calculate impact metrics
        impact_pct = ((during_mean - pre_mean) / pre_mean * 100) if pre_mean > 0 else np.nan
        recovery_pct = ((post_mean - pre_mean) / pre_mean * 100) if pre_mean > 0 else np.nan

        result = {
            'crisis': crisis_name,
            'description': crisis_info['description'],
            'period': f"{start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}",
            'pre_crisis': {
                'mean': pre_mean,
                'std': pre_std,
                'min': pre_crisis.min(),
                'max': pre_crisis.max(),
                'count': len(pre_crisis)
            },
            'during_crisis': {
                'mean': during_mean,
                'std': during_std,
                'min': during_crisis.min() if len(during_crisis) > 0 else np.nan,
                'max': during_crisis.max() if len(during_crisis) > 0 else np.nan,
                'count': len(during_crisis)
            },
            'post_crisis': {
                'mean': post_mean,
                'std': post_std,
                'min': post_crisis.min() if len(post_crisis) > 0 else np.nan,
                'max': post_crisis.max() if len(post_crisis) > 0 else np.nan,
                'count': len(post_crisis)
            },
            'impact_pct': impact_pct,
            'recovery_pct': recovery_pct
        }

        return result

    def detect_structural_breaks(
        self,
        data: pd.Series,
        window_size: int = 12
    ) -> List[Dict]:
        """
        Detect structural breaks using rolling statistics.

        Args:
            data: Time series data
            window_size: Window size for rolling statistics

        Returns:
            List of detected breaks
        """
        # Calculate rolling mean and std
        rolling_mean = data.rolling(window=window_size).mean()
        rolling_std = data.rolling(window=window_size).std()

        # Calculate z-score of changes
        changes = data.diff().abs()
        z_scores = (changes - changes.mean()) / changes.std()

        # Detect breaks (3+ standard deviations)
        breaks = []
        for idx, (date, z_score) in enumerate(zip(data.index, z_scores)):
            if z_score > 3 and idx > window_size:
                breaks.append({
                    'date': date,
                    'value': data.iloc[idx],
                    'z_score': z_score,
                    'change_pct': (changes.iloc[idx] / data.iloc[idx-1] * 100) if data.iloc[idx-1] != 0 else np.nan
                })

        return breaks

    def analyze_all_crises(self, data: pd.Series) -> Dict:
        """
        Analyze all defined crises.

        Args:
            data: Time series data

        Returns:
            Dictionary with all crisis analyses
        """
        results = {}
        for crisis_name in self.CRISIS_PERIODS.keys():
            try:
                results[crisis_name] = self.analyze_crisis_impact(data, crisis_name)
                self.logger.info(f"✓ Analyzed {crisis_name}")
            except Exception as e:
                self.logger.error(f"Error analyzing {crisis_name}: {e}")

        return results

    def get_crisis_summary(self, analyses: Dict) -> pd.DataFrame:
        """
        Create summary table of all crises.

        Args:
            analyses: Dictionary of crisis analyses

        Returns:
            Summary DataFrame
        """
        rows = []
        for crisis_name, analysis in analyses.items():
            rows.append({
                'Crisis': analysis['description'],
                'Period': analysis['period'],
                'Pre-Crisis Mean': analysis['pre_crisis']['mean'],
                'During Crisis Mean': analysis['during_crisis']['mean'],
                'Post-Crisis Mean': analysis['post_crisis']['mean'],
                'Impact (%)': analysis['impact_pct'],
                'Recovery (%)': analysis['recovery_pct']
            })

        return pd.DataFrame(rows)

    def identify_anomalies(
        self,
        data: pd.Series,
        threshold: float = 2.5
    ) -> pd.DataFrame:
        """
        Identify anomalous values in time series.

        Args:
            data: Time series data
            threshold: Z-score threshold for anomalies

        Returns:
            DataFrame of anomalies
        """
        # Calculate z-scores
        z_scores = np.abs((data - data.mean()) / data.std())

        # Find anomalies
        anomalies = []
        for date, (value, z_score) in enumerate(zip(data.values, z_scores)):
            if z_score > threshold:
                anomalies.append({
                    'date': data.index[date],
                    'value': value,
                    'z_score': z_score,
                    'deviation_pct': ((value - data.mean()) / data.mean() * 100)
                })

        return pd.DataFrame(anomalies)
