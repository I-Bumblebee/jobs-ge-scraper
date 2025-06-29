from abc import ABC, abstractmethod
from typing import AsyncIterator, List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ScrapingConfig:
    """Configuration for scraping operations."""
    job_count: int = 20
    location_id: Optional[str] = None
    category_id: Optional[str] = None
    query: Optional[str] = None
    has_salary: bool = False
    max_concurrent: int = 5
    batch_size: int = 10
    locale: str = "en"


class ScraperInterface(ABC):
    """Interface that all job platform scrapers must implement."""
    
    @abstractmethod
    async def get_job_listings(self, config: ScrapingConfig) -> AsyncIterator[Dict[str, Any]]:
        """
        Get job listings from the platform.
        
        Args:
            config: Scraping configuration
            
        Yields:
            Job listing dictionaries
        """
        pass
    
    @abstractmethod
    async def get_job_details(self, job_id: str, job_url: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific job.
        
        Args:
            job_id: Unique job identifier
            job_url: URL to the job detail page
            
        Returns:
            Detailed job information dictionary
        """
        pass
    
    @abstractmethod
    async def search_jobs(self, config: ScrapingConfig) -> AsyncIterator[Dict[str, Any]]:
        """
        Search for jobs based on criteria.
        
        Args:
            config: Search configuration
            
        Yields:
            Matching job dictionaries
        """
        pass
    
    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Return the name of the platform."""
        pass
    
    @property
    @abstractmethod
    def supported_locations(self) -> Dict[str, str]:
        """Return supported location mappings."""
        pass
    
    @property
    @abstractmethod
    def supported_categories(self) -> Dict[str, str]:
        """Return supported category mappings."""
        pass 