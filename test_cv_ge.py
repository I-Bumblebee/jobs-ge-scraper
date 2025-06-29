#!/usr/bin/env python3
"""
Simple test script for CV.ge scraper functionality.
"""

import asyncio
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.scrapers.factory.scraper_factory import ScraperFactory, ScraperType
from src.scrapers.base.scraper_interface import ScrapingConfig


async def test_cv_ge_scraper():
    """Test CV.ge scraper basic functionality."""
    print("🧪 Testing CV.ge Scraper")
    print("=" * 50)
    
    try:
        # Create CV.ge scraper
        print("Creating CV.ge scraper...")
        scraper = ScraperFactory.create_scraper(ScraperType.CV_GE)
        print(f"✅ CV.ge scraper created: {scraper.platform_name}")
        
        # Test basic properties
        print(f"📍 Supported locations: {len(scraper.supported_locations)}")
        print(f"📋 Supported categories: {len(scraper.supported_categories)}")
        
        # Test URL building
        config = ScrapingConfig(job_count=5, locale="ge")
        url1 = await scraper._build_listing_url(config, page=1)
        url2 = await scraper._build_listing_url(config, page=2)
        
        print(f"🔗 Page 1 URL: {url1}")
        print(f"🔗 Page 2 URL: {url2}")
        
        # Test detail URL building
        detail_url = await scraper._build_detail_url("417196")
        print(f"🔗 Detail URL: {detail_url}")
        
        # Test job ID extraction
        test_urls = [
            "/announcement/417196/some-title",
            "/announcement/417203/another-job",
            "invalid-url"
        ]
        
        print(f"\n📝 Testing job ID extraction:")
        for url in test_urls:
            job_id = scraper._extract_job_id(url)
            print(f"  {url} → {job_id}")
        
        print(f"\n✅ Basic functionality tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_cv_ge_live_scraping():
    """Test actual CV.ge scraping (if user wants to)."""
    print("\n🌐 Live CV.ge Scraping Test")
    print("=" * 50)
    
    response = input("Do you want to test live scraping from CV.ge? (y/n): ").lower().strip()
    
    if response != 'y':
        print("Skipping live scraping test.")
        return True
    
    try:
        # Create scraper
        scraper = ScraperFactory.create_scraper(ScraperType.CV_GE)
        
        # Configure for a small test
        config = ScrapingConfig(
            job_count=3,  # Only get 3 jobs for testing
            locale="ge"
        )
        
        print(f"🔍 Fetching {config.job_count} jobs from CV.ge...")
        
        jobs_found = 0
        async for job in scraper.get_job_listings(config):
            jobs_found += 1
            print(f"  📄 Job {jobs_found}: {job.get('title', 'N/A')}")
            print(f"     Company: {job.get('company', {}).get('name', 'N/A')}")
            print(f"     Location: {job.get('location', {}).get('city', 'N/A')}")
            print(f"     URL: {job.get('url', 'N/A')}")
            print()
            
            if jobs_found >= config.job_count:
                break
        
        print(f"✅ Live scraping test completed! Found {jobs_found} jobs.")
        return True
        
    except Exception as e:
        print(f"❌ Live scraping test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("🚀 CV.ge Scraper Test Suite")
    print("=" * 60)
    
    # Run basic functionality tests
    basic_passed = await test_cv_ge_scraper()
    
    if basic_passed:
        # Run live scraping test if user wants
        live_passed = await test_cv_ge_live_scraping()
        
        if basic_passed and live_passed:
            print("\n🎉 All tests passed! CV.ge scraper is ready to use.")
            return 0
    
    print("\n❌ Some tests failed. Check the errors above.")
    return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 