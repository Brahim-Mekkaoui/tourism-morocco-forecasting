"""
Features Module

Feature engineering and dimensionality reduction.
- Google Trends aggregation
- PCA/ACP dimensionality reduction
- PLS transformation
- Lead/lag analysis

Author: MEKKAOUI Brahim
"""

from src.features.google_trends import GoogleTrendsFeatures
from src.features.engineering import FeatureEngineer

__all__ = [
    "GoogleTrendsFeatures",
    "FeatureEngineer",
]
