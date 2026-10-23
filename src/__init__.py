"""
Tourism Morocco Forecasting & Intelligence Dashboard
Core module package

Author: MEKKAOUI Brahim
Supervisor: KHTIRA Rachida
Institution: ESI + DEPF
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "MEKKAOUI Brahim"

from src.config import Config
from src.logger import get_logger

# Initialize global logger
logger = get_logger(__name__)

__all__ = [
    "Config",
    "get_logger",
    "logger",
]
