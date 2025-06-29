"""
Scrapers package for multi-platform job scraping.
"""

from .factory.scraper_factory import ScraperFactory
from .base.scraper_interface import ScraperInterface

__all__ = ['ScraperFactory', 'ScraperInterface'] 