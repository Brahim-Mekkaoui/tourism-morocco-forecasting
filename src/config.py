"""
Configuration Management Module

Loads and manages application configuration from YAML files.
Provides singleton Config instance for consistent configuration access.

Author: MEKKAOUI Brahim
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from functools import lru_cache


class Config:
    """
    Configuration manager for Tourism Morocco Forecasting Dashboard.

    Loads configuration from YAML files and provides access to settings
    through a dict-like interface.

    Attributes:
        config_dir (Path): Directory containing configuration files
        main_config (Dict): Main configuration dictionary
        google_trends_terms (Dict): Google Trends search terms
    """

    _instance = None  # Singleton instance

    def __new__(cls):
        """Implement singleton pattern for Config."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize configuration from YAML files."""
        if self._initialized:
            return

        self.config_dir = Path(__file__).parent.parent / "config"
        self.main_config = {}
        self.google_trends_terms = {}

        self._load_config()
        self._initialized = True

    def _load_config(self) -> None:
        """Load configuration files from config directory."""
        config_file = self.config_dir / "config.yaml"
        terms_file = self.config_dir / "google_trends_terms.yaml"

        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                self.main_config = yaml.safe_load(f) or {}
        else:
            raise FileNotFoundError(f"Configuration file not found: {config_file}")

        if terms_file.exists():
            with open(terms_file, 'r', encoding='utf-8') as f:
                self.google_trends_terms = yaml.safe_load(f) or {}

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-separated key path.

        Args:
            key: Dot-separated path to configuration value (e.g., 'models.sarima.order')
            default: Default value if key not found

        Returns:
            Configuration value or default

        Example:
            >>> config = Config()
            >>> config.get('models.sarima.order')
            [1, 1, 1]
        """
        keys = key.split('.')
        value = self.main_config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def get_nested(self, *keys: str, default: Any = None) -> Any:
        """
        Get nested configuration value.

        Args:
            *keys: Variable number of keys for nested access
            default: Default value if path not found

        Returns:
            Configuration value or default

        Example:
            >>> config = Config()
            >>> config.get_nested('models', 'sarima', 'order')
            [1, 1, 1]
        """
        return self.get('.'.join(keys), default)

    def __getitem__(self, key: str) -> Any:
        """Allow dict-like access to configuration."""
        value = self.get(key)
        if value is None:
            raise KeyError(f"Configuration key not found: {key}")
        return value

    def get_google_trends_terms(self) -> Dict[str, list]:
        """
        Get all Google Trends search terms organized by language.

        Returns:
            Dictionary with language keys and lists of search terms
        """
        return self.google_trends_terms

    def get_terms_flat_list(self) -> list:
        """
        Get flattened list of all Google Trends terms.

        Returns:
            Flat list of all 53 search terms across all languages
        """
        terms = []
        for lang in ['english', 'french', 'spanish', 'german']:
            if lang in self.google_trends_terms:
                lang_data = self.google_trends_terms[lang]
                if isinstance(lang_data, dict):
                    for category in lang_data.values():
                        if isinstance(category, list):
                            terms.extend(category)

        # Add additional terms
        if 'additional' in self.google_trends_terms:
            for term in self.google_trends_terms['additional'].values():
                terms.append(term)

        return terms

    def to_dict(self) -> Dict:
        """Get entire configuration as dictionary."""
        return self.main_config.copy()

    def __repr__(self) -> str:
        """String representation of Config."""
        return f"Config(project={self.get('project.name')}, environment={self.get('environment')})"


# Singleton instance
_config = None


def get_config() -> Config:
    """
    Get or create singleton Config instance.

    Returns:
        Config singleton instance

    Example:
        >>> config = get_config()
        >>> config.get('models.sarima.order')
    """
    global _config
    if _config is None:
        _config = Config()
    return _config
