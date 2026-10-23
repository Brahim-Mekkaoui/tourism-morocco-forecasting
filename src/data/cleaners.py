"""
Data Cleaners Module

Handles data cleaning, preprocessing, and normalization.
- Missing value imputation
- Outlier detection and handling
- Data type conversion
- Feature scaling

Author: MEKKAOUI Brahim
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from src.logger import get_logger
from src.config import get_config
from src.utils import detect_outliers

logger = get_logger(__name__)


class DataCleaner:
    """
    Main data cleaning orchestrator.

    Coordinates cleaning operations across multiple datasets.
    """

    def __init__(self):
        """Initialize data cleaner."""
        self.config = get_config()
        self.logger = logger

    def clean_manar_data(self, df: pd.DataFrame, data_type: str) -> pd.DataFrame:
        """
        Clean MANAR (tourism ministry) data.

        Steps:
        1. Identify date column
        2. Parse dates
        3. Sort by date
        4. Handle missing values
        5. Detect outliers

        Args:
            df: Raw DataFrame from MANAR Excel file
            data_type: Type of MANAR data for context-specific cleaning

        Returns:
            Cleaned DataFrame
        """
        self.logger.info(f"Cleaning MANAR data: {data_type}")

        df = df.copy()

        # Try to identify and parse date column
        df = self._parse_date_column(df)

        # Sort by date
        if hasattr(df.index, 'name') and 'date' in str(df.index.name).lower():
            df = df.sort_index()
        elif 'date' in df.columns:
            df = df.sort_values('date')

        # Handle missing values
        df = self._handle_missing_values(df)

        # Detect and handle outliers
        df = self._handle_outliers(df, method='zscore')

        self.logger.info(f"Cleaned {data_type}: {df.shape}")
        return df

    def clean_google_trends_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean Google Trends data.

        Steps:
        1. Parse date index
        2. Handle missing values
        3. Normalize values (0-100 scale)
        4. Detect anomalies

        Args:
            df: DataFrame from Google Trends API

        Returns:
            Cleaned DataFrame
        """
        self.logger.info("Cleaning Google Trends data")

        df = df.copy()

        # Ensure datetime index
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)

        # Handle missing values with forward fill
        df = df.fillna(method='ffill').fillna(method='bfill')

        # Normalize if necessary (Google Trends is already 0-100)
        # Just ensure numeric types
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = pd.to_numeric(df[col], errors='coerce')

        self.logger.info(f"Cleaned Google Trends data: {df.shape}")
        return df

    def _parse_date_column(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Identify and parse date column in DataFrame.

        Args:
            df: DataFrame to parse

        Returns:
            DataFrame with parsed date column
        """
        # Try common date column names
        date_candidates = ['date', 'Date', 'Date_Year', 'Année', 'Année-Mois', 'période']

        for col in date_candidates:
            if col in df.columns:
                try:
                    df[col] = pd.to_datetime(df[col])
                    df = df.set_index(col)
                    self.logger.debug(f"Parsed date column: {col}")
                    return df
                except Exception as e:
                    self.logger.debug(f"Failed to parse {col}: {e}")

        # Try to parse first column as date
        try:
            df.index = pd.to_datetime(df.iloc[:, 0])
            df = df.iloc[:, 1:]
            self.logger.debug("Parsed first column as date index")
            return df
        except Exception:
            self.logger.warning("Could not identify date column")
            return df

    def _handle_missing_values(
        self,
        df: pd.DataFrame,
        method: str = 'forward_fill',
        max_missing_pct: float = 10.0
    ) -> pd.DataFrame:
        """
        Handle missing values in DataFrame.

        Args:
            df: DataFrame with potential missing values
            method: 'forward_fill', 'backward_fill', 'interpolate', or 'drop'
            max_missing_pct: Maximum allowed missing percentage

        Returns:
            DataFrame with missing values handled
        """
        missing_pct = df.isnull().sum().sum() / df.size * 100

        if missing_pct == 0:
            self.logger.debug("No missing values found")
            return df

        self.logger.info(f"Found {missing_pct:.2f}% missing values")

        if missing_pct > max_missing_pct:
            self.logger.warning(
                f"Missing percentage {missing_pct:.2f}% exceeds threshold {max_missing_pct}%"
            )

        if method == 'forward_fill':
            df = df.fillna(method='ffill').fillna(method='bfill')
        elif method == 'backward_fill':
            df = df.fillna(method='bfill').fillna(method='ffill')
        elif method == 'interpolate':
            df = df.interpolate(method='linear', limit_direction='both')
        elif method == 'drop':
            df = df.dropna()

        self.logger.debug(f"Handled missing values using {method}")
        return df

    def _handle_outliers(
        self,
        df: pd.DataFrame,
        method: str = 'zscore',
        threshold: float = 3.0,
        action: str = 'cap'
    ) -> pd.DataFrame:
        """
        Detect and handle outliers in DataFrame.

        Args:
            df: DataFrame to process
            method: 'zscore' or 'iqr'
            threshold: Outlier detection threshold
            action: 'remove', 'cap', or 'flag'

        Returns:
            DataFrame with outliers handled
        """
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        outlier_count = 0
        for col in numeric_cols:
            outliers = detect_outliers(df[col], method=method, threshold=threshold)

            if outliers.any():
                outlier_count += outliers.sum()

                if action == 'remove':
                    df = df[~outliers]
                elif action == 'cap':
                    # Cap outliers to 95th/5th percentile
                    upper = df[col].quantile(0.95)
                    lower = df[col].quantile(0.05)
                    df[col] = df[col].clip(lower, upper)
                elif action == 'flag':
                    df[f'{col}_outlier'] = outliers

        if outlier_count > 0:
            self.logger.info(f"Found and handled {outlier_count} outliers")

        return df

    def normalize_features(
        self,
        df: pd.DataFrame,
        method: str = 'minmax',
        exclude_cols: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Normalize numeric features.

        Args:
            df: DataFrame to normalize
            method: 'minmax' (0-1) or 'zscore' (mean=0, std=1)
            exclude_cols: Column names to exclude from normalization

        Returns:
            Normalized DataFrame
        """
        if exclude_cols is None:
            exclude_cols = []

        df_normalized = df.copy()
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            if col in exclude_cols:
                continue

            if method == 'minmax':
                min_val = df[col].min()
                max_val = df[col].max()
                if max_val - min_val != 0:
                    df_normalized[col] = (df[col] - min_val) / (max_val - min_val)

            elif method == 'zscore':
                mean_val = df[col].mean()
                std_val = df[col].std()
                if std_val != 0:
                    df_normalized[col] = (df[col] - mean_val) / std_val

        self.logger.info(f"Normalized {len(numeric_cols)} numeric features using {method}")
        return df_normalized

    def align_datasets(
        self,
        dfs: Dict[str, pd.DataFrame],
        method: str = 'inner'
    ) -> Dict[str, pd.DataFrame]:
        """
        Align multiple DataFrames by date index.

        Args:
            dfs: Dictionary of DataFrames to align
            method: 'inner' (intersection) or 'outer' (union)

        Returns:
            Dictionary of aligned DataFrames
        """
        if not dfs:
            return dfs

        # Get all dates
        all_dates = set()
        for df in dfs.values():
            if isinstance(df.index, pd.DatetimeIndex):
                all_dates.update(df.index)

        if not all_dates:
            self.logger.warning("No datetime index found in DataFrames")
            return dfs

        all_dates = sorted(all_dates)

        # Align each DataFrame
        aligned = {}
        for name, df in dfs.items():
            if isinstance(df.index, pd.DatetimeIndex):
                aligned[name] = df.reindex(all_dates)
            else:
                aligned[name] = df

        self.logger.info(f"Aligned {len(aligned)} datasets to {len(all_dates)} dates")
        return aligned
