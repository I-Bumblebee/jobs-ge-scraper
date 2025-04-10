import asyncio
import aiohttp
import random
from typing import AsyncIterator, Optional, List
from contextlib import asynccontextmanager

PAGE_SIZE = 300
REQUEST_DELAY = 1.0

class Collector:
    """
    Handles HTTP requests to jobs.ge with proper rate limiting and async capabilities.
    """
    
    def __init__(
        self,
        locale: str = "ge",
        job_count: int = 20,
        location_id: Optional[int] = None,
        category_id: Optional[int] = None,
        query: Optional[str] = None,
        has_salary: bool = False,
        timeout: int = 30,
        max_retries: int = 3,
        max_concurrent: int = 5
    ):
        """
        Initialize the collector with search parameters.
        
        Args:
            locale: Language localee (e.g., 'ge', 'en')
            job_count: Total number of jobs to fetch
            location_id: Filter by location ID
            category_id: Filter by category ID
            query: Search query string
            has_salary: Filter for jobs with salary information
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts for failed requests
            max_concurrent: Maximum concurrent requests
        """
        self.locale = locale
        self.job_count = job_count
        self.location_id = location_id
        self.category_id = category_id
        self.query = query
        self.has_salary = has_salary
        self.timeout = timeout
        self.max_retries = max_retries
        self.max_concurrent = max_concurrent
        
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
        
        # Create a semaphore for concurrent requests
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    def _build_url(self, page: int = None, job_id: str = None) -> str:
        """
        Builds the URL for a specific page or job with all parameters.
        
        Args:
            page: Page number (1-indexed)
            job_id: Job ID for detail page
            
        Returns:
            Complete URL for the request
        """
        base_url = f"https://jobs.ge/{self.locale}"
        
        # Detail page
        if job_id:
            return f"{base_url}/?view=jobs&id={job_id}"
        
        # List page
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
    
    @asynccontextmanager
    async def _session_manager(self):
        """Context manager for handling aiohttp session lifecycle."""
        session = aiohttp.ClientSession()
        try:
            yield session
        finally:
            await session.close()
    
    @asynccontextmanager
    async def _rate_limiter(self):
        """Context manager for rate limiting requests."""
        async with self.semaphore:
            # Add jitter to avoid detection and server load spikes
            delay = REQUEST_DELAY * (0.8 + 0.4 * random.random())
            await asyncio.sleep(delay)
            yield
    
    async def _fetch_with_retry(self, session: aiohttp.ClientSession, url: str) -> str:
        """
        Fetches a URL with retry logic.
        
        Args:
            session: Active aiohttp ClientSession
            url: URL to fetch
            
        Returns:
            HTML content as string
        """
        for attempt in range(self.max_retries):
            try:
                async with self._rate_limiter():
                    async with session.get(url, headers=self.headers, timeout=self.timeout) as response:
                        if response.status == 200:
                            return await response.text()
                        else:
                            raise aiohttp.ClientResponseError(
                                request_info=response.request_info,
                                history=response.history,
                                status=response.status,
                                message=f"HTTP Error {response.status}",
                            )
                            
            except asyncio.TimeoutError:
                print(f"Timeout on {url}, attempt {attempt+1}/{self.max_retries}")
            except Exception as e:
                print(f"Error on {url}, attempt {attempt+1}/{self.max_retries}: {str(e)}")
            
            # Exponential backoff for retries
            await asyncio.sleep(2 ** attempt)
        
        raise Exception(f"Failed to fetch {url} after {self.max_retries} attempts")
    
    async def fetch_page(self, session: Optional[aiohttp.ClientSession], page: int) -> str:
        """
        Fetches a single page of job listings.
        
        Args:
            session: Active aiohttp ClientSession or None to create one
            page: Page number to fetch
            
        Returns:
            HTML content as string
        """
        url = self._build_url(page=page)
        
        if session:
            html = await self._fetch_with_retry(session, url)
            print(f"Successfully fetched page {page}")
            return html
        
        # Create a session if none was provided
        async with self._session_manager() as new_session:
            html = await self._fetch_with_retry(new_session, url)
            print(f"Successfully fetched page {page}")
            return html
    
    async def fetch_pages_generator(self) -> AsyncIterator[str]:
        """
        Fetches pages asynchronously and yields them one at a time.
        
        Yields:
            HTML content of each page as string
        """
        async with self._session_manager() as session:
            # Use asyncio.as_completed to yield results as they complete
            fetch_tasks = [
                self.fetch_page(session, page) 
                for page in range(1, self.total_pages + 1)
            ]
            
            for completed_task in asyncio.as_completed(fetch_tasks):
                try:
                    yield await completed_task
                except Exception as e:
                    print(f"Error in page fetching: {str(e)}")
    
    async def fetch_detail_page(self, session: Optional[aiohttp.ClientSession], job_url: str) -> str:
        """
        Fetches a detail page for a specific job.
        
        Args:
            session: Active aiohttp ClientSession or None to create one
            job_url: URL of the job detail page
            
        Returns:
            HTML content as string
        """
        if session:
            html = await self._fetch_with_retry(session, job_url)
            print(f"Successfully fetched job details: {job_url}")
            return html
        
        # Create a session if none was provided
        async with self._session_manager() as new_session:
            html = await self._fetch_with_retry(new_session, job_url)
            print(f"Successfully fetched job details: {job_url}")
            return html
    
    async def fetch_details_batch(self, job_urls: List[str]) -> List[str]:
        """
        Fetches multiple job detail pages with controlled concurrency.
        
        Args:
            job_urls: List of URLs to job detail pages
            
        Returns:
            List of HTML strings, one per job detail page
        """
        async with self._session_manager() as session:
            # Use as_completed for more efficient processing
            fetch_tasks = [
                self.fetch_detail_page(session, url) 
                for url in job_urls
            ]
            
            results = []
            for completed_task in asyncio.as_completed(fetch_tasks):
                try:
                    result = await completed_task
                    results.append(result)
                except Exception as e:
                    print(f"Error in detail fetching: {str(e)}")
            
            return results

    async def fetch_details_generator(self, job_ids: List[str]) -> AsyncIterator[tuple[str, str]]:
        """
        Fetches job details asynchronously and yields (job_id, html) pairs as they complete.
        
        Args:
            job_ids: List of job IDs to fetch details for
            
        Yields:
            Tuple of (job_id, html_content) as they complete
        """
        job_urls = [self._build_url(job_id=job_id) for job_id in job_ids]
        
        async with self._session_manager() as session:
            # Create tasks for all URLs
            fetch_tasks = {
                asyncio.create_task(self.fetch_detail_page(session, url)): (job_id, url)
                for job_id, url in zip(job_ids, job_urls)
            }
            
            # Yield results as they complete
            for task in asyncio.as_completed(fetch_tasks.keys()):
                job_id, url = fetch_tasks[task]
                try:
                    html = await task
                    yield job_id, html
                except Exception as e:
                    print(f"Error fetching job {job_id}: {str(e)}")
                    yield job_id, None
