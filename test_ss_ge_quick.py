#!/usr/bin/env python3
"""
Quick test script for jobs.ss.ge scraper - faster testing with fewer jobs.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.scrapers.factory.scraper_factory import ScraperFactory, ScraperType
from src.scrapers.base.scraper_interface import ScrapingConfig
from src.utils.database_output_manager import DatabaseOutputManager
from src.config.database import test_connection, create_tables

async def test_ss_ge_quick():
    try:
        print('🚀 Quick SS.ge test (50 jobs max)...')
        
        # Test database connection
        if not test_connection():
            print("❌ Database connection failed")
            return
        create_tables()
        
        # Create SS_GE scraper
        scraper = ScraperFactory.create_scraper(ScraperType.SS_GE)
        config = ScrapingConfig(job_count=50, locale='ge')  # Only 50 jobs for quick test
        
        db_manager = DatabaseOutputManager()
        
        print('📊 Testing job listings and database saving...')
        count = 0
        saved_count = 0
        
        start_time = datetime.now()
        
        async for job in scraper.get_job_listings(config):
            count += 1
            job['platform'] = 'ss_ge'
            job['_scraped_at'] = datetime.now().isoformat()
            
            # Save to database
            if await db_manager.save_job_listing(job):
                saved_count += 1
            
            print(f'✅ Job {count}: {job.get("title", "Unknown")} - Saved: {saved_count}/{count}')
            
            if count >= 50:  # Stop at 50 jobs
                break
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f'✅ Quick test completed: {saved_count}/{count} jobs saved in {duration:.1f} seconds')
        print(f'📈 Rate: {count/duration:.1f} jobs/second')
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ss_ge_quick()) 