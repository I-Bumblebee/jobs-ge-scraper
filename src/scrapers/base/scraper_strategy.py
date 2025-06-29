from abc import ABC, abstractmethod
from typing import Dict, Any, List
from enum import Enum
import asyncio
import aiohttp
from bs4 import BeautifulSoup


class ScrapingMethod(Enum):
    """Different scraping methods available."""
    STATIC = "static"  # BeautifulSoup
    DYNAMIC = "dynamic"  # Selenium
    API = "api"  # REST API calls
    SCRAPY = "scrapy"  # Scrapy framework


class ScraperStrategy(ABC):
    """Strategy pattern for different scraping approaches."""
    
    def __init__(self, max_concurrent: int = 5, timeout: int = 30):
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    @abstractmethod
    async def fetch_page(self, url: str, **kwargs) -> str:
        """Fetch a single page using the strategy."""
        pass
    
    @abstractmethod
    async def parse_content(self, content: str, parser_func) -> Dict[str, Any]:
        """Parse content using the strategy."""
        pass
    
    @property
    @abstractmethod
    def method_type(self) -> ScrapingMethod:
        """Return the scraping method type."""
        pass


class StaticScraperStrategy(ScraperStrategy):
    """Strategy for static content scraping using BeautifulSoup."""
    
    def __init__(self, max_concurrent: int = 5, timeout: int = 30):
        super().__init__(max_concurrent, timeout)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
        }
    
    async def fetch_page(self, url: str, **kwargs) -> str:
        """Fetch page using aiohttp."""
        async with self.semaphore:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, 
                    headers=self.headers, 
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status
                        )
    
    async def parse_content(self, content: str, parser_func) -> Dict[str, Any]:
        """Parse content using BeautifulSoup."""
        soup = BeautifulSoup(content, "html.parser")
        result = parser_func(soup)
        # Handle both sync and async parser functions
        if hasattr(result, '__await__'):
            return await result
        return result
    
    @property
    def method_type(self) -> ScrapingMethod:
        return ScrapingMethod.STATIC


class DynamicScraperStrategy(ScraperStrategy):
    """Strategy for dynamic content scraping using Selenium."""
    
    def __init__(self, max_concurrent: int = 2, timeout: int = 30, headless: bool = True):
        super().__init__(max_concurrent, timeout)
        self.headless = headless
        self._driver_pool = []
    
    async def fetch_page(self, url: str, **kwargs) -> str:
        """Fetch page using Selenium."""
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.wait import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        async with self.semaphore:
            options = Options()
            if self.headless:
                options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            
            driver = webdriver.Chrome(options=options)
            try:
                driver.get(url)
                
                # Wait for page to load
                wait_for = kwargs.get('wait_for_element')
                if wait_for:
                    wait = WebDriverWait(driver, self.timeout)
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, wait_for)))
                
                # Execute any custom JavaScript if provided
                custom_js = kwargs.get('execute_js')
                if custom_js:
                    driver.execute_script(custom_js)
                
                return driver.page_source
            finally:
                driver.quit()
    
    async def parse_content(self, content: str, parser_func) -> Dict[str, Any]:
        """Parse content using BeautifulSoup (content already rendered by Selenium)."""
        soup = BeautifulSoup(content, "html.parser")
        result = parser_func(soup)
        # Handle both sync and async parser functions
        if hasattr(result, '__await__'):
            return await result
        return result
    
    @property
    def method_type(self) -> ScrapingMethod:
        return ScrapingMethod.DYNAMIC


class APIScraperStrategy(ScraperStrategy):
    """Strategy for API-based scraping."""
    
    def __init__(self, max_concurrent: int = 10, timeout: int = 30, api_key: str = None):
        super().__init__(max_concurrent, timeout)
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
    
    async def fetch_page(self, url: str, **kwargs) -> str:
        """Fetch data from API endpoint."""
        async with self.semaphore:
            async with aiohttp.ClientSession() as session:
                method = kwargs.get('method', 'GET')
                data = kwargs.get('data')
                
                async with session.request(
                    method,
                    url,
                    headers=self.headers,
                    json=data if method == 'POST' else None,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status
                        )
    
    async def parse_content(self, content: str, parser_func) -> Dict[str, Any]:
        """Parse JSON content."""
        import json
        data = json.loads(content)
        result = parser_func(data)
        # Handle both sync and async parser functions
        if hasattr(result, '__await__'):
            return await result
        return result
    
    @property
    def method_type(self) -> ScrapingMethod:
        return ScrapingMethod.API 