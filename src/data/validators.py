"""
Data Validators Module

Validates data quality and integrity.
- Shape and size checks
- Type validation
- Statistical validation
- Temporal validation

Author: MEKKAOUI Brahim
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from src.logger import get_logger
from src.config import get_config
from src.utils import get_data_quality_report

logger = get_logger(__name__)


class DataValidator:
    """
    Validates data quality and integrity.

    Checks:
    - Non-empty data
    - Required columns
    - Data types
    - Missing values
    - Statistical properties
    - Temporal consistency
    """

    def __init__(self):
        """Initialize data validator."""
        self.config = get_config()
        self.logger = logger
        self.validation_results = {}

    def validate_dataframe(
        self,
        df: pd.DataFrame,
        name: str = "DataFrame",
        min_rows: int = 0,
        max_missing_pct: float = 10.0,
        required_columns: Optional[List[str]] = None
    ) -> bool:
        """
        Validate DataFrame basic properties.

        Args:
            df: DataFrame to validate
            name: Name for logging
            min_rows: Minimum required rows
            max_missing_pct: Maximum allowed missing percentage
            required_columns: List of required column names

        Returns:
            True if validation passes, False otherwise
        """
        self.logger.info(f"Validating {name}")

        checks = {
            'empty': not df.empty,
            'shape': len(df) >= min_rows,
        }

        if required_columns:
            checks['columns'] = all(col in df.columns for col in required_columns)

        # Missing values check
        missing_pct = df.isnull().sum().sum() / df.size * 100 if df.size > 0 else 0
        checks['missing'] = missing_pct <= max_missing_pct

        # Log results
        all_passed = all(checks.values())
        self.validation_results[name] = {
            'passed': all_passed,
            'checks': checks,
            'missing_pct': missing_pct,
            'shape': df.shape
        }

        if all_passed:
            self.logger.info(f"✓ {name} validation passed")
        else:
            self.logger.error(f"✗ {name} validation failed: {checks}")

        return all_passed

    def validate_temporal_data(
        self,
        df: pd.DataFrame,
        name: str = "Temporal Data",
        freq: Optional[str] = None
    ) -> bool:
        """
        Validate temporal/time series data properties.

        Args:
            df: DataFrame with datetime index
            name: Name for logging
            freq: Expected frequency (e.g., 'MS' for month start)

        Returns:
            True if validation passes, False otherwise
        """
        self.logger.info(f"Validating temporal properties of {name}")

        checks = {}

        # Check datetime index
        if not isinstance(df.index, pd.DatetimeIndex):
            checks['datetime_index'] = False
            self.validation_results[name] = {'passed': False, 'checks': checks}
            self.logger.error(f"{name}: Index is not DatetimeIndex")
            return False

        checks['datetime_index'] = True

        # Check sorted
        checks['sorted'] = df.index.is_monotonic_increasing

        # Check duplicates
        checks['no_duplicates'] = not df.index.has_duplicates

        # Check frequency if specified
        if freq:
            try:
                inferred_freq = pd.infer_freq(df.index)
                checks['frequency'] = inferred_freq == freq
            except Exception:
                checks['frequency'] = False

        all_passed = all(checks.values())
        self.validation_results[name] = {
            'passed': all_passed,
            'checks': checks,
            'date_range': (df.index.min(), df.index.max()),
            'length': len(df)
        }

        if all_passed:
            self.logger.info(f"✓ {name} temporal validation passed")
        else:
            self.logger.error(f"✗ {name} temporal validation failed: {checks}")

        return all_passed

    def validate_numeric_ranges(
        self,
        df: pd.DataFrame,
        name: str = "Numeric Data",
        ranges: Optional[Dict[str, tuple]] = None
    ) -> bool:
        """
        Validate numeric columns are within expected ranges.

        Args:
            df: DataFrame with numeric columns
            name: Name for logging
            ranges: Dict mapping column names to (min, max) tuples

        Returns:
            True if validation passes, False otherwise
        """
        self.logger.info(f"Validating numeric ranges of {name}")

        checks = {}
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            col_min = df[col].min()
            col_max = df[col].max()

            if ranges and col in ranges:
                expected_min, expected_max = ranges[col]
                checks[col] = (col_min >= expected_min) and (col_max <= expected_max)
            else:
                # Just check for reasonable values (not inf or extreme)
                checks[col] = np.isfinite(col_min) and np.isfinite(col_max)

        all_passed = all(checks.values())
        self.validation_results[name] = {
            'passed': all_passed,
            'checks': checks,
        }

        if all_passed:
            self.logger.info(f"✓ {name} numeric ranges validation passed")
        else:
            self.logger.error(f"✗ {name} numeric ranges validation failed")

        return all_passed

    def validate_no_leakage(
        self,
        train_df: pd.DataFrame,
        test_df: pd.DataFrame,
        name: str = "Train-Test Split",
        check_columns: Optional[List[str]] = None
    ) -> bool:
        """
        Validate there's no temporal or data leakage between train and test.

        Args:
            train_df: Training DataFrame
            test_df: Test DataFrame
            name: Name for logging
            check_columns: Specific columns to check

        Returns:
            True if no leakage detected, False otherwise
        """
        self.logger.info(f"Validating {name} for data leakage")

        checks = {}

        # Check temporal separation (for datetime index)
        if isinstance(train_df.index, pd.DatetimeIndex) and isinstance(test_df.index, pd.DatetimeIndex):
            train_max = train_df.index.max()
            test_min = test_df.index.min()
            checks['temporal_separation'] = train_max < test_min

            if checks['temporal_separation']:
                self.logger.debug(f"Temporal separation: train until {train_max}, test from {test_min}")
            else:
                self.logger.warning(f"Temporal overlap detected!")

        # Check no duplicate rows
        if check_columns:
            train_subset = train_df[check_columns]
            test_subset = test_df[check_columns]
            duplicates = pd.merge(
                train_subset.reset_index(drop=True),
                test_subset.reset_index(drop=True),
                how='inner'
            )
            checks['no_data_duplication'] = len(duplicates) == 0

        all_passed = all(checks.values())
        self.validation_results[name] = {
            'passed': all_passed,
            'checks': checks,
        }

        if all_passed:
            self.logger.info(f"✓ {name} leakage validation passed")
        else:
            self.logger.error(f"✗ {name} leakage validation failed: {checks}")

        return all_passed

    def get_quality_report(
        self,
        df: pd.DataFrame,
        name: str = "DataFrame"
    ) -> Dict[str, Any]:
        """
        Generate comprehensive data quality report.

        Args:
            df: DataFrame to report on
            name: Name for logging

        Returns:
            Dictionary with quality metrics
        """
        self.logger.info(f"Generating quality report for {name}")

        report = get_data_quality_report(df)

        return report

    def generate_validation_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive validation report from all validations.

        Returns:
            Dictionary with all validation results
        """
        report = {
            'timestamp': pd.Timestamp.now().isoformat(),
            'total_validations': len(self.validation_results),
            'passed': sum(1 for v in self.validation_results.values() if v.get('passed', False)),
            'failed': sum(1 for v in self.validation_results.values() if not v.get('passed', False)),
            'details': self.validation_results
        }

        report['success_rate'] = (
            report['passed'] / report['total_validations'] * 100
            if report['total_validations'] > 0 else 0
        )

        self.logger.info(
            f"Validation Report: {report['passed']}/{report['total_validations']} passed "
            f"({report['success_rate']:.1f}%)"
        )

        return report

    def assert_valid(
        self,
        df: pd.DataFrame,
        name: str = "DataFrame",
        **kwargs
    ) -> None:
        """
        Assert DataFrame is valid, raise exception if not.

        Args:
            df: DataFrame to validate
            name: Name for error messages
            **kwargs: Arguments to pass to validate_dataframe

        Raises:
            AssertionError: If validation fails
        """
        if not self.validate_dataframe(df, name, **kwargs):
            raise AssertionError(f"Validation failed for {name}")
