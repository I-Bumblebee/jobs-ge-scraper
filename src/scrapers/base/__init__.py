"""
Base classes and interfaces for all scrapers.
"""

from .scraper_interface import ScraperInterface
from .base_scraper import BaseScraper
from .scraper_strategy import ScraperStrategy

__all__ = ['ScraperInterface', 'BaseScraper', 'ScraperStrategy'] 