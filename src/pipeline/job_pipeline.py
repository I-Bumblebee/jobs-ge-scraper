import asyncio
import logging
from typing import Dict, List, Any, AsyncIterator, Optional
from datetime import datetime
from dataclasses import asdict

from ..scrapers.base.scraper_interface import ScraperInterface, ScrapingConfig
from ..scrapers.factory.scraper_factory import ScraperFactory, ScraperType
from ..data.models import Platform, ScrapingResult
from ..utils.database_output_manager import DatabaseOutputManager


class JobPipeline:
    """
    Main pipeline for coordinating job scraping across multiple platforms.
    Implements the pipeline pattern for processing job data.
    """
    
    def __init__(
        self,
        platforms: List[ScraperType],
        config: ScrapingConfig,
        max_concurrent_details: int = 5
    ):
        """
        Initialize the job pipeline.
        
        Args:
            platforms: List of platforms to scrape
            config: Scraping configuration
            max_concurrent_details: Maximum concurrent detail requests
        """
        self.db_manager = DatabaseOutputManager()
        self.platforms = platforms
        self.config = config
        self.max_concurrent_details = max_concurrent_details
        self.logger = logging.getLogger(f"{__name__}.JobPipeline")
        
        # Create scrapers for each platform
        self.scrapers: Dict[ScraperType, ScraperInterface] = {}
        self._initialize_scrapers()
        
        # Semaphore for rate limiting detail requests
        self.detail_semaphore = asyncio.Semaphore(max_concurrent_details)
    
    def _initialize_scrapers(self):
        """Initialize scrapers for all specified platforms."""
        for platform in self.platforms:
            try:
                scraper = ScraperFactory.create_scraper(platform)
                self.scrapers[platform] = scraper
                self.logger.info(f"Initialized scraper for {platform.value}")
            except Exception as e:
                self.logger.error(f"Failed to initialize scraper for {platform.value}: {str(e)}")
    
    async def scrape_job_listings(self) -> AsyncIterator[Dict[str, Any]]:
        """
        Scrape job listings from all configured platforms.
        
        Yields:
            Job listing dictionaries with platform information
        """
        # For now, process platforms sequentially to avoid async complexity
        # Can be optimized later for true concurrent processing
        for platform_type, scraper in self.scrapers.items():
            try:
                async for job_listing in self._scrape_platform_listings(platform_type, scraper):
                    yield job_listing
            except Exception as e:
                self.logger.error(f"Error in platform scraping: {str(e)}")
    
    async def _scrape_platform_listings(
        self, 
        platform_type: ScraperType, 
        scraper: ScraperInterface
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Scrape listings from a single platform.
        
        Args:
            platform_type: The platform type
            scraper: The scraper instance
            
        Yields:
            Job listing dictionaries
        """
        try:
            self.logger.info(f"Starting scraping for {platform_type.value}")
            
            async for job_listing in scraper.get_job_listings(self.config):
                # Add platform information to the job listing
                job_listing['_platform_type'] = platform_type.value
                job_listing['_scraper_info'] = {
                    'platform_name': scraper.platform_name,
                    'scraped_at': datetime.now().isoformat()
                }
                yield job_listing
                
        except Exception as e:
            self.logger.error(f"Error scraping {platform_type.value}: {str(e)}")
    
    async def get_job_details(self, job_id: str, job_url: str, platform_type: ScraperType) -> Dict[str, Any]:
        """
        Get detailed information for a specific job.
        
        Args:
            job_id: Job identifier
            job_url: Job URL
            platform_type: Platform type
            
        Returns:
            Detailed job information
        """
        async with self.detail_semaphore:
            try:
                if platform_type not in self.scrapers:
                    raise ValueError(f"No scraper available for platform: {platform_type.value}")
                
                scraper = self.scrapers[platform_type]
                job_details = await scraper.get_job_details(job_id, job_url)
                
                # Add scraper metadata
                job_details['_platform_type'] = platform_type.value
                job_details['_detailed_at'] = datetime.now().isoformat()
                
                return job_details
                
            except Exception as e:
                self.logger.error(f"Error getting details for job {job_id}: {str(e)}")
                return {
                    'id': job_id,
                    'platform': platform_type.value,
                    'error': str(e),
                    '_detailed_at': datetime.now().isoformat()
                }
    
    async def process_job_details_batch(self, job_batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process a batch of jobs to get detailed information.
        
        Args:
            job_batch: List of job listing dictionaries
            
        Returns:
            List of detailed job dictionaries
        """
        detail_tasks = []
        
        for job in job_batch:
            platform_type = ScraperType(job.get('_platform_type'))
            job_id = job.get('id')
            job_url = job.get('url')
            
            if job_id and platform_type:
                task = self.get_job_details(job_id, job_url, platform_type)
                detail_tasks.append(task)
        
        # Execute all detail requests concurrently
        detailed_jobs = await asyncio.gather(*detail_tasks, return_exceptions=True)
        
        # Filter out exceptions and return valid results
        valid_results = []
        for result in detailed_jobs:
            if isinstance(result, Exception):
                self.logger.error(f"Detail request failed: {str(result)}")
            else:
                valid_results.append(result)
        
        return valid_results
    
    async def run_full_pipeline(self) -> Dict[str, Any]:
        """
        Run the complete scraping pipeline.
        
        Returns:
            Pipeline execution summary
        """
        start_time = datetime.now()
        summary = {
            'start_time': start_time.isoformat(),
            'platforms': [p.value for p in self.platforms],
            'config': asdict(self.config),
            'results': {},
            'total_jobs_found': 0,
            'total_details_fetched': 0,
            'errors': []
        }
        
        try:
            self.logger.info("Starting full pipeline execution")
            
            # Phase 1: Collect job listings
            all_jobs = []
            async for job_listing in self.scrape_job_listings():
                all_jobs.append(job_listing)
                await self.db_manager.save_job_listing(job_listing)
            
            summary['total_jobs_found'] = len(all_jobs)
            self.logger.info(f"Found {len(all_jobs)} total jobs")
            
            # Phase 2: Get detailed information in batches
            batch_size = self.config.batch_size
            detailed_jobs = []
            
            for i in range(0, len(all_jobs), batch_size):
                batch = all_jobs[i:i + batch_size]
                batch_details = await self.process_job_details_batch(batch)
                detailed_jobs.extend(batch_details)
                
                self.logger.info(f"Processed batch {i//batch_size + 1}/{(len(all_jobs) + batch_size - 1)//batch_size}")
            
            summary['total_details_fetched'] = len(detailed_jobs)
            
            # Phase 3: Save detailed jobs
            for job_detail in detailed_jobs:
                await self.db_manager.save_job_details(job_detail)
            
            end_time = datetime.now()
            summary['end_time'] = end_time.isoformat()
            summary['duration_seconds'] = (end_time - start_time).total_seconds()
            
            self.logger.info(f"Pipeline completed successfully in {summary['duration_seconds']:.2f} seconds")
            
        except Exception as e:
            error_msg = f"Pipeline execution failed: {str(e)}"
            self.logger.error(error_msg)
            summary['errors'].append(error_msg)
            summary['end_time'] = datetime.now().isoformat()
        
        return summary 