from typing import Dict, List, Optional
import re
from urllib.parse import urlencode

from ...base.base_scraper import BaseScraper
from ...base.scraper_interface import ScrapingConfig
from ...base.scraper_strategy import StaticScraperStrategy
from ....data.models import (
    JobListing, 
    JobDetails, 
    Company, 
    JobMetadata, 
    JobDates, 
    Location, 
    Salary,
    Platform
)
from .jobs_ge_parser import JobsGeParser


class JobsGeScraper(BaseScraper):
    """Jobs.ge platform scraper implementation."""
    
    # Platform-specific constants
    BASE_URL = "https://jobs.ge"
    PAGE_SIZE = 300
    
    # Jobs.ge specific categories mapping
    CATEGORIES = {
        "All Categories": "",
        "Administration/Management": "1",
        "Finance, Statistics": "3",
        "Sales/Procurement": "2",
        "PR/Marketing": "4",
        "General Technical Staff": "18",
        "Logistics/Transport/Distribution": "5",
        "Construction/Repair": "11",
        "Cleaning": "16",
        "Security/Safety": "17",
        "IT/Programming": "6",
        "Media/Publishing": "13",
        "Education": "12",
        "Law": "7",
        "Medicine/Pharmacy": "8",
        "Beauty/Fashion": "14",
        "Food": "10",
        "Other": "9"
    }
    
    # Jobs.ge specific locations mapping
    LOCATIONS = {
        "Any Location": "",
        "Tbilisi": "1",
        "Abkhazeti AR": "15",
        "Adjara AR": "14",
        "Guria": "9",
        "Imereti": "8",
        "Kakheti": "3",
        "Kvemo Kartli": "5",
        "Mtskheta-Mtianeti": "4",
        "Racha-Lechkhumi, Lw. Svaneti": "12",
        "Samegrelo-Zemo Svaneti": "13",
        "Samtskhe-Javakheti": "7",
        "Shida Kartli": "6",
        "Abroad": "16",
        "Remote": "17"
    }
    
    def __init__(self, strategy=None, **kwargs):
        """Initialize the Jobs.ge scraper."""
        super().__init__(
            strategy=strategy or StaticScraperStrategy(), 
            **kwargs
        )
        self.parser = JobsGeParser()
    
    @property
    def platform_name(self) -> str:
        """Return the platform name."""
        return "Jobs.ge"
    
    @property
    def supported_locations(self) -> Dict[str, str]:
        """Return supported location mappings."""
        return self.LOCATIONS.copy()
    
    @property
    def supported_categories(self) -> Dict[str, str]:
        """Return supported category mappings."""
        return self.CATEGORIES.copy()
    
    async def _build_listing_url(self, config: ScrapingConfig, page: int = 1) -> str:
        """Build URL for job listings page."""
        base_url = f"{self.BASE_URL}/{config.locale}"
        
        params = {"page": page}
        
        if config.category_id:
            params["cid"] = config.category_id
        
        if config.location_id:
            params["lid"] = config.location_id
        
        if config.query:
            params["q"] = config.query
        
        if config.has_salary:
            params["has_salary"] = "1"
        
        return f"{base_url}?{urlencode(params)}"
    
    async def _build_detail_url(self, job_id: str) -> str:
        """Build URL for job detail page."""
        return f"{self.BASE_URL}/ge/?view=jobs&id={job_id}"
    
    async def _parse_job_listing(self, soup) -> List[JobListing]:
        """Parse job listings from page content."""
        return self.parser.parse_job_listings(soup)
    
    async def _parse_job_detail(self, soup, job_id: str) -> Dict:
        """Parse job detail from page content."""
        return self.parser.parse_job_detail(soup, job_id)
    
    def _extract_job_id(self, url: Optional[str]) -> Optional[str]:
        """Extract job ID from URL."""
        if not url:
            return None
        match = re.search(r"id=(\d+)", url)
        return match.group(1) if match else None 