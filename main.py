#!/usr/bin/env python3

import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.scrapers.factory.scraper_factory import ScraperFactory, ScraperType
from src.scrapers.base.scraper_interface import ScrapingConfig
from src.utils.database_output_manager import DatabaseOutputManager
from src.config.database import test_connection, create_tables
from src.utils.logger import setup_logging


async def main():
    setup_logging(level="INFO")
    
    print("🔄 Database Connection Test")
    if not test_connection():
        print("❌ Database connection failed")
        return
    print("✅ Database connected")
    
    print("🔄 Creating database tables")
    create_tables()
    print("✅ Tables ready")
    
    db_manager = DatabaseOutputManager()
    
    platforms = [
        # Scale up to 5000 jobs total - production targets
        (ScraperType.JOBS_GE, {"job_count": 2500, "category_id": "1", "location_id": "1", "locale": "ge"}),  # All categories  
        (ScraperType.CV_GE, {"job_count": 2000, "locale": "ge"}),   # CV.ge 
        (ScraperType.SS_GE, {"job_count": 500, "locale": "ge"})     # jobs.ss.ge with parallel optimization
    ]
    
    total_saved = 0
    
    for platform_type, config_data in platforms:
        print(f"🚀 Starting {platform_type.value}")
        
        try:
            scraper = ScraperFactory.create_scraper(platform_type)
            config = ScrapingConfig(**config_data)
            
            job_count = 0
            saved_count = 0
            
            async for job_listing in scraper.get_job_listings(config):
                job_count += 1
                job_listing['platform'] = platform_type.value
                job_listing['_scraped_at'] = datetime.now().isoformat()
                
                if await db_manager.save_job_listing(job_listing):
                    saved_count += 1
                
                if job_count % 5 == 0:
                    print(f"📊 {platform_type.value}: {saved_count}/{job_count} saved")
                
                if job_count >= config.job_count:
                    break
            
            print(f"✅ {platform_type.value}: {saved_count}/{job_count} jobs saved")
            total_saved += saved_count
            
        except Exception as e:
            print(f"❌ {platform_type.value} failed: {e}")
    
    print(f"🎉 Total jobs saved: {total_saved}")


if __name__ == "__main__":
    asyncio.run(main()) 