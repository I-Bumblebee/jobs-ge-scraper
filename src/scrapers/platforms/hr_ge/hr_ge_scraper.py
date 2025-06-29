from typing import Dict, List, Optional, AsyncIterator, Any
import re
from urllib.parse import urlencode

from ...base.base_scraper import BaseScraper
from ...base.scraper_interface import ScrapingConfig
from ...base.scraper_strategy import DynamicScraperStrategy
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
from .hr_ge_parser import HrGeParser


class HrGeScraper(BaseScraper):
    """HR.ge platform scraper implementation using Selenium for Angular content."""
    
    # Platform-specific constants
    BASE_URL = "https://www.hr.ge"
    SEARCH_PAGE_URL = "https://www.hr.ge/search-posting"
    
    # HR.ge doesn't have explicit category/location filtering in the URL
    # but we can still support basic configurations for future use
    CATEGORIES = {
        "All Categories": "",
        "Administration": "admin",
        "Finance": "finance", 
        "Sales": "sales",
        "IT/Programming": "it",
        "Medicine": "medicine",
        "Education": "education",
        "Marketing": "marketing",
        "Other": "other"
    }
    
    LOCATIONS = {
        "Any Location": "",
        "თბილისი": "tbilisi",
        "ბათუმი": "batumi", 
        "ქუთაისი": "kutaisi",
        "რუსთავი": "rustavi",
        "ფოთი": "poti",
        "გორი": "gori",
        "Other": "other"
    }
    
    def __init__(self, strategy=None, **kwargs):
        """Initialize the HR.ge scraper with Selenium strategy."""
        super().__init__(
            strategy=strategy or DynamicScraperStrategy(max_concurrent=2, timeout=30, headless=True), 
            **kwargs
        )
        self.parser = HrGeParser()
    
    @property
    def platform_name(self) -> str:
        """Return the platform name."""
        return "HR.ge"
    
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
        # HR.ge uses Angular pagination, the main search page loads all jobs dynamically
        return self.SEARCH_PAGE_URL
    
    async def _build_detail_url(self, job_id: str) -> str:
        """Build URL for job detail page."""
        # HR.ge URLs are like: /announcement/{id}/title-slug
        return f"{self.BASE_URL}/announcement/{job_id}"
    
    async def get_job_details(self, job_id: str, job_url: str = None) -> Dict[str, Any]:
        """
        Get detailed information for a specific job.
        Override to handle HR.ge URL format and use Selenium.
        """
        try:
            # Use provided URL or build detail URL
            if job_url and job_url.startswith("http"):
                detail_url = job_url
            elif job_url:
                detail_url = f"{self.BASE_URL}{job_url}"
            else:
                detail_url = await self._build_detail_url(job_id)
            
            # Fetch the job detail page using Selenium with wait for content
            content = await self._fetch_with_retry(
                detail_url,
                wait_for_element="div.tile.tile--with-logo",
                execute_js="window.scrollTo(0, document.body.scrollHeight);"
            )
            
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
                "url": job_url or detail_url
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
        # HR.ge URLs: /announcement/417493/title-slug
        match = re.search(r"/announcement/(\d+)", url)
        return match.group(1) if match else None
    
    async def _scroll_and_load_jobs(self, driver, max_jobs: int) -> None:
        """Scroll down to load more jobs dynamically."""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.wait import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import time
        
        last_height = driver.execute_script("return document.body.scrollHeight")
        jobs_loaded = 0
        
        while jobs_loaded < max_jobs:
            # Scroll down to the bottom
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait for new content to load
            time.sleep(2)
            
            # Check current number of job items
            try:
                job_items = driver.find_elements(By.TAG_NAME, "app-announcement-item")
                jobs_loaded = len(job_items)
                
                self.logger.info(f"Loaded {jobs_loaded} jobs so far...")
                
                # Check if page height changed (indicating new content loaded)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    # No more content to load
                    break
                last_height = new_height
                
            except Exception as e:
                self.logger.warning(f"Error checking job count: {str(e)}")
                break
            
            # Prevent infinite scrolling
            if jobs_loaded > max_jobs * 2:
                break
    
    async def get_job_listings(self, config: ScrapingConfig) -> AsyncIterator[Dict[str, Any]]:
        """
        Get job listings from HR.ge using Selenium.
        Override to handle Angular dynamic content loading.
        """
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.wait import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        total_jobs_found = 0
        
        try:
            # Setup Chrome options for Selenium
            options = Options()
            if hasattr(self.strategy, 'headless') and self.strategy.headless:
                options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            driver = webdriver.Chrome(options=options)
            
            try:
                # Navigate to the search page
                url = await self._build_listing_url(config)
                driver.get(url)
                
                # Wait for the page to load and Angular to render
                wait = WebDriverWait(driver, 30)
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "app-announcement-item")))
                
                # Scroll and load more jobs if needed
                await self._scroll_and_load_jobs(driver, config.job_count)
                
                # Get the page source after Angular has rendered
                content = driver.page_source
                
                # Parse the content using our parser
                job_listings = await self._parse_with_strategy(
                    content, 
                    self._parse_job_listing
                )
                
                if not job_listings:
                    self.logger.info("No jobs found on HR.ge")
                    return
                
                # Filter jobs based on config if needed
                filtered_jobs = self._filter_jobs(job_listings, config)
                
                for job_listing in filtered_jobs:
                    if total_jobs_found >= config.job_count:
                        break
                    
                    yield job_listing.to_dict()
                    total_jobs_found += 1
                
            finally:
                driver.quit()
                
        except Exception as e:
            self.logger.error(f"Error fetching HR.ge listings: {str(e)}")
            raise
    
    def _filter_jobs(self, job_listings: List[JobListing], config: ScrapingConfig) -> List[JobListing]:
        """Filter job listings based on configuration."""
        filtered = []
        
        for job in job_listings:
            # Basic filtering - can be enhanced based on HR.ge structure
            include_job = True
            
            # Location filtering (basic text matching)
            if config.location_id and config.location_id != "":
                location_text = job.location.city.lower() if job.location.city else ""
                if config.location_id.lower() not in location_text:
                    include_job = False
            
            # Query filtering (search in title)
            if config.query:
                if config.query.lower() not in job.title.lower():
                    include_job = False
            
            if include_job:
                filtered.append(job)
        
        return filtered
    
    async def search_jobs(self, config: ScrapingConfig) -> AsyncIterator[Dict[str, Any]]:
        """
        Search for jobs on HR.ge.
        Since HR.ge doesn't have advanced search in URL, we use the same as get_job_listings.
        """
        async for job in self.get_job_listings(config):
            yield job 