"""
Google Trends Features Module

Handles Google Trends data aggregation, normalization, and feature engineering.
- Multi-language term aggregation
- Time series smoothing
- Correlation analysis
- Lead/lag detection

Author: MEKKAOUI Brahim
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from scipy.signal import correlate
from src.logger import get_logger
from src.config import get_config

logger = get_logger(__name__)


class GoogleTrendsFeatures:
    """
    Process and engineer features from Google Trends data.

    Handles:
    - Loading 53 multilingual terms
    - Aggregating by language
    - Normalizing interest values
    - Creating lag features
    - Computing correlations with tourism metrics
    """

    def __init__(self):
        """Initialize Google Trends feature processor."""
        self.config = get_config()
        self.logger = logger
        self.terms_by_language = None
        self.normalized_data = None

    def load_and_prepare_terms(self, gt_data: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Load and prepare Google Trends data by language.

        Args:
            gt_data: Raw Google Trends DataFrame from API

        Returns:
            Dictionary mapping language codes to DataFrames
        """
        self.logger.info("Preparing Google Trends data by language")

        config = self.config
        terms = config.get_google_trends_terms()

        prepared = {}

        for lang in ['english', 'french', 'spanish', 'german']:
            if lang in terms and lang in gt_data.columns:
                lang_df = gt_data[[col for col in gt_data.columns if col in terms[lang]]].copy()
                prepared[lang] = lang_df
                self.logger.info(f"Prepared {len(lang_df.columns)} {lang} terms")

        self.terms_by_language = prepared
        return prepared

    def aggregate_by_language(
        self,
        gt_data: Dict[str, pd.DataFrame],
        method: str = 'mean'
    ) -> pd.DataFrame:
        """
        Aggregate Google Trends data by language.

        Args:
            gt_data: Dictionary of language-specific DataFrames
            method: 'mean', 'median', or 'sum'

        Returns:
            DataFrame with aggregated features by language
        """
        self.logger.info(f"Aggregating Google Trends terms by language ({method})")

        aggregated = pd.DataFrame(index=gt_data[list(gt_data.keys())[0]].index)

        for lang, df in gt_data.items():
            if method == 'mean':
                aggregated[f'gt_{lang}'] = df.mean(axis=1)
            elif method == 'median':
                aggregated[f'gt_{lang}'] = df.median(axis=1)
            elif method == 'sum':
                aggregated[f'gt_{lang}'] = df.sum(axis=1)

        self.logger.info(f"Created {len(aggregated.columns)} aggregated features")
        return aggregated

    def normalize_features(
        self,
        df: pd.DataFrame,
        method: str = 'minmax'
    ) -> pd.DataFrame:
        """
        Normalize Google Trends features.

        Args:
            df: DataFrame with raw Google Trends data
            method: 'minmax' (0-1) or 'zscore'

        Returns:
            Normalized DataFrame
        """
        self.logger.info(f"Normalizing Google Trends features ({method})")

        df_norm = df.copy()

        for col in df.columns:
            if method == 'minmax':
                min_val = df[col].min()
                max_val = df[col].max()
                if max_val - min_val != 0:
                    df_norm[col] = (df[col] - min_val) / (max_val - min_val)
            elif method == 'zscore':
                mean_val = df[col].mean()
                std_val = df[col].std()
                if std_val != 0:
                    df_norm[col] = (df[col] - mean_val) / std_val

        self.normalized_data = df_norm
        return df_norm

    def apply_smoothing(
        self,
        df: pd.DataFrame,
        window: int = 3,
        method: str = 'rolling_mean'
    ) -> pd.DataFrame:
        """
        Apply smoothing to Google Trends data.

        Args:
            df: Input DataFrame
            window: Window size for smoothing
            method: 'rolling_mean' or 'exponential'

        Returns:
            Smoothed DataFrame
        """
        self.logger.info(f"Applying {method} smoothing (window={window})")

        df_smooth = df.copy()

        for col in df.columns:
            if method == 'rolling_mean':
                df_smooth[col] = df[col].rolling(window=window, center=True).mean()
            elif method == 'exponential':
                df_smooth[col] = df[col].ewm(span=window).mean()

        return df_smooth

    def create_lag_features(
        self,
        df: pd.DataFrame,
        lags: List[int] = [1, 3, 6, 12]
    ) -> pd.DataFrame:
        """
        Create lag features from Google Trends data.

        Args:
            df: Input DataFrame
            lags: List of lag values (in months)

        Returns:
            DataFrame with original and lag features
        """
        self.logger.info(f"Creating lag features with lags: {lags}")

        df_lags = df.copy()

        for lag in lags:
            for col in df.columns:
                df_lags[f'{col}_lag{lag}'] = df[col].shift(lag)

        return df_lags

    def calculate_correlation(
        self,
        gt_df: pd.DataFrame,
        target_df: pd.Series,
        lags: Optional[List[int]] = None
    ) -> Dict[str, float]:
        """
        Calculate correlation between Google Trends and tourism metric.

        Args:
            gt_df: Google Trends DataFrame
            target_df: Target series (e.g., tourist arrivals)
            lags: Lag values to test

        Returns:
            Dictionary with correlation values
        """
        if lags is None:
            lags = [0, 1, 3, 6]

        self.logger.info(f"Calculating correlations with {len(lags)} lag values")

        correlations = {}

        for col in gt_df.columns:
            max_corr = 0
            best_lag = 0

            for lag in lags:
                if lag == 0:
                    corr = gt_df[col].corr(target_df)
                else:
                    shifted_gt = gt_df[col].shift(lag)
                    corr = shifted_gt.corr(target_df)

                if abs(corr) > abs(max_corr):
                    max_corr = corr
                    best_lag = lag

            correlations[col] = {
                'correlation': max_corr,
                'lag': best_lag
            }

        return correlations

    def detect_optimal_lead_lag(
        self,
        gt_data: pd.DataFrame,
        target_data: pd.Series,
        max_lag: int = 12
    ) -> Dict[str, int]:
        """
        Detect optimal lead/lag for each Google Trends term.

        Args:
            gt_data: Google Trends features
            target_data: Target variable (e.g., arrivals)
            max_lag: Maximum lag to test (in months)

        Returns:
            Dictionary mapping terms to optimal lags
        """
        self.logger.info(f"Detecting optimal lead/lag (max_lag={max_lag})")

        optimal_lags = {}

        # Remove NaN values for correlation
        valid_idx = ~(gt_data.isnull().any(axis=1) | target_data.isnull())
        gt_clean = gt_data[valid_idx].reset_index(drop=True)
        target_clean = target_data[valid_idx].reset_index(drop=True)

        for col in gt_clean.columns:
            max_corr = 0
            best_lag = 0

            for lag in range(-max_lag, max_lag + 1):
                if lag < 0:
                    # Negative lag: target leads Google Trends
                    corr = gt_clean[col].iloc[-lag:].corr(target_clean.iloc[:lag])
                elif lag == 0:
                    corr = gt_clean[col].corr(target_clean)
                else:
                    # Positive lag: Google Trends leads target
                    corr = gt_clean[col].iloc[:-lag].corr(target_clean.iloc[lag:])

                if pd.notna(corr) and abs(corr) > abs(max_corr):
                    max_corr = corr
                    best_lag = lag

            optimal_lags[col] = best_lag

        # Summary statistics
        lag_dist = {}
        for lag in optimal_lags.values():
            lag_dist[lag] = lag_dist.get(lag, 0) + 1

        self.logger.info(f"Optimal lag distribution: {lag_dist}")

        return optimal_lags

    def apply_optimal_lags(
        self,
        gt_data: pd.DataFrame,
        optimal_lags: Dict[str, int]
    ) -> pd.DataFrame:
        """
        Apply optimal lags to Google Trends data.

        Args:
            gt_data: Google Trends DataFrame
            optimal_lags: Dictionary mapping columns to lag values

        Returns:
            Lagged Google Trends DataFrame
        """
        self.logger.info("Applying optimal lags to Google Trends data")

        gt_lagged = gt_data.copy()

        for col, lag in optimal_lags.items():
            if col in gt_lagged.columns:
                gt_lagged[col] = gt_lagged[col].shift(lag)

        return gt_lagged
