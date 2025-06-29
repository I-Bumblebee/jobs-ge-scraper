import scrapy
import sys
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup

# Add the project root to Python path to import our modules
sys.path.insert(0, str(Path(__file__).parents[4]))

from src.scrapers.platforms.cv_ge.cv_ge_parser import CvGeParser
from items import JobItem


class CvGeSpider(scrapy.Spider):
    """Simple Scrapy spider for cv.ge job listings."""
    
    name = 'cv_ge'
    allowed_domains = ['cv.ge']
    start_urls = ['https://www.cv.ge/announcements/all']
    
    # CV.ge specific settings
    MAX_PAGES = 24  # CV.ge has 24 pages total
    BASE_URL = 'https://www.cv.ge'
    
    def __init__(self, *args, **kwargs):
        super(CvGeSpider, self).__init__(*args, **kwargs)
        self.parser = CvGeParser()
        self.jobs_scraped = 0
        self.max_jobs = int(kwargs.get('max_jobs', 50))  # Default to 50 jobs
        self.current_page = 1
        
        self.logger.info(f"CV.ge Spider initialized. Max jobs: {self.max_jobs}")
    
    def start_requests(self):
        """Generate initial requests."""
        yield scrapy.Request(
            url=self.start_urls[0],
            callback=self.parse,
            meta={'page': 1}
        )
    
    def parse(self, response):
        """Parse job listings from the main page."""
        page = response.meta.get('page', 1)
        self.logger.info(f"Parsing CV.ge page {page}")
        
        # Create BeautifulSoup object for the parser
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Use the existing parser to extract job listings
        try:
            job_listings = self.parser.parse_job_listings(soup)
            self.logger.info(f"Found {len(job_listings)} jobs on page {page}")
            
            if not job_listings:
                self.logger.info(f"No jobs found on page {page}, stopping")
                return
            
            # Convert job listings to Scrapy items
            for job_listing in job_listings:
                if self.jobs_scraped >= self.max_jobs:
                    self.logger.info(f"Reached max jobs limit ({self.max_jobs}), stopping")
                    return
                
                item = self.convert_to_scrapy_item(job_listing)
                self.jobs_scraped += 1
                yield item
                
                # Optionally yield a request for job details
                if hasattr(job_listing, 'url') and job_listing.url:
                    yield scrapy.Request(
                        url=job_listing.url,
                        callback=self.parse_job_detail,
                        meta={'job_id': job_listing.id}
                    )
            
            # Continue to next page if we haven't reached max jobs and max pages
            if (self.jobs_scraped < self.max_jobs and 
                page < self.MAX_PAGES and 
                len(job_listings) > 0):
                
                next_page = page + 1
                next_url = f"{self.BASE_URL}/announcements/all?page={next_page}"
                
                self.logger.info(f"Moving to page {next_page}: {next_url}")
                yield scrapy.Request(
                    url=next_url,
                    callback=self.parse,
                    meta={'page': next_page}
                )
                
        except Exception as e:
            self.logger.error(f"Error parsing page {page}: {str(e)}")
    
    def parse_job_detail(self, response):
        """Parse detailed job information (optional)."""
        job_id = response.meta.get('job_id')
        self.logger.info(f"Parsing job details for ID: {job_id}")
        
        try:
            # Create BeautifulSoup object for the parser
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Use the existing parser to extract job details
            job_details = self.parser.parse_job_detail(soup, job_id)
            
            # You could yield a separate item for job details or
            # update the main job item with additional details
            self.logger.info(f"Parsed details for job {job_id}")
            
        except Exception as e:
            self.logger.error(f"Error parsing job details for {job_id}: {str(e)}")
    
    def convert_to_scrapy_item(self, job_listing):
        """Convert JobListing object to Scrapy JobItem."""
        item = JobItem()
        
        # Basic job information
        item['id'] = job_listing.id
        item['platform'] = job_listing.platform.value if hasattr(job_listing.platform, 'value') else str(job_listing.platform)
        item['title'] = job_listing.title
        item['url'] = job_listing.url
        
        # Company information
        if hasattr(job_listing, 'company') and job_listing.company:
            item['company_name'] = job_listing.company.name
            item['company_url'] = job_listing.company.jobs_url
            item['company_logo_url'] = job_listing.company.logo_url
        else:
            item['company_name'] = ''
            item['company_url'] = ''
            item['company_logo_url'] = ''
        
        # Location information
        if hasattr(job_listing, 'location') and job_listing.location:
            item['location_city'] = job_listing.location.city
            item['location_country'] = job_listing.location.country
            item['location_is_remote'] = job_listing.location.is_remote
        else:
            item['location_city'] = ''
            item['location_country'] = ''
            item['location_is_remote'] = False
        
        # Job metadata
        if hasattr(job_listing, 'metadata') and job_listing.metadata:
            item['is_expiring'] = job_listing.metadata.is_expiring
            item['was_recently_updated'] = job_listing.metadata.was_recently_updated
            item['has_salary_info'] = job_listing.metadata.has_salary_info
            item['is_new'] = job_listing.metadata.is_new
            item['is_in_region'] = job_listing.metadata.is_in_region
            item['is_vip'] = job_listing.metadata.is_vip
        else:
            item['is_expiring'] = False
            item['was_recently_updated'] = False  
            item['has_salary_info'] = False
            item['is_new'] = False
            item['is_in_region'] = False
            item['is_vip'] = False
        
        # Dates
        if hasattr(job_listing, 'dates') and job_listing.dates:
            item['published_date'] = job_listing.dates.published
            item['deadline_date'] = job_listing.dates.deadline
            item['scraped_date'] = job_listing.dates.scraped or datetime.now()
        else:
            item['published_date'] = None
            item['deadline_date'] = None
            item['scraped_date'] = datetime.now()
        
        return item
    
    def closed(self, reason):
        """Called when the spider is closed."""
        self.logger.info(f"CV.ge Spider closed. Reason: {reason}. Total jobs scraped: {self.jobs_scraped}") 