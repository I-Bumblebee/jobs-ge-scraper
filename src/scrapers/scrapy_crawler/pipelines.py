import logging
from datetime import datetime
from scrapy import signals
from scrapy.exceptions import DropItem


class JobValidationPipeline:
    """Pipeline for validating job items."""
    
    def process_item(self, item, spider):
        """Validate job item fields."""
        
        # Check required fields
        required_fields = ['id', 'title', 'url']
        for field in required_fields:
            if not item.get(field):
                raise DropItem(f"Missing required field: {field}")
        
        # Clean and validate data
        if item.get('title'):
            item['title'] = item['title'].strip()
        
        if item.get('company_name'):
            item['company_name'] = item['company_name'].strip()
        
        # Ensure scraped_date is set
        if not item.get('scraped_date'):
            item['scraped_date'] = datetime.now()
        
        return item


class JobStoragePipeline:
    """Pipeline for storing job items."""
    
    def __init__(self):
        self.jobs_scraped = 0
        
    @classmethod
    def from_crawler(cls, crawler):
        return cls()
    
    def open_spider(self, spider):
        """Initialize storage when spider opens."""
        spider.logger.info("JobStoragePipeline opened")
        self.jobs_scraped = 0
    
    def close_spider(self, spider):
        """Clean up when spider closes."""
        spider.logger.info(f"JobStoragePipeline closed. Total jobs processed: {self.jobs_scraped}")
    
    def process_item(self, item, spider):
        """Process and store the job item."""
        
        # Log the job
        spider.logger.info(f"Processing job: {item.get('title', 'Unknown')}")
        
        # Here you could add database storage, file export, etc.
        # For now, we'll just count and log
        self.jobs_scraped += 1
        
        # Print job summary
        print(f"\n{'='*60}")
        print(f"Job #{self.jobs_scraped}: {item.get('title', 'N/A')}")
        print(f"Company: {item.get('company_name', 'N/A')}")
        print(f"Location: {item.get('location_city', 'N/A')}")
        print(f"URL: {item.get('url', 'N/A')}")
        print(f"VIP: {'Yes' if item.get('is_vip') else 'No'}")
        if item.get('published_date'):
            print(f"Published: {item.get('published_date')}")
        print(f"{'='*60}")
        
        return item


class DuplicatesPipeline:
    """Pipeline for filtering duplicate jobs."""
    
    def __init__(self):
        self.ids_seen = set()
    
    def process_item(self, item, spider):
        """Filter out duplicate jobs based on ID."""
        
        job_id = item.get('id')
        if job_id in self.ids_seen:
            raise DropItem(f"Duplicate item found: {job_id}")
        else:
            self.ids_seen.add(job_id)
            return item 