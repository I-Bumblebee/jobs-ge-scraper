from typing import Dict, List, Optional, AsyncIterator, Any
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
from .cv_ge_parser import CvGeParser


class CvGeScraper(BaseScraper):
    """CV.ge platform scraper implementation."""
    
    # Platform-specific constants
    BASE_URL = "https://www.cv.ge"
    MAX_PAGES = 24  # CV.ge has 24 pages total according to user
    
    # CV.ge doesn't have explicit category/location filtering in the URL
    # but we can still support basic configurations
    CATEGORIES = {
        "All Categories": "",
        # CV.ge uses Georgian categories, but for simplicity we'll keep it general
        "Administration": "admin",
        "Finance": "finance", 
        "Sales": "sales",
        "IT/Programming": "it",
        "Medicine": "medicine",
        "Education": "education",
        "Other": "other"
    }
    
    LOCATIONS = {
        "Any Location": "",
        "თბილისი": "tbilisi",
        "ბათუმი": "batumi", 
        "ქუთაისი": "kutaisi",
        "რუსთავი": "rustavi",
        "Other": "other"
    }
    
    def __init__(self, strategy=None, **kwargs):
        """Initialize the CV.ge scraper."""
        super().__init__(
            strategy=strategy or StaticScraperStrategy(), 
            **kwargs
        )
        self.parser = CvGeParser()
    
    @property
    def platform_name(self) -> str:
        """Return the platform name."""
        return "CV.ge"
    
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
        # CV.ge uses simple pagination: /announcements/all?page=N
        if page <= 1:
            return f"{self.BASE_URL}/announcements/all"
        else:
            return f"{self.BASE_URL}/announcements/all?page={page}"
    
    async def _build_detail_url(self, job_id: str) -> str:
        """Build URL for job detail page."""
        # CV.ge URLs are like: /announcement/{id}/title-slug
        # Since we might not have the title slug, we'll construct basic URL
        return f"{self.BASE_URL}/announcement/{job_id}"
    
    async def get_job_details(self, job_id: str, job_url: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific job.
        Override to handle CV.ge URL format properly.
        """
        try:
            # Ensure we have an absolute URL
            detail_url = job_url
            if not detail_url.startswith("http"):
                detail_url = f"{self.BASE_URL}{detail_url}"
            
            # Fetch the job detail page
            content = await self._fetch_with_retry(detail_url)
            
            # Parse the job detail
            job_detail = await self._parse_with_strategy(
                content, 
                lambda soup: self._parse_job_detail(soup, job_id)
            )
            
            return job_detail
            
        except Exception as e:
            self.logger.error(f"Error fetching job details for {job_id}: {str(e)}")
            return {
                "id": job_id,
                "error": str(e),
                "url": job_url
            }
    
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
        # CV.ge URLs: /announcement/417196/title-slug
        match = re.search(r"/announcement/(\d+)", url)
        return match.group(1) if match else None
    
    async def get_job_listings(self, config: ScrapingConfig) -> AsyncIterator[Dict[str, Any]]:
        """
        Get job listings from CV.ge.
        Override to handle the fixed 24-page structure of CV.ge.
        """
        
        page = 1
        total_jobs_found = 0
        
        while total_jobs_found < config.job_count and page <= self.MAX_PAGES:
            try:
                url = await self._build_listing_url(config, page)
                content = await self._fetch_with_retry(url)
                
                job_listings = await self._parse_with_strategy(
                    content, 
                    self._parse_job_listing
                )
                
                if not job_listings:
                    self.logger.info(f"No more jobs found on page {page}")
                    break
                
                # Filter jobs based on config if needed
                filtered_jobs = self._filter_jobs(job_listings, config)
                
                for job_listing in filtered_jobs:
                    if total_jobs_found >= config.job_count:
                        break
                    
                    yield job_listing.to_dict()
                    total_jobs_found += 1
                
                page += 1
                
                # Apply rate limiting
                await self._apply_rate_limit()
                
            except Exception as e:
                self.logger.error(f"Error fetching CV.ge page {page}: {str(e)}")
                break
    
    def _filter_jobs(self, job_listings: List[JobListing], config: ScrapingConfig) -> List[JobListing]:
        """Filter job listings based on configuration."""
        filtered = []
        
        for job in job_listings:
            # Basic filtering - can be enhanced based on CV.ge structure
            include_job = True
            
            # Location filtering (basic text matching)
            if config.location_id and config.location_id != "":
                location_text = job.location.city.lower() if job.location.city else ""
                if config.location_id.lower() not in location_text:
                    include_job = False
            
            # Category filtering (would require job description analysis for CV.ge)
            # For now, we'll include all jobs since CV.ge doesn't have URL-based category filtering
            
            # Query filtering (search in title)
            if config.query:
                if config.query.lower() not in job.title.lower():
                    include_job = False
            
            if include_job:
                filtered.append(job)
        
        return filtered
    
    async def search_jobs(self, config: ScrapingConfig) -> AsyncIterator[Dict[str, Any]]:
        """
        Search for jobs on CV.ge.
        Since CV.ge doesn't have advanced search in URL, we use the same as get_job_listings.
        """
        async for job in self.get_job_listings(config):
            yield job 