"""
Plot Generator Module

Creates static plots using matplotlib and seaborn.
Used for reports and historical visualization.

Author: MEKKAOUI Brahim
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional, Tuple
from src.logger import get_logger

logger = get_logger(__name__)


class PlotGenerator:
    """
    Generate static plots for reports and analysis.

    Provides methods to create:
    - Time series plots
    - Heatmaps
    - Box plots
    - Distribution plots
    """

    def __init__(self, figsize: Tuple = (12, 6)):
        """
        Initialize plot generator.

        Args:
            figsize: Default figure size (width, height)
        """
        self.figsize = figsize
        self.logger = logger

        # Set style
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = figsize

    def plot_time_series(
        self,
        data: Dict[str, pd.Series],
        title: str = "Time Series",
        xlabel: str = "Date",
        ylabel: str = "Value",
        figsize: Optional[Tuple] = None
    ) -> plt.Figure:
        """
        Create time series plot.

        Args:
            data: Dictionary of series names to Series objects
            title: Plot title
            xlabel: X-axis label
            ylabel: Y-axis label
            figsize: Figure size

        Returns:
            Matplotlib figure object
        """
        figsize = figsize or self.figsize
        fig, ax = plt.subplots(figsize=figsize)

        for name, series in data.items():
            ax.plot(series.index, series.values, label=name, marker='o', alpha=0.7)

        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        return fig

    def plot_forecast(
        self,
        actual: pd.Series,
        forecast: pd.Series,
        ci_lower: Optional[pd.Series] = None,
        ci_upper: Optional[pd.Series] = None,
        title: str = "Forecast",
        figsize: Optional[Tuple] = None
    ) -> plt.Figure:
        """
        Create forecast plot with confidence intervals.

        Args:
            actual: Actual values
            forecast: Forecast values
            ci_lower: Lower confidence interval
            ci_upper: Upper confidence interval
            title: Plot title
            figsize: Figure size

        Returns:
            Matplotlib figure object
        """
        figsize = figsize or self.figsize
        fig, ax = plt.subplots(figsize=figsize)

        # Plot actual
        ax.plot(actual.index, actual.values, 'b-', label='Actual', linewidth=2)

        # Plot forecast
        ax.plot(forecast.index, forecast.values, 'r--', label='Forecast', linewidth=2)

        # Plot confidence intervals
        if ci_lower is not None and ci_upper is not None:
            ax.fill_between(
                ci_lower.index,
                ci_lower.values,
                ci_upper.values,
                alpha=0.2,
                color='red',
                label='95% CI'
            )

        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel('Date')
        ax.set_ylabel('Value')
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        return fig

    def plot_residuals(
        self,
        residuals: pd.Series,
        title: str = "Residuals",
        figsize: Optional[Tuple] = None
    ) -> plt.Figure:
        """
        Create residuals diagnostic plot.

        Args:
            residuals: Model residuals
            title: Plot title
            figsize: Figure size

        Returns:
            Matplotlib figure object
        """
        figsize = figsize or self.figsize
        fig, axes = plt.subplots(2, 2, figsize=figsize)

        # Time series plot
        axes[0, 0].plot(residuals.index, residuals.values)
        axes[0, 0].set_title('Residuals Over Time')
        axes[0, 0].set_ylabel('Residuals')
        axes[0, 0].grid(True, alpha=0.3)

        # Histogram
        axes[0, 1].hist(residuals, bins=30, edgecolor='black')
        axes[0, 1].set_title('Residuals Distribution')
        axes[0, 1].set_xlabel('Residuals')
        axes[0, 1].set_ylabel('Frequency')

        # Q-Q plot
        from scipy import stats
        stats.probplot(residuals, dist="norm", plot=axes[1, 0])
        axes[1, 0].set_title('Q-Q Plot')

        # ACF-like plot (correlation)
        from pandas.plotting import autocorrelation_plot
        autocorrelation_plot(residuals, ax=axes[1, 1])
        axes[1, 1].set_title('Autocorrelation')

        fig.suptitle(title, fontsize=14, fontweight='bold')
        plt.tight_layout()
        return fig

    def plot_comparison(
        self,
        actual: pd.Series,
        predictions: Dict[str, pd.Series],
        title: str = "Model Comparison",
        figsize: Optional[Tuple] = None
    ) -> plt.Figure:
        """
        Compare multiple model predictions.

        Args:
            actual: Actual values
            predictions: Dictionary of model names to predictions
            title: Plot title
            figsize: Figure size

        Returns:
            Matplotlib figure object
        """
        figsize = figsize or self.figsize
        fig, ax = plt.subplots(figsize=figsize)

        # Plot actual
        ax.plot(actual.index, actual.values, 'k-', label='Actual', linewidth=2)

        # Plot predictions
        colors = ['b', 'r', 'g', 'orange', 'purple']
        for (name, pred), color in zip(predictions.items(), colors):
            ax.plot(pred.index, pred.values, '--', label=name, color=color, linewidth=1.5)

        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel('Date')
        ax.set_ylabel('Value')
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        return fig

    def plot_correlation_heatmap(
        self,
        data: pd.DataFrame,
        title: str = "Correlation Matrix",
        figsize: Optional[Tuple] = None
    ) -> plt.Figure:
        """
        Create correlation heatmap.

        Args:
            data: DataFrame with numeric columns
            title: Plot title
            figsize: Figure size

        Returns:
            Matplotlib figure object
        """
        figsize = figsize or self.figsize
        fig, ax = plt.subplots(figsize=figsize)

        # Calculate correlation
        corr = data.corr()

        # Create heatmap
        sns.heatmap(corr, annot=True, fmt='.2f', cmap='coolwarm', center=0,
                   square=True, ax=ax, cbar_kws={'label': 'Correlation'})

        ax.set_title(title, fontsize=14, fontweight='bold')
        plt.tight_layout()
        return fig

    @staticmethod
    def save_figure(fig: plt.Figure, filepath: str) -> None:
        """
        Save figure to file.

        Args:
            fig: Matplotlib figure
            filepath: Path to save
        """
        fig.savefig(filepath, dpi=300, bbox_inches='tight')
        logger.info(f"Figure saved: {filepath}")
        plt.close(fig)
