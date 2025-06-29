#!/usr/bin/env python3
"""
Test script for jobs.ss.ge scraper functionality.
"""

import asyncio
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.scrapers.factory.scraper_factory import ScraperFactory, ScraperType
from src.scrapers.base.scraper_interface import ScrapingConfig

async def test_ss_ge():
    try:
        print('🚀 Testing jobs.ss.ge scraper...')
        
        # Create SS_GE scraper
        scraper = ScraperFactory.create_scraper(ScraperType.SS_GE)
        config = ScrapingConfig(job_count=10, locale='ge')
        
        print('📊 Testing job listings...')
        count = 0
        async for job in scraper.get_job_listings(config):
            count += 1
            print(f'✅ Found job {count}: {job.get("title", "Unknown")}')
            if count >= 5:  # Test first 5 jobs
                break
        
        print(f'✅ Test completed: Found {count} jobs from jobs.ss.ge')
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ss_ge()) 