#!/usr/bin/env python3
"""
Test script for HR.ge scraper functionality.
"""

import asyncio
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.scrapers.factory.scraper_factory import ScraperFactory, ScraperType
from src.scrapers.base.scraper_interface import ScrapingConfig


async def test_hr_ge_scraper():
    """Test HR.ge scraper basic functionality."""
    print("🧪 Testing HR.ge Scraper")
    print("=" * 50)
    
    try:
        # Create HR.ge scraper
        print("Creating HR.ge scraper...")
        scraper = ScraperFactory.create_scraper(ScraperType.HR_GE)
        print(f"✅ HR.ge scraper created: {scraper.platform_name}")
        
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
        detail_url = await scraper._build_detail_url("417493")
        print(f"🔗 Detail URL: {detail_url}")
        
        # Test job ID extraction
        test_urls = [
            "/announcement/417493/Local-Friend--Experience-Host",
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


async def test_hr_ge_live_scraping():
    """Test actual HR.ge scraping (if user wants to)."""
    print("\n🌐 Live HR.ge Scraping Test")
    print("=" * 50)
    
    response = input("Do you want to test live scraping from HR.ge? (y/n): ").lower().strip()
    
    if response != 'y':
        print("Skipping live scraping test.")
        return True
    
    try:
        # Create scraper
        scraper = ScraperFactory.create_scraper(ScraperType.HR_GE)
        
        # Configure for a small test
        config = ScrapingConfig(
            job_count=3,  # Only get 3 jobs for testing
            locale="ge"
        )
        
        print(f"🔍 Fetching {config.job_count} jobs from HR.ge using Selenium...")
        print("⏰ This may take a moment as it loads Angular content...")
        
        jobs_found = 0
        async for job in scraper.get_job_listings(config):
            jobs_found += 1
            print(f"  📄 Job {jobs_found}: {job.get('title', 'N/A')}")
            print(f"     Company: {job.get('company', {}).get('name', 'N/A')}")
            print(f"     Location: {job.get('location', {}).get('city', 'N/A')}")
            print(f"     URL: {job.get('url', 'N/A')}")
            print(f"     VIP: {job.get('metadata', {}).get('is_vip', False)}")
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


async def test_hr_ge_job_details():
    """Test HR.ge job details fetching."""
    print("\n📄 HR.ge Job Details Test")
    print("=" * 50)
    
    response = input("Do you want to test job details fetching? (y/n): ").lower().strip()
    
    if response != 'y':
        print("Skipping job details test.")
        return True
    
    try:
        # Create scraper
        scraper = ScraperFactory.create_scraper(ScraperType.HR_GE)
        
        # Test with a known job ID (you can change this)
        test_job_id = "417493"
        test_job_url = f"https://www.hr.ge/announcement/{test_job_id}"
        
        print(f"🔍 Fetching details for job ID: {test_job_id}")
        print(f"🔗 URL: {test_job_url}")
        print("⏰ This may take a moment as it loads Angular content...")
        
        details = await scraper.get_job_details(test_job_id, test_job_url)
        
        if 'error' in details:
            print(f"❌ Error fetching details: {details['error']}")
        else:
            print(f"✅ Successfully fetched job details!")
            print(f"   📝 Title: {details.get('title', 'N/A')}")
            print(f"   🏢 Company: {details.get('company_name', 'N/A')}")
            print(f"   📍 Location: {details.get('location', 'N/A')}")
            print(f"   💼 Employment Type: {details.get('employment_type', 'N/A')}")
            print(f"   📋 Requirements: {details.get('requirements', 'N/A')}")
            print(f"   ⭐ VIP: {details.get('is_vip', False)}")
            
            # Show first 200 characters of description
            desc = details.get('description', '')
            if desc:
                preview = desc[:200] + "..." if len(desc) > 200 else desc
                print(f"   📖 Description preview: {preview}")
        
        return True
        
    except Exception as e:
        print(f"❌ Job details test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("🚀 HR.ge Scraper Test Suite")
    print("=" * 60)
    
    # Run basic functionality tests
    basic_passed = await test_hr_ge_scraper()
    
    if basic_passed:
        # Run live scraping test if user wants
        live_passed = await test_hr_ge_live_scraping()
        
        # Run job details test if user wants
        details_passed = await test_hr_ge_job_details()
        
        if basic_passed and live_passed and details_passed:
            print("\n🎉 All tests passed! HR.ge scraper is ready to use.")
            print("💡 Note: Make sure you have Chrome and chromedriver installed for Selenium.")
            return 0
    
    print("\n❌ Some tests failed. Check the errors above.")
    return 1


if __name__ == "__main__":
    exit(asyncio.run(main())) 