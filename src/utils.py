"""
Utility Functions Module

Common utility functions for data processing, validation, and file handling.

Author: MEKKAOUI Brahim
"""

import pickle
import joblib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime
from src.logger import get_logger

logger = get_logger(__name__)


def ensure_directory(path: str) -> Path:
    """
    Create directory if it doesn't exist.

    Args:
        path: Directory path

    Returns:
        Path object pointing to created directory
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Directory ensured: {dir_path}")
    return dir_path


def save_pickle(obj: Any, filepath: str) -> None:
    """
    Save Python object to pickle file.

    Args:
        obj: Object to save
        filepath: Path to save file
    """
    ensure_directory(Path(filepath).parent)
    with open(filepath, 'wb') as f:
        pickle.dump(obj, f)
    logger.info(f"Object saved to pickle: {filepath}")


def load_pickle(filepath: str) -> Any:
    """
    Load Python object from pickle file.

    Args:
        filepath: Path to pickle file

    Returns:
        Loaded object
    """
    with open(filepath, 'rb') as f:
        obj = pickle.load(f)
    logger.info(f"Object loaded from pickle: {filepath}")
    return obj


def save_joblib(obj: Any, filepath: str) -> None:
    """
    Save Python object using joblib (better for large numpy arrays/models).

    Args:
        obj: Object to save
        filepath: Path to save file
    """
    ensure_directory(Path(filepath).parent)
    joblib.dump(obj, filepath)
    logger.info(f"Object saved with joblib: {filepath}")


def load_joblib(filepath: str) -> Any:
    """
    Load Python object using joblib.

    Args:
        filepath: Path to joblib file

    Returns:
        Loaded object
    """
    obj = joblib.load(filepath)
    logger.info(f"Object loaded with joblib: {filepath}")
    return obj


def save_json(data: Dict, filepath: str) -> None:
    """
    Save dictionary to JSON file.

    Args:
        data: Dictionary to save
        filepath: Path to save file
    """
    ensure_directory(Path(filepath).parent)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"JSON saved: {filepath}")


def load_json(filepath: str) -> Dict:
    """
    Load dictionary from JSON file.

    Args:
        filepath: Path to JSON file

    Returns:
        Loaded dictionary
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    logger.info(f"JSON loaded: {filepath}")
    return data


def save_csv(df: pd.DataFrame, filepath: str, index: bool = False) -> None:
    """
    Save DataFrame to CSV file.

    Args:
        df: DataFrame to save
        filepath: Path to save file
        index: Whether to save index column
    """
    ensure_directory(Path(filepath).parent)
    df.to_csv(filepath, index=index, encoding='utf-8')
    logger.info(f"CSV saved: {filepath} ({len(df)} rows)")


def load_csv(filepath: str, parse_dates: Optional[List] = None) -> pd.DataFrame:
    """
    Load CSV file into DataFrame.

    Args:
        filepath: Path to CSV file
        parse_dates: List of column names to parse as dates

    Returns:
        Loaded DataFrame
    """
    df = pd.read_csv(filepath, parse_dates=parse_dates)
    logger.info(f"CSV loaded: {filepath} ({len(df)} rows)")
    return df


def validate_dataframe(
    df: pd.DataFrame,
    name: str = "DataFrame",
    min_rows: int = 0,
    check_dates: bool = False,
    check_columns: Optional[List[str]] = None
) -> bool:
    """
    Validate DataFrame quality and structure.

    Args:
        df: DataFrame to validate
        name: Name for logging purposes
        min_rows: Minimum number of rows required
        check_dates: Whether to check for date columns
        check_columns: List of required column names

    Returns:
        True if validation passes, False otherwise
    """
    # Check DataFrame not empty
    if df.empty:
        logger.error(f"{name}: DataFrame is empty")
        return False

    # Check row count
    if len(df) < min_rows:
        logger.error(f"{name}: Has {len(df)} rows, expected at least {min_rows}")
        return False

    # Check required columns
    if check_columns:
        missing_cols = set(check_columns) - set(df.columns)
        if missing_cols:
            logger.error(f"{name}: Missing columns: {missing_cols}")
            return False

    # Check for excessive missing values
    missing_pct = df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100
    if missing_pct > 50:
        logger.warning(f"{name}: {missing_pct:.1f}% missing values")

    logger.info(f"{name} validation passed: {len(df)} rows, {len(df.columns)} columns")
    return True


def get_data_quality_report(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate data quality report for DataFrame.

    Args:
        df: DataFrame to analyze

    Returns:
        Dictionary with quality metrics
    """
    report = {
        'shape': df.shape,
        'columns': list(df.columns),
        'dtypes': df.dtypes.astype(str).to_dict(),
        'missing_values': df.isnull().sum().to_dict(),
        'missing_percentage': (df.isnull().sum() / len(df) * 100).to_dict(),
        'numeric_summary': df.describe().to_dict(),
        'duplicates': df.duplicated().sum(),
    }

    return report


def detect_outliers(
    series: pd.Series,
    method: str = 'zscore',
    threshold: float = 3.0
) -> pd.Series:
    """
    Detect outliers in a pandas Series.

    Args:
        series: Series to analyze
        method: 'zscore' or 'iqr'
        threshold: Threshold for outlier detection

    Returns:
        Boolean Series marking outliers
    """
    if method == 'zscore':
        z_scores = np.abs((series - series.mean()) / series.std())
        return z_scores > threshold
    elif method == 'iqr':
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        return (series < (Q1 - threshold * IQR)) | (series > (Q3 + threshold * IQR))
    else:
        raise ValueError(f"Unknown method: {method}")


def time_series_split(
    df: pd.DataFrame,
    train_size: float = 0.8,
    date_column: Optional[str] = None
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split time series data into train and test sets.

    Args:
        df: Time series DataFrame (should be sorted by date)
        train_size: Proportion of data for training
        date_column: Name of date column (for validation)

    Returns:
        Tuple of (train_df, test_df)
    """
    split_idx = int(len(df) * train_size)
    train_df = df.iloc[:split_idx].copy()
    test_df = df.iloc[split_idx:].copy()

    logger.info(
        f"Time series split: train={len(train_df)} rows, test={len(test_df)} rows"
    )

    return train_df, test_df


def rolling_window_split(
    df: pd.DataFrame,
    window_size: int,
    step_size: int = 1,
    min_train_size: Optional[int] = None
) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
    """
    Create rolling window splits for temporal cross-validation.

    Args:
        df: Time series DataFrame
        window_size: Size of test window
        step_size: Step size for rolling window
        min_train_size: Minimum training set size

    Returns:
        List of (train_df, test_df) tuples
    """
    if min_train_size is None:
        min_train_size = len(df) // 2

    splits = []
    for i in range(min_train_size, len(df) - window_size, step_size):
        train_df = df.iloc[:i].copy()
        test_df = df.iloc[i:i + window_size].copy()
        splits.append((train_df, test_df))

    logger.info(f"Created {len(splits)} rolling window splits")
    return splits


def get_timestamp() -> str:
    """
    Get current timestamp as formatted string.

    Returns:
        ISO format timestamp
    """
    return datetime.now().isoformat()


def log_performance(
    model_name: str,
    metrics: Dict[str, float],
    dataset: str = "test"
) -> None:
    """
    Log model performance metrics.

    Args:
        model_name: Name of model
        metrics: Dictionary of metric names and values
        dataset: Name of dataset (train/test/validation)
    """
    logger.info(f"Performance on {dataset} set ({model_name}):")
    for metric, value in metrics.items():
        logger.info(f"  {metric}: {value:.4f}")
