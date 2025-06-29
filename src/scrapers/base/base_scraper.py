import asyncio
import logging
from typing import AsyncIterator, Dict, Any, List, Optional
from abc import ABC, abstractmethod

from .scraper_interface import ScraperInterface, ScrapingConfig
from .scraper_strategy import ScraperStrategy, StaticScraperStrategy
from ...data.models import JobListing


class BaseScraper(ScraperInterface, ABC):
    """Base implementation for all job platform scrapers."""
    
    def __init__(
        self, 
        strategy: ScraperStrategy = None,
        max_retries: int = 3,
        rate_limit_delay: float = 1.0
    ):
        """
        Initialize the base scraper.
        
        Args:
            strategy: Scraping strategy to use (defaults to StaticScraperStrategy)
            max_retries: Maximum number of retry attempts
            rate_limit_delay: Delay between requests in seconds
        """
        self.strategy = strategy or StaticScraperStrategy()
        self.max_retries = max_retries
        self.rate_limit_delay = rate_limit_delay
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Rate limiting
        self._last_request_time = 0
        self._request_lock = asyncio.Lock()
    
    async def _apply_rate_limit(self):
        """Apply rate limiting to requests."""
        async with self._request_lock:
            import time
            current_time = time.time()
            time_since_last = current_time - self._last_request_time
            
            if time_since_last < self.rate_limit_delay:
                await asyncio.sleep(self.rate_limit_delay - time_since_last)
            
            self._last_request_time = time.time()
    
    async def _fetch_with_retry(self, url: str, **kwargs) -> str:
        """
        Fetch content with retry logic.
        
        Args:
            url: URL to fetch
            **kwargs: Additional arguments for the strategy
            
        Returns:
            Page content as string
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                await self._apply_rate_limit()
                content = await self.strategy.fetch_page(url, **kwargs)
                self.logger.info(f"Successfully fetched: {url}")
                return content
                
            except Exception as e:
                last_exception = e
                self.logger.warning(
                    f"Attempt {attempt + 1}/{self.max_retries} failed for {url}: {str(e)}"
                )
                
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    wait_time = (2 ** attempt) * self.rate_limit_delay
                    await asyncio.sleep(wait_time)
        
        self.logger.error(f"Failed to fetch {url} after {self.max_retries} attempts")
        raise last_exception
    
    async def _parse_with_strategy(self, content: str, parser_func) -> Dict[str, Any]:
        """
        Parse content using the current strategy.
        
        Args:
            content: Content to parse
            parser_func: Function to use for parsing
            
        Returns:
            Parsed data dictionary
        """
        try:
            return await self.strategy.parse_content(content, parser_func)
        except Exception as e:
            self.logger.error(f"Parsing failed: {str(e)}")
            raise
    
    @abstractmethod
    async def _build_listing_url(self, config: ScrapingConfig, page: int = 1) -> str:
        """Build URL for job listings page."""
        pass
    
    @abstractmethod
    async def _build_detail_url(self, job_id: str) -> str:
        """Build URL for job detail page."""
        pass
    
    @abstractmethod
    async def _parse_job_listing(self, soup_or_data) -> List[JobListing]:
        """Parse job listings from page content."""
        pass
    
    @abstractmethod
    async def _parse_job_detail(self, soup_or_data, job_id: str) -> Dict[str, Any]:
        """Parse job detail from page content."""
        pass
    
    async def get_job_listings(self, config: ScrapingConfig) -> AsyncIterator[Dict[str, Any]]:
        """
        Get job listings from the platform.
        
        Args:
            config: Scraping configuration
            
        Yields:
            Job listing dictionaries
        """
        page = 1
        total_jobs_found = 0
        
        while total_jobs_found < config.job_count:
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
                
                for job_listing in job_listings:
                    if total_jobs_found >= config.job_count:
                        break
                    
                    yield job_listing.to_dict()
                    total_jobs_found += 1
                
                page += 1
                
            except Exception as e:
                self.logger.error(f"Error fetching page {page}: {str(e)}")
                break
    
    async def get_job_details(self, job_id: str, job_url: str = None) -> Dict[str, Any]:
        """
        Get detailed information for a specific job.
        
        Args:
            job_id: Unique job identifier
            job_url: Optional job URL (will be built if not provided)
            
        Returns:
            Detailed job information dictionary
        """
        try:
            if not job_url:
                job_url = await self._build_detail_url(job_id)
            
            content = await self._fetch_with_retry(job_url)
            
            job_details = await self._parse_with_strategy(
                content,
                lambda soup_or_data: self._parse_job_detail(soup_or_data, job_id)
            )
            
            return job_details
            
        except Exception as e:
            self.logger.error(f"Error fetching job details for {job_id}: {str(e)}")
            return {"id": job_id, "error": str(e)}
    
    async def search_jobs(self, config: ScrapingConfig) -> AsyncIterator[Dict[str, Any]]:
        """
        Search for jobs based on criteria.
        
        Args:
            config: Search configuration
            
        Yields:
            Matching job dictionaries
        """
        # Default implementation delegates to get_job_listings
        # Individual scrapers can override for platform-specific search
        async for job in self.get_job_listings(config):
            yield job 