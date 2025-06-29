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
from .ss_ge_parser import SsGeParser


class SsGeScraper(BaseScraper):
    """jobs.ss.ge platform scraper implementation using Selenium for dynamic content."""
    
    # Platform-specific constants
    BASE_URL = "https://jobs.ss.ge"
    HOME_PAGE_URL = "https://jobs.ss.ge/ka/l/vacancies"  # Jobs listing page with pagination
    
    # SS.ge supports pagination
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
        """Initialize the jobs.ss.ge scraper with Selenium strategy."""
        super().__init__(
            strategy=strategy or DynamicScraperStrategy(max_concurrent=2, timeout=30, headless=True), 
            **kwargs
        )
        self.parser = SsGeParser()
    
    @property
    def platform_name(self) -> str:
        """Return the platform name."""
        return "jobs.ss.ge"
    
    @property
    def supported_locations(self) -> Dict[str, str]:
        """Return supported location mappings."""
        return self.LOCATIONS.copy()
    
    @property
    def supported_categories(self) -> Dict[str, str]:
        """Return supported category mappings."""
        return self.CATEGORIES.copy()
    
    async def _build_listing_url(self, config: ScrapingConfig, page: int = 1) -> str:
        """Build URL for job listings - using pagination."""
        # jobs.ss.ge uses pagination: ?page=2, ?page=3, etc.
        if page == 1:
            return self.HOME_PAGE_URL
        else:
            return f"{self.HOME_PAGE_URL}?page={page}"
    
    async def _build_detail_url(self, job_id: str) -> str:
        """Build URL for job detail page."""
        # jobs.ss.ge URLs format needs to be determined from actual job URLs
        return f"{self.BASE_URL}/ka/l/vacancies/{job_id}"
    
    async def get_job_details(self, job_id: str, job_url: str = None) -> Dict[str, Any]:
        """
        Get detailed information for a specific job.
        Override to handle jobs.ss.ge URL format and use Selenium.
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
                wait_for_element="div.sc-28f268a4-2",
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
        # jobs.ss.ge URLs need to be analyzed from actual URLs
        match = re.search(r"/vacancies/(\d+)", url)
        return match.group(1) if match else None
    
    async def get_job_listings(self, config: ScrapingConfig) -> AsyncIterator[Dict[str, Any]]:
        """
        Get job listings from jobs.ss.ge using parallel pagination for maximum speed.
        Uses two Chrome instances: one for odd pages, one for even pages.
        """
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        from queue import Queue
        import threading
        
        # Shared state between threads
        total_jobs_found = 0
        jobs_seen = set()  # Track job IDs to avoid duplicates
        jobs_queue = Queue()  # Thread-safe queue for jobs
        stop_scraping = threading.Event()  # Signal to stop all threads
        max_pages = 50  # Safety limit
        
        def create_chrome_driver():
            """Create optimized Chrome driver for parallel scraping."""
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            
            options = Options()
            if hasattr(self.strategy, 'headless') and self.strategy.headless:
                options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            # Aggressive performance optimizations for maximum speed
            options.add_argument("--disable-images")           # Don't load images
            options.add_argument("--disable-plugins")
            options.add_argument("--disable-extensions")
            options.add_argument("--page-load-strategy=eager") # Don't wait for all resources
            options.add_argument("--disable-web-security")     # Skip security checks
            options.add_argument("--disable-features=TranslateUI")
            options.add_argument("--disable-iframes")
            options.add_argument("--disable-background-timer-throttling")
            options.add_argument("--disable-renderer-backgrounding")
            options.add_argument("--disable-backgrounding-occluded-windows")
            options.add_argument("--disable-client-side-phishing-detection")
            options.add_argument("--disable-sync")
            options.add_argument("--disable-default-apps")
            options.add_argument("--no-default-browser-check")
            options.add_argument("--disable-gpu")  # Disable GPU acceleration
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            return webdriver.Chrome(options=options)
        
        def scrape_pages_worker(page_offset, thread_name, parser, config, logger, jobs_queue, jobs_seen, stop_scraping, max_pages, lock):
            """Worker function to scrape pages with given offset (0 for odd pages, 1 for even pages)."""
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.wait import WebDriverWait
            from bs4 import BeautifulSoup
            import time
            
            driver = create_chrome_driver()
            
            try:
                page = 1 + page_offset  # Start at 1 (odd) or 2 (even)
                
                while not stop_scraping.is_set() and page <= max_pages:
                    try:
                        # Build URL for this page  
                        if page == 1:
                            url = "https://jobs.ss.ge/ka/l/vacancies"
                        else:
                            url = f"https://jobs.ss.ge/ka/l/vacancies?page={page}"
                        
                        logger.info(f"{thread_name}: Loading page {page}: {url}")
                        driver.get(url)
                        
                        # Wait for initial page load - minimal wait
                        wait = WebDriverWait(driver, 8)   
                        time.sleep(0.5)  
                        
                        # Find job cards using optimized selectors
                        job_selectors = [
                            "div.sc-28f268a4-2.udaGZ",  # Primary selector
                            "div.sc-28f268a4-2",        # Fallback
                        ]
                        
                        job_elements = []
                        for selector in job_selectors:
                            try:
                                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                                if elements:
                                    job_elements = elements
                                    break
                            except Exception as e:
                                continue
                        
                        if not job_elements:
                            logger.warning(f"{thread_name}: No job elements found on page {page}")
                            break  
                        
                        logger.info(f"{thread_name}: Found {len(job_elements)} job elements on page {page}")
                        
                        # Parse jobs from this page (sync version for threading)
                        content = driver.page_source
                        soup = BeautifulSoup(content, 'html.parser')
                        current_job_listings = parser.parse_job_listings(soup)
                        
                        # Add jobs to queue (thread-safe)
                        new_jobs_found = 0
                        for job_listing in current_job_listings:
                            if stop_scraping.is_set():
                                break
                                
                            job_id = job_listing.id
                            
                            # Thread-safe duplicate check (use shared lock)
                            with lock:
                                if job_id not in jobs_seen:
                                    jobs_seen.add(job_id)
                                    jobs_queue.put(job_listing.to_dict())
                                    new_jobs_found += 1
                        
                        logger.info(f"{thread_name}: Page {page} added {new_jobs_found} new jobs to queue")
                        
                        # Move to next page (odd thread: 1,3,5... even thread: 2,4,6...)
                        page += 2
                        
                        # Brief pause between pages
                        time.sleep(0.3)
                        
                    except Exception as e:
                        logger.error(f"{thread_name}: Error on page {page}: {str(e)}")
                        break
                        
            finally:
                driver.quit()
                logger.info(f"{thread_name}: Worker finished")
        
        try:
            # Create shared lock for thread safety
            lock = threading.Lock()
            
            # Start two parallel worker threads
            with ThreadPoolExecutor(max_workers=2) as executor:
                # Thread 1: Odd pages (1, 3, 5, 7...)
                odd_future = executor.submit(
                    scrape_pages_worker, 0, "ODD_THREAD", 
                    self.parser, config, self.logger, jobs_queue, 
                    jobs_seen, stop_scraping, max_pages, lock
                )
                # Thread 2: Even pages (2, 4, 6, 8...)  
                even_future = executor.submit(
                    scrape_pages_worker, 1, "EVEN_THREAD",
                    self.parser, config, self.logger, jobs_queue, 
                    jobs_seen, stop_scraping, max_pages, lock
                )
                
                # Yield jobs as they come in from the queue
                while total_jobs_found < config.job_count:
                    try:
                        # Get job from queue with timeout
                        job_dict = jobs_queue.get(timeout=2.0)
                        
                        yield job_dict
                        total_jobs_found += 1
                        
                        # Mark task as done
                        jobs_queue.task_done()
                        
                        # Log progress
                        if total_jobs_found % 10 == 0:
                            self.logger.info(f"Parallel SS.ge: {total_jobs_found}/{config.job_count} jobs collected")
                        
                        # Check if we've hit our target - immediately stop threads
                        if total_jobs_found >= config.job_count:
                            self.logger.info(f"Target reached ({total_jobs_found}/{config.job_count}) - stopping worker threads")
                            stop_scraping.set()
                            break
                            
                    except:
                        # No more jobs in queue, check if both threads are done
                        if odd_future.done() and even_future.done():
                            self.logger.info("Both worker threads completed")
                            break
                        continue
                
                # Clean shutdown after target reached or threads completed
                self.logger.info("Initiating clean shutdown of worker threads...")
                stop_scraping.set()
                
                # Wait for both worker threads to finish
                try:
                    odd_future.result(timeout=5)
                    even_future.result(timeout=5)
                    self.logger.info("Worker threads successfully stopped")
                except Exception as e:
                    self.logger.warning(f"Thread cleanup timeout: {e}")
                
                self.logger.info(f"Parallel SS.ge scraping completed: {total_jobs_found} total jobs")
                
        except Exception as e:
            self.logger.error(f"Error fetching jobs.ss.ge listings: {str(e)}")
            raise
    
    def _should_include_job(self, job: JobListing, config: ScrapingConfig) -> bool:
        """Check if a job should be included based on configuration filters."""
        # Location filtering (basic text matching)
        if config.location_id and config.location_id != "":
            location_text = job.location.city.lower() if job.location.city else ""
            if config.location_id.lower() not in location_text:
                return False
        
        # Query filtering (search in title)
        if config.query:
            if config.query.lower() not in job.title.lower():
                return False
        
        return True
    
    async def search_jobs(self, config: ScrapingConfig) -> AsyncIterator[Dict[str, Any]]:
        """
        Search for jobs on jobs.ss.ge.
        Uses the same pagination-based approach as get_job_listings.
        """
        async for job in self.get_job_listings(config):
            yield job 