"""
Data Loaders Module

Loads data from various sources:
- MANAR (Moroccan Ministry of Tourism) Excel files
- Google Trends API via pytrends

Author: MEKKAOUI Brahim
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from src.logger import get_logger
from src.config import get_config
from src.utils import ensure_directory, validate_dataframe

logger = get_logger(__name__)


class MANARDataLoader:
    """
    Loads tourism data from MANAR Excel files.

    The MANAR (Ministry of Tourism) provides 13 Excel files with:
    - Tourist arrivals (by country, category)
    - Tourism receipts
    - Hotel capacity
    - Nights spent

    Attributes:
        data_path (Path): Directory containing MANAR Excel files
        files_mapping (Dict): Maps data types to file names
    """

    # Mapping of data types to Excel file names
    FILES_MAPPING = {
        'arrivals_total': 'Arrivées_des_touristes.xlsx',
        'arrivals_monthly_cumulative': 'Arrivées_des_touristes_mensuel_cumulé_en_nombre.xlsx',
        'arrivals_by_country': 'Arrivées_des_touristes_par_pays.xlsx',
        'arrivals_foreign_stay': 'Arrivés_de_touristes_étrangers_de_Séjour_TES.xlsx',
        'hotel_capacity': 'Capacité_en_lits_des_hôtels_homologués.xlsx',
        'tourist_flow_by_country': 'Flux_de_touristes_par_pays.xlsx',
        'nights_monthly': 'Nuitées_touristique.xlsx',
        'nights_annual': 'Nuitées_touristiques_Annuel.xlsx',
        'nights_by_category': 'Nuitées_touristiques_par_catégorie.xlsx',
        'nights_by_country': 'Nuitées_touristiques_par_pays.xlsx',
        'receipts_total': 'Recettes_touristiques.xlsx',
        'receipts_monthly_cumulative': 'Recettes_touristiques_mensuel_cumulé.xlsx',
        'receipts_by_country': 'Recettes_touristiques_par_pays.xlsx',
    }

    def __init__(self, data_path: Optional[str] = None):
        """
        Initialize MANAR data loader.

        Args:
            data_path: Path to directory containing MANAR Excel files
                      If None, uses path from config
        """
        if data_path is None:
            config = get_config()
            data_path = config.get('data.manar_path', 'data/manar')

        self.data_path = Path(data_path)
        logger.info(f"Initialized MANARDataLoader with path: {self.data_path}")

    def load_arrivals(self) -> pd.DataFrame:
        """
        Load total tourist arrivals data.

        Returns:
            DataFrame with tourist arrivals data
        """
        return self._load_file('arrivals_total')

    def load_arrivals_by_country(self) -> pd.DataFrame:
        """Load arrivals broken down by country."""
        return self._load_file('arrivals_by_country')

    def load_arrivals_foreign_stay(self) -> pd.DataFrame:
        """Load foreign tourists staying in Morocco (TES)."""
        return self._load_file('arrivals_foreign_stay')

    def load_receipts(self) -> pd.DataFrame:
        """Load total tourism receipts."""
        return self._load_file('receipts_total')

    def load_receipts_by_country(self) -> pd.DataFrame:
        """Load receipts broken down by country."""
        return self._load_file('receipts_by_country')

    def load_nights(self) -> pd.DataFrame:
        """Load nights spent by tourists."""
        return self._load_file('nights_monthly')

    def load_nights_by_country(self) -> pd.DataFrame:
        """Load nights broken down by country."""
        return self._load_file('nights_by_country')

    def load_hotel_capacity(self) -> pd.DataFrame:
        """Load hotel bed capacity."""
        return self._load_file('hotel_capacity')

    def load_all(self) -> Dict[str, pd.DataFrame]:
        """
        Load all available MANAR data.

        Returns:
            Dictionary mapping data types to DataFrames
        """
        data = {}
        for data_type in self.FILES_MAPPING.keys():
            try:
                data[data_type] = self._load_file(data_type)
            except Exception as e:
                logger.warning(f"Failed to load {data_type}: {e}")

        logger.info(f"Loaded {len(data)} datasets from MANAR")
        return data

    def _load_file(self, data_type: str) -> pd.DataFrame:
        """
        Load a specific Excel file.

        Args:
            data_type: Type of data to load (key in FILES_MAPPING)

        Returns:
            Loaded DataFrame

        Raises:
            ValueError: If data_type not recognized
            FileNotFoundError: If file not found
        """
        if data_type not in self.FILES_MAPPING:
            raise ValueError(f"Unknown data type: {data_type}")

        filename = self.FILES_MAPPING[data_type]
        filepath = self.data_path / filename

        if not filepath.exists():
            raise FileNotFoundError(f"Data file not found: {filepath}")

        logger.info(f"Loading {data_type} from {filename}")

        try:
            df = pd.read_excel(filepath)
            logger.info(f"Successfully loaded {data_type}: {df.shape}")
            return df
        except Exception as e:
            logger.error(f"Error loading {data_type}: {e}")
            raise

    def get_available_files(self) -> List[str]:
        """
        Get list of available data files in the MANAR directory.

        Returns:
            List of available Excel filenames
        """
        if not self.data_path.exists():
            logger.warning(f"Data path does not exist: {self.data_path}")
            return []

        excel_files = list(self.data_path.glob('*.xlsx'))
        available = [f.name for f in excel_files]
        logger.info(f"Found {len(available)} Excel files in {self.data_path}")
        return available


class GoogleTrendsLoader:
    """
    Loads data from Google Trends API using pytrends library.

    Fetches search interest data for tourism-related terms in multiple languages.
    Implements retry logic and rate limiting.
    """

    def __init__(self):
        """Initialize Google Trends loader."""
        from pytrends.request import TrendReq

        config = get_config()
        self.pytrends = TrendReq(
            hl=config.get('google_trends.api.language', 'all'),
            tz=0,  # UTC
            timeout=(self._get_timeout(), self._get_timeout()),
            retries=config.get('google_trends.api.retry_attempts', 3),
            backoff_factor=1.0,
        )

        self.config = config
        self.logger = logger

    def _get_timeout(self) -> int:
        """Get timeout from config."""
        return self.config.get('google_trends.api.timeout', 30)

    def load_term_data(
        self,
        keywords: List[str],
        timeframe: str = '',
        geo: str = 'MA',
        cat: int = 0,
        gprop: str = ''
    ) -> pd.DataFrame:
        """
        Fetch Google Trends data for specified keywords.

        Args:
            keywords: List of search terms
            timeframe: Timeframe string (e.g., '2020-01-01 2026-07-31')
            geo: Geographic region code
            cat: Category code
            gprop: Google property (web, images, news, youtube)

        Returns:
            DataFrame with interest over time
        """
        if not timeframe:
            timeframe = self.config.get('google_trends.api.timeframe')

        try:
            self.logger.info(f"Fetching Google Trends data for {len(keywords)} keywords")

            self.pytrends.build_payload(
                keywords=keywords,
                timeframe=timeframe,
                geo=geo,
                cat=cat,
                gprop=gprop
            )

            df = self.pytrends.interest_over_time()

            # Remove 'isPartial' column if present
            if 'isPartial' in df.columns:
                df = df.drop('isPartial', axis=1)

            self.logger.info(f"Retrieved {len(df)} time periods for {len(keywords)} keywords")
            return df

        except Exception as e:
            self.logger.error(f"Error fetching Google Trends data: {e}")
            raise

    def load_all_terms(self) -> pd.DataFrame:
        """
        Load Google Trends data for all configured search terms.

        Returns:
            Combined DataFrame with all terms data
        """
        config = get_config()
        terms = config.get_terms_flat_list()

        self.logger.info(f"Loading Google Trends data for {len(terms)} multilingual terms")

        timeframe = config.get('google_trends.api.timeframe')

        return self.load_term_data(
            keywords=terms,
            timeframe=timeframe,
            geo='MA'  # Morocco
        )


class DataLoader:
    """
    Main data loader orchestrating loading from all sources.

    Combines MANAR and Google Trends data into unified dataset.
    """

    def __init__(self):
        """Initialize main data loader."""
        self.manar_loader = MANARDataLoader()
        self.google_trends_loader = GoogleTrendsLoader()
        self.logger = logger

    def load_all_data(self) -> Tuple[Dict[str, pd.DataFrame], pd.DataFrame]:
        """
        Load all available data.

        Returns:
            Tuple of (MANAR data dict, Google Trends DataFrame)
        """
        self.logger.info("Loading complete dataset")

        # Load MANAR data
        manar_data = self.manar_loader.load_all()

        # Load Google Trends data
        try:
            google_trends = self.google_trends_loader.load_all_terms()
        except Exception as e:
            self.logger.warning(f"Failed to load Google Trends: {e}")
            google_trends = pd.DataFrame()

        return manar_data, google_trends
