import asyncio
import aiohttp
import random
from typing import Optional, List

PAGE_SIZE = 300
REQUEST_DELAY = 1.0

class Collector:
    """
    Handles HTTP requests to jobs.ge with proper rate limiting and async capabilities.
    """
    
    def __init__(
        self,
        local: str = "ge",
        job_count: int = 20,
        location_id: Optional[int] = None,
        category_id: Optional[int] = None,
        query: Optional[str] = None,
        has_salary: bool = False,
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize the collector with search parameters.
        
        Args:
            local: Language locale (e.g., 'ge', 'en')
            job_count: Total number of jobs to fetch
            location_id: Filter by location ID
            category_id: Filter by category ID
            query: Search query string
            has_salary: Filter for jobs with salary information
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts for failed requests
        """
        self.local = local
        self.job_count = job_count
        self.location_id = location_id
        self.category_id = category_id
        self.query = query
        self.has_salary = has_salary
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Calculate total pages needed
        self.total_pages = (job_count + PAGE_SIZE - 1) // PAGE_SIZE
        
        # Default headers to mimic browser behavior
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0"
        }
    
    def _build_url(self, page: int) -> str:
        """
        Builds the URL for a specific page with all parameters.
        
        Args:
            page: Page number (1-indexed)
            
        Returns:
            Complete URL for the request
        """
        base_url = f"https://jobs.ge/{self.local}"
        params = [f"page={page}"]
        
        if self.category_id is not None:
            params.append(f"cid={self.category_id}")
        
        if self.location_id is not None:
            params.append(f"lid={self.location_id}")
        
        if self.query:
            params.append(f"q={self.query}")
        
        if self.has_salary:
            params.append("has_salary=1")
        
        return f"{base_url}?{'&'.join(params)}"
    
    async def fetch_page(self, session: aiohttp.ClientSession, page: int) -> str:
        """
        Fetches a single page of job listings.
        
        Args:
            session: Active aiohttp ClientSession
            page: Page number to fetch
            
        Returns:
            HTML content as string
        """
        url = self._build_url(page)
        
        for attempt in range(self.max_retries):
            try:
                # Add jitter to avoid detection and server load spikes
                delay = REQUEST_DELAY * (0.8 + 0.4 * random.random())
                await asyncio.sleep(delay)
                
                async with session.get(url, headers=self.headers, timeout=self.timeout) as response:
                    if response.status == 200:
                        html = await response.text()
                        print(f"Successfully fetched page {page}")
                        return html
                    else:
                        print(f"Error fetching page {page}: HTTP {response.status}")
                        
            except asyncio.TimeoutError:
                print(f"Timeout on page {page}, attempt {attempt+1}/{self.max_retries}")
            except Exception as e:
                print(f"Error on page {page}, attempt {attempt+1}/{self.max_retries}: {str(e)}")
            
            # Exponential backoff for retries
            await asyncio.sleep(2 ** attempt)
        
        raise Exception(f"Failed to fetch page {page} after {self.max_retries} attempts")
    
    async def fetch_all_pages(self) -> List[str]:
        """
        Fetches all pages needed to fulfill the job_count requirement.
        
        Returns:
            List of HTML strings, one per page
        """
        async with aiohttp.ClientSession() as session:
            tasks = []
            for page in range(1, self.total_pages + 1):
                tasks.append(self.fetch_page(session, page))
            
            return await asyncio.gather(*tasks)
    
    async def fetch_detail_page(self, session: aiohttp.ClientSession, job_url: str) -> str:
        """
        Fetches a detail page for a specific job.
        
        Args:
            session: Active aiohttp ClientSession
            job_url: URL of the job detail page
            
        Returns:
            HTML content as string
        """
        for attempt in range(self.max_retries):
            try:
                # Add jitter to avoid detection
                delay = REQUEST_DELAY * (0.8 + 0.4 * random.random())
                await asyncio.sleep(delay)
                
                async with session.get(job_url, headers=self.headers, timeout=self.timeout) as response:
                    if response.status == 200:
                        html = await response.text()
                        print(f"Successfully fetched job details: {job_url}")
                        return html
                    else:
                        print(f"Error fetching job details: HTTP {response.status}")
                        
            except asyncio.TimeoutError:
                print(f"Timeout on job detail, attempt {attempt+1}/{self.max_retries}")
            except Exception as e:
                print(f"Error on job detail, attempt {attempt+1}/{self.max_retries}: {str(e)}")
            
            # Exponential backoff for retries
            await asyncio.sleep(2 ** attempt)
        
        raise Exception(f"Failed to fetch job details after {self.max_retries} attempts")
    
    async def fetch_details_batch(self, job_urls: List[str], max_concurrent: int = 5) -> List[str]:
        """
        Fetches multiple job detail pages with controlled concurrency.
        
        Args:
            job_urls: List of URLs to job detail pages
            max_concurrent: Maximum number of concurrent requests
            
        Returns:
            List of HTML strings, one per job detail page
        """
        results = []
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def fetch_with_semaphore(url):
            async with semaphore:
                return await self.fetch_detail_page(session, url)
        
        async with aiohttp.ClientSession() as session:
            tasks = [fetch_with_semaphore(url) for url in job_urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        return [r for r in results if not isinstance(r, Exception)]
