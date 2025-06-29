from typing import Dict, Type, Optional
from enum import Enum

from ..base.scraper_interface import ScraperInterface
from ..base.scraper_strategy import (
    ScraperStrategy, 
    StaticScraperStrategy, 
    DynamicScraperStrategy, 
    APIScraperStrategy
)
from ...data.models import Platform


class ScraperType(Enum):
    """Available scraper types."""
    JOBS_GE = "jobs_ge"
    CV_GE = "cv_ge"
    HR_GE = "hr_ge"
    INDEED = "indeed"
    LINKEDIN = "linkedin"
    GLASSDOOR = "glassdoor"
    STACK_OVERFLOW = "stack_overflow"


class ScraperFactory:
    """
    Factory class for creating appropriate scrapers for different platforms.
    Implements the Factory design pattern.
    """
    
    _scrapers: Dict[ScraperType, Type[ScraperInterface]] = {}
    
    @classmethod
    def register_scraper(cls, scraper_type: ScraperType, scraper_class: Type[ScraperInterface]):
        """
        Register a scraper class for a specific platform.
        
        Args:
            scraper_type: The type of scraper
            scraper_class: The scraper class to register
        """
        cls._scrapers[scraper_type] = scraper_class
    
    @classmethod
    def create_scraper(
        cls, 
        scraper_type: ScraperType, 
        strategy: Optional[ScraperStrategy] = None,
        **kwargs
    ) -> ScraperInterface:
        """
        Create a scraper instance for the specified platform.
        
        Args:
            scraper_type: Type of scraper to create
            strategy: Optional scraping strategy to use
            **kwargs: Additional arguments for scraper initialization
            
        Returns:
            Configured scraper instance
            
        Raises:
            ValueError: If scraper type is not supported
        """
        if scraper_type not in cls._scrapers:
            available_types = ", ".join([t.value for t in cls._scrapers.keys()])
            raise ValueError(
                f"Unsupported scraper type: {scraper_type.value}. "
                f"Available types: {available_types}"
            )
        
        scraper_class = cls._scrapers[scraper_type]
        return scraper_class(strategy=strategy, **kwargs)
    
    @classmethod
    def get_available_scrapers(cls) -> Dict[str, str]:
        """
        Get a dictionary of available scraper types and their descriptions.
        
        Returns:
            Dictionary mapping scraper type to description
        """
        descriptions = {
            ScraperType.JOBS_GE: "Georgian job platform Jobs.ge",
            ScraperType.CV_GE: "Georgian job platform CV.ge",
            ScraperType.INDEED: "International job platform Indeed",
            ScraperType.LINKEDIN: "Professional network LinkedIn Jobs",
            ScraperType.GLASSDOOR: "Company review and job platform Glassdoor",
            ScraperType.STACK_OVERFLOW: "Developer-focused Stack Overflow Jobs",
        }
        
        return {
            scraper_type.value: descriptions.get(scraper_type, "No description available")
            for scraper_type in cls._scrapers.keys()
        }
    
    @classmethod
    def create_strategy(cls, strategy_type: str, **kwargs) -> ScraperStrategy:
        """
        Create a scraping strategy.
        
        Args:
            strategy_type: Type of strategy ('static', 'dynamic', 'api')
            **kwargs: Strategy-specific configuration
            
        Returns:
            Configured strategy instance
        """
        strategy_mapping = {
            'static': StaticScraperStrategy,
            'dynamic': DynamicScraperStrategy,
            'api': APIScraperStrategy,
        }
        
        if strategy_type not in strategy_mapping:
            available_strategies = ", ".join(strategy_mapping.keys())
            raise ValueError(
                f"Unsupported strategy type: {strategy_type}. "
                f"Available strategies: {available_strategies}"
            )
        
        strategy_class = strategy_mapping[strategy_type]
        return strategy_class(**kwargs)


# Register available scrapers
def _register_default_scrapers():
    """Register all available scrapers with the factory."""
    # Import here to avoid circular imports
    from ..platforms.jobs_ge.jobs_ge_scraper import JobsGeScraper
    from ..platforms.cv_ge.cv_ge_scraper import CvGeScraper
    from ..platforms.hr_ge.hr_ge_scraper import HrGeScraper
    
    ScraperFactory.register_scraper(ScraperType.JOBS_GE, JobsGeScraper)
    ScraperFactory.register_scraper(ScraperType.CV_GE, CvGeScraper)
    ScraperFactory.register_scraper(ScraperType.HR_GE, HrGeScraper)
    
    # Additional scrapers can be registered here as they are implemented
    # ScraperFactory.register_scraper(ScraperType.INDEED, IndeedScraper)
    # ScraperFactory.register_scraper(ScraperType.LINKEDIN, LinkedInScraper)


# Auto-register scrapers when module is imported
_register_default_scrapers() 