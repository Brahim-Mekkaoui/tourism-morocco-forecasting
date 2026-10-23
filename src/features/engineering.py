"""
Feature Engineering Module

Dimensionality reduction and feature transformation.
- Principal Component Analysis (PCA/ACP)
- Partial Least Squares (PLS)
- Feature selection
- Feature importance

Author: MEKKAOUI Brahim
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from sklearn.decomposition import PCA
from sklearn.cross_decomposition import PLSRegression
from sklearn.preprocessing import StandardScaler
from src.logger import get_logger
from src.config import get_config
from src.utils import save_joblib, load_joblib

logger = get_logger(__name__)


class FeatureEngineer:
    """
    Main feature engineering coordinator.

    Handles:
    - Feature scaling
    - PCA/ACP transformation
    - PLS transformation
    - Feature importance calculation
    """

    def __init__(self):
        """Initialize feature engineer."""
        self.config = get_config()
        self.logger = logger
        self.scaler = StandardScaler()
        self.pca = None
        self.pls = None
        self.scaled_data = None

    def scale_features(
        self,
        X: pd.DataFrame,
        fit: bool = True
    ) -> pd.DataFrame:
        """
        Scale features using StandardScaler.

        Args:
            X: Input features DataFrame
            fit: Whether to fit scaler (True for training)

        Returns:
            Scaled DataFrame
        """
        self.logger.info(f"Scaling features: fit={fit}")

        if fit:
            X_scaled = self.scaler.fit_transform(X)
        else:
            X_scaled = self.scaler.transform(X)

        X_scaled_df = pd.DataFrame(
            X_scaled,
            index=X.index,
            columns=X.columns
        )

        self.scaled_data = X_scaled_df
        return X_scaled_df

    def apply_pca(
        self,
        X: pd.DataFrame,
        n_components: Optional[int] = None,
        fit: bool = True
    ) -> Tuple[pd.DataFrame, PCA]:
        """
        Apply Principal Component Analysis (PCA/ACP).

        Reduces 53 Google Trends terms to n_components principal components.

        Args:
            X: Input features (typically 53 Google Trends terms)
            n_components: Number of components (default from config: 3)
            fit: Whether to fit PCA (True for training)

        Returns:
            Tuple of (transformed DataFrame, PCA model)
        """
        if n_components is None:
            n_components = self.config.get('features.dimensionality_reduction.pca.n_components', 3)

        self.logger.info(f"Applying PCA with {n_components} components")

        # Scale features first
        X_scaled = self.scale_features(X, fit=fit)

        if fit:
            self.pca = PCA(
                n_components=n_components,
                random_state=self.config.get('features.dimensionality_reduction.pca.random_state', 42)
            )
            X_pca = self.pca.fit_transform(X_scaled)
        else:
            if self.pca is None:
                raise ValueError("PCA model not fitted yet. Call with fit=True first.")
            X_pca = self.pca.transform(X_scaled)

        # Calculate explained variance
        explained_var = self.pca.explained_variance_ratio_
        cumsum_var = np.cumsum(explained_var)

        self.logger.info(f"PCA explained variance: {explained_var}")
        self.logger.info(f"Cumulative variance: {cumsum_var}")

        # Create DataFrame with component names
        X_pca_df = pd.DataFrame(
            X_pca,
            index=X.index,
            columns=[f'PC{i+1}' for i in range(n_components)]
        )

        return X_pca_df, self.pca

    def apply_pls(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        n_components: Optional[int] = None,
        fit: bool = True
    ) -> Tuple[pd.DataFrame, PLSRegression]:
        """
        Apply Partial Least Squares (PLS) regression.

        Reduces 53 Google Trends terms to n_components PLS components
        while considering the target variable.

        Args:
            X: Input features (53 Google Trends terms)
            y: Target variable (tourism metric)
            n_components: Number of components (default from config: 3)
            fit: Whether to fit PLS (True for training)

        Returns:
            Tuple of (transformed DataFrame, PLS model)
        """
        if n_components is None:
            n_components = self.config.get('features.dimensionality_reduction.pls.n_components', 3)

        self.logger.info(f"Applying PLS with {n_components} components")

        # Scale features first
        X_scaled = self.scale_features(X, fit=fit)

        # Scale target
        y_scaled = (y - y.mean()) / y.std() if fit else y

        if fit:
            self.pls = PLSRegression(
                n_components=n_components,
                random_state=self.config.get('features.dimensionality_reduction.pls.random_state', 42)
            )
            self.pls.fit(X_scaled, y_scaled.values.reshape(-1, 1))
            X_pls = self.pls.transform(X_scaled)
        else:
            if self.pls is None:
                raise ValueError("PLS model not fitted yet. Call with fit=True first.")
            X_pls = self.pls.transform(X_scaled)

        self.logger.info(f"PLS model fitted")

        # Create DataFrame with component names
        X_pls_df = pd.DataFrame(
            X_pls,
            index=X.index,
            columns=[f'PLS{i+1}' for i in range(n_components)]
        )

        return X_pls_df, self.pls

    def calculate_feature_importance(
        self,
        pca_model: PCA,
        feature_names: List[str]
    ) -> Dict[str, float]:
        """
        Calculate feature importance from PCA loadings.

        Args:
            pca_model: Fitted PCA model
            feature_names: Names of original features

        Returns:
            Dictionary mapping features to importance scores
        """
        self.logger.info("Calculating feature importance from PCA loadings")

        # Sum absolute loadings across all components
        loadings = np.abs(pca_model.components_).sum(axis=0)

        # Normalize to sum to 1
        importance = loadings / loadings.sum()

        importance_dict = dict(zip(feature_names, importance))

        # Sort by importance
        sorted_importance = dict(
            sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)
        )

        self.logger.info(f"Top 5 important features: {list(sorted_importance.items())[:5]}")

        return sorted_importance

    def select_features(
        self,
        X: pd.DataFrame,
        importance: Optional[Dict[str, float]] = None,
        threshold: float = 0.01
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Select features based on importance threshold.

        Args:
            X: Features DataFrame
            importance: Feature importance dictionary
            threshold: Minimum importance threshold

        Returns:
            Tuple of (selected features DataFrame, selected feature names)
        """
        self.logger.info(f"Selecting features with importance > {threshold}")

        if importance is None:
            self.logger.warning("No importance scores provided, returning all features")
            return X, list(X.columns)

        selected_features = [
            feat for feat, imp in importance.items()
            if imp > threshold and feat in X.columns
        ]

        self.logger.info(f"Selected {len(selected_features)} features from {len(X.columns)}")

        return X[selected_features], selected_features

    def save_transformers(
        self,
        save_dir: str = 'models'
    ) -> None:
        """
        Save fitted transformers (scaler, PCA, PLS).

        Args:
            save_dir: Directory to save models
        """
        self.logger.info(f"Saving feature transformers to {save_dir}")

        save_joblib(self.scaler, f'{save_dir}/scaler.joblib')

        if self.pca is not None:
            save_joblib(self.pca, f'{save_dir}/pca_model.joblib')

        if self.pls is not None:
            save_joblib(self.pls, f'{save_dir}/pls_model.joblib')

        self.logger.info("Transformers saved successfully")

    def load_transformers(
        self,
        load_dir: str = 'models'
    ) -> None:
        """
        Load fitted transformers.

        Args:
            load_dir: Directory containing saved models
        """
        self.logger.info(f"Loading feature transformers from {load_dir}")

        try:
            self.scaler = load_joblib(f'{load_dir}/scaler.joblib')
            self.pca = load_joblib(f'{load_dir}/pca_model.joblib')
            self.pls = load_joblib(f'{load_dir}/pls_model.joblib')
            self.logger.info("Transformers loaded successfully")
        except Exception as e:
            self.logger.error(f"Error loading transformers: {e}")
            raise
