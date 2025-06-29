#!/usr/bin/env python3
"""
Database-integrated main script for concurrent multi-platform job scraping.
Scrapes jobs.ge, cv.ge, and hr.ge platforms and saves all data to PostgreSQL database.
"""

import asyncio
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.scrapers.factory.scraper_factory import ScraperFactory, ScraperType
from src.scrapers.base.scraper_interface import ScrapingConfig
from src.utils.database_output_manager import DatabaseOutputManager
from src.utils.logger import setup_logging, ScrapingLogger
from src.config.database import test_connection, create_tables


class DatabaseScrapingPipeline:
    """Pipeline for scraping multiple platforms and saving to database."""
    
    def __init__(self):
        """Initialize the database scraping pipeline."""
        self.logger = logging.getLogger(f"{__name__}.DatabaseScrapingPipeline")
        self.db_manager = DatabaseOutputManager()
        self.scraping_results = {}
        
    async def scrape_platform(self, platform_type: ScraperType, config: ScrapingConfig) -> Dict[str, Any]:
        """
        Scrape a single platform and save to database.
        
        Args:
            platform_type: The platform to scrape
            config: Scraping configuration
            
        Returns:
            Scraping results summary
        """
        platform_name = platform_type.value
        scraping_logger = ScrapingLogger(platform=platform_name, operation="database_scraping")
        
        start_time = datetime.now()
        result = {
            'platform': platform_name,
            'start_time': start_time,
            'total_jobs_found': 0,
            'successful_saves': 0,
            'failed_saves': 0,
            'errors': []
        }
        
        try:
            self.logger.info(f"🚀 Starting scraping for {platform_name}")
            scraping_logger.log_start(f"Starting {platform_name} scraping with database saving")
            
            # Create scraper
            scraper = ScraperFactory.create_scraper(platform_type)
            
            # Scrape job listings
            jobs_processed = 0
            async for job_listing in scraper.get_job_listings(config):
                jobs_processed += 1
                result['total_jobs_found'] = jobs_processed
                
                # Add platform info to job data
                job_listing['platform'] = platform_name
                job_listing['_scraped_at'] = datetime.now().isoformat()
                
                # Save to database
                if await self.db_manager.save_job_listing(job_listing):
                    result['successful_saves'] += 1
                    self.logger.debug(f"✅ {platform_name}: Saved job {job_listing.get('id', 'unknown')}")
                else:
                    result['failed_saves'] += 1
                    error_msg = f"Failed to save job {job_listing.get('id', 'unknown')}"
                    result['errors'].append(error_msg)
                    self.logger.warning(f"❌ {platform_name}: {error_msg}")
                
                # Progress feedback
                if jobs_processed % 10 == 0:
                    self.logger.info(f"📊 {platform_name}: Processed {jobs_processed} jobs")
            
            # Record completion
            result['end_time'] = datetime.now()
            result['duration_seconds'] = (result['end_time'] - start_time).total_seconds()
            
            # Log results
            scraping_logger.log_success(
                f"{platform_name} scraping completed",
                total_jobs=result['total_jobs_found'],
                successful_saves=result['successful_saves'],
                duration=result['duration_seconds']
            )
            
            self.logger.info(
                f"✅ {platform_name} completed: "
                f"{result['successful_saves']}/{result['total_jobs_found']} jobs saved "
                f"({result['duration_seconds']:.1f}s)"
            )
            
            return result
            
        except Exception as e:
            error_msg = f"{platform_name} scraping failed: {str(e)}"
            result['errors'].append(error_msg)
            result['end_time'] = datetime.now()
            
            scraping_logger.log_error(error_msg, exception=e)
            self.logger.error(f"❌ {error_msg}")
            
            return result
    
    async def run_concurrent_scraping(self, platforms_config: Dict[ScraperType, ScrapingConfig]) -> Dict[str, Any]:
        """
        Run concurrent scraping for multiple platforms.
        
        Args:
            platforms_config: Dictionary mapping platform types to their configurations
            
        Returns:
            Overall scraping results
        """
        overall_start = datetime.now()
        self.logger.info("🔥 Starting concurrent multi-platform scraping with database saving")
        
        # Create tasks for each platform
        tasks = []
        for platform_type, config in platforms_config.items():
            task = self.scrape_platform(platform_type, config)
            tasks.append((platform_type.value, task))
        
        # Run all platforms concurrently
        platform_results = {}
        for platform_name, task in tasks:
            try:
                result = await task
                platform_results[platform_name] = result
            except Exception as e:
                platform_results[platform_name] = {
                    'platform': platform_name,
                    'error': str(e),
                    'total_jobs_found': 0,
                    'successful_saves': 0,
                    'failed_saves': 0
                }
        
        # Calculate overall summary
        overall_end = datetime.now()
        overall_summary = {
            'start_time': overall_start,
            'end_time': overall_end,
            'duration_seconds': (overall_end - overall_start).total_seconds(),
            'platforms': list(platforms_config.keys()),
            'platform_results': platform_results,
            'total_jobs_found': sum(r.get('total_jobs_found', 0) for r in platform_results.values()),
            'total_successful_saves': sum(r.get('successful_saves', 0) for r in platform_results.values()),
            'total_failed_saves': sum(r.get('failed_saves', 0) for r in platform_results.values()),
            'all_errors': []
        }
        
        # Collect all errors
        for result in platform_results.values():
            if 'errors' in result:
                overall_summary['all_errors'].extend(result['errors'])
        
        # Save scraping results to database
        for platform_name, result in platform_results.items():
            await self.db_manager.save_scraping_result({
                'platform': platform_name,
                'total_jobs_found': result.get('total_jobs_found', 0),
                'successful_scrapes': result.get('successful_saves', 0),
                'failed_scrapes': result.get('failed_saves', 0),
                'start_time': result.get('start_time'),
                'end_time': result.get('end_time'),
                'errors': result.get('errors', [])
            })
        
        return overall_summary


async def main():
    """Main function to run concurrent multi-platform scraping."""
    
    # Set up logging
    logger = setup_logging(level="INFO", log_file="database_scraping")
    logger.info("🎯 Starting database-integrated job scraper")
    
    try:
        # Test database connection
        print("🔍 Testing database connection...")
        if not test_connection():
            print("❌ Database connection failed!")
            print("Please ensure:")
            print("1. PostgreSQL database is running (docker-compose up -d)")
            print("2. Environment variables are set correctly")
            print("3. Database credentials are correct")
            return 1
        
        print("✅ Database connection successful!")
        
        # Ensure tables exist
        print("🗄️  Ensuring database tables exist...")
        create_tables()
        print("✅ Database tables ready!")
        
        # Initialize pipeline
        pipeline = DatabaseScrapingPipeline()
        
        # Configure scraping for all 3 platforms
        platforms_config = {
            # Jobs.ge - IT jobs with good coverage
            ScraperType.JOBS_GE: ScrapingConfig(
                job_count=100,
                category_id="6",  # IT/Programming
                location_id="1",  # Tbilisi
                has_salary=True,
                locale="ge",
                max_concurrent=3,
                batch_size=10
            ),
            
            # CV.ge - All jobs with good coverage
            ScraperType.CV_GE: ScrapingConfig(
                job_count=50,
                locale="ge",
                max_concurrent=3,
                batch_size=10
            ),
            
            # HR.ge - All jobs
            ScraperType.HR_GE: ScrapingConfig(
                job_count=50,
                locale="ge",
                max_concurrent=3,
                batch_size=10
            )
        }
        
        print("\n🚀 Starting concurrent scraping of all platforms:")
        print(f"   • Jobs.ge: {platforms_config[ScraperType.JOBS_GE].job_count} IT jobs")
        print(f"   • CV.ge: {platforms_config[ScraperType.CV_GE].job_count} jobs")
        print(f"   • HR.ge: {platforms_config[ScraperType.HR_GE].job_count} jobs")
        print()
        
        # Run concurrent scraping
        results = await pipeline.run_concurrent_scraping(platforms_config)
        
        # Display results
        print("\n" + "="*60)
        print("🎉 CONCURRENT SCRAPING COMPLETED!")
        print("="*60)
        
        print(f"\n📊 Overall Summary:")
        print(f"   • Duration: {results['duration_seconds']:.1f} seconds")
        print(f"   • Total jobs found: {results['total_jobs_found']}")
        print(f"   • Successfully saved: {results['total_successful_saves']}")
        print(f"   • Failed saves: {results['total_failed_saves']}")
        print(f"   • Success rate: {(results['total_successful_saves'] / max(results['total_jobs_found'], 1) * 100):.1f}%")
        
        print(f"\n📋 Platform Breakdown:")
        for platform_name, result in results['platform_results'].items():
            duration = result.get('duration_seconds', 0)
            jobs_found = result.get('total_jobs_found', 0)
            saved = result.get('successful_saves', 0)
            
            print(f"   • {platform_name}:")
            print(f"     - Jobs found: {jobs_found}")
            print(f"     - Saved to DB: {saved}")
            print(f"     - Duration: {duration:.1f}s")
            
            if result.get('errors'):
                print(f"     - Errors: {len(result['errors'])}")
        
        # Check database for verification
        print(f"\n🗄️  Database Verification:")
        stats = await pipeline.db_manager.get_scraping_stats()
        if stats:
            print("   Platform totals in database:")
            for platform, count in stats.get('platform_totals', {}).items():
                print(f"     • {platform}: {count} jobs")
        
        if results['all_errors']:
            print(f"\n⚠️  Errors encountered ({len(results['all_errors'])}):")
            for error in results['all_errors'][:5]:  # Show first 5 errors
                print(f"   • {error}")
            if len(results['all_errors']) > 5:
                print(f"   ... and {len(results['all_errors']) - 5} more errors")
        
        print(f"\n✅ All data has been saved to the PostgreSQL database!")
        print(f"You can now query the database to see the scraped job data.")
        
        logger.info("Database scraping completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Database scraping failed: {str(e)}", exc_info=True)
        print(f"\n❌ Scraping failed: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 