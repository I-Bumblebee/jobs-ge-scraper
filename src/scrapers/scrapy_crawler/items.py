import scrapy
from scrapy import Field


class JobItem(scrapy.Item):
    """Scrapy item for job listings."""
    
    # Basic job information
    id = Field()
    platform = Field()
    title = Field()
    url = Field()
    
    # Company information
    company_name = Field()
    company_url = Field()
    company_logo_url = Field()
    
    # Location information
    location_city = Field()
    location_country = Field()
    location_is_remote = Field()
    
    # Job metadata
    is_expiring = Field()
    was_recently_updated = Field()
    has_salary_info = Field()
    is_new = Field()
    is_in_region = Field()
    is_vip = Field()
    
    # Dates
    published_date = Field()
    deadline_date = Field()
    scraped_date = Field()
    
    # Additional fields for detailed information
    description = Field()
    requirements = Field()
    salary_min = Field()
    salary_max = Field()
    salary_currency = Field()
    employment_type = Field()
    experience_level = Field()


class JobDetailItem(scrapy.Item):
    """Scrapy item for detailed job information."""
    
    job_id = Field()
    description = Field()
    requirements = Field()
    responsibilities = Field()
    benefits = Field()
    salary_info = Field()
    employment_type = Field()
    experience_level = Field()
    contact_info = Field()
    application_instructions = Field() 