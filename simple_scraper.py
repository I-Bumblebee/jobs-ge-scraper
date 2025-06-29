#!/usr/bin/env python3
"""
Simple, working Jobs.ge scraper
No complex pipelines - just works!
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from src.scrapers.factory.scraper_factory import ScraperFactory, ScraperType
from src.scrapers.base.scraper_interface import ScrapingConfig


async def scrape_jobs_simple():
    """Simple function to scrape jobs that actually works."""
    
    print("🚀 Simple Jobs.ge Scraper")
    print("=" * 50)
    
    # Create output directory
    output_dir = Path("data/simple_output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create scraper
    print("Creating Jobs.ge scraper...")
    scraper = ScraperFactory.create_scraper(ScraperType.JOBS_GE)
    print("✅ Scraper created!")
    
    # Configure scraping
    config = ScrapingConfig(
        job_count=20,           # Number of jobs to scrape
        location_id=1,          # Tbilisi
        category_id=6,          # IT/Programming
        locale="ge"             # Georgian site
    )
    
    print(f"\nConfiguration:")
    print(f"  - Jobs to scrape: {config.job_count}")
    print(f"  - Location: Tbilisi (ID: {config.location_id})")
    print(f"  - Category: IT/Programming (ID: {config.category_id})")
    print(f"  - Language: Georgian")
    
    # Scrape jobs
    print(f"\n🔍 Starting to scrape jobs...")
    jobs = []
    
    try:
        async for job in scraper.get_job_listings(config):
            jobs.append(job)
            print(f"  📋 Job {len(jobs)}: {job.get('title', 'No title')}")
            
            if len(jobs) >= config.job_count:
                break
        
        print(f"\n✅ Successfully scraped {len(jobs)} jobs!")
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"jobs_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"💾 Results saved to: {output_file}")
        
        # Show summary
        print(f"\n📊 Summary:")
        print(f"  - Total jobs found: {len(jobs)}")
        print(f"  - Companies: {len(set(job.get('company', {}).get('name', 'Unknown') for job in jobs))}")
        print(f"  - Output file: {output_file}")
        
        # Show first few jobs
        print(f"\n📋 First few jobs:")
        for i, job in enumerate(jobs[:5], 1):
            company = job.get('company', {}).get('name', 'Unknown Company')
            title = job.get('title', 'No title')
            print(f"  {i}. {title} - {company}")
        
        return jobs
        
    except Exception as e:
        print(f"❌ Error occurred: {str(e)}")
        return []


def main():
    """Main function."""
    print("Simple Jobs.ge Scraper")
    print("This bypasses all the complex pipeline stuff and just works!\n")
    
    # Run the scraper
    jobs = asyncio.run(scrape_jobs_simple())
    
    if jobs:
        print(f"\n🎉 SUCCESS! Scraped {len(jobs)} jobs successfully!")
        print("Check the 'data/simple_output' folder for the results.")
    else:
        print("\n❌ No jobs were scraped. Check your internet connection.")
    
    print("\n" + "="*50)
    print("Scraping complete!")


if __name__ == "__main__":
    main() 