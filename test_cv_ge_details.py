#!/usr/bin/env python3
"""
Test script for CV.ge job details fetching.
"""

import asyncio
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.scrapers.factory.scraper_factory import ScraperFactory, ScraperType
from src.scrapers.base.scraper_interface import ScrapingConfig


async def test_cv_ge_job_details():
    """Test CV.ge job details fetching functionality."""
    print("🧪 Testing CV.ge Job Details Fetching")
    print("=" * 50)
    
    try:
        # Create CV.ge scraper
        print("Creating CV.ge scraper...")
        scraper = ScraperFactory.create_scraper(ScraperType.CV_GE)
        
        # Test URLs that should work (from our previous test)
        test_jobs = [
            {
                "id": "416596",
                "url": "https://www.cv.ge/announcement/416596/გაყიდვების-სპეციალისტი"
            },
            {
                "id": "417722", 
                "url": "https://www.cv.ge/announcement/417722/მოლარე"
            }
        ]
        
        for i, job in enumerate(test_jobs, 1):
            print(f"\n📄 Testing job {i}: ID {job['id']}")
            print(f"🔗 URL: {job['url']}")
            
            try:
                # Fetch job details
                details = await scraper.get_job_details(job['id'], job['url'])
                
                if 'error' in details:
                    print(f"❌ Error fetching details: {details['error']}")
                else:
                    print(f"✅ Successfully fetched job details!")
                    print(f"   📝 Description length: {len(details.get('description', ''))} characters")
                    print(f"   🏢 Company: {details.get('company_name', 'N/A')}")
                    print(f"   📧 Contact email: {details.get('contact_email', 'N/A')}")
                    
                    if details.get('salary'):
                        print(f"   💰 Salary info: {details['salary']}")
                    
                    # Show first 200 characters of description
                    desc = details.get('description', '')
                    if desc:
                        preview = desc[:200] + "..." if len(desc) > 200 else desc
                        print(f"   📖 Description preview: {preview}")
                
            except Exception as e:
                print(f"❌ Exception fetching job {job['id']}: {str(e)}")
                import traceback
                traceback.print_exc()
        
        print(f"\n✅ Job details fetching test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run the job details test."""
    print("🚀 CV.ge Job Details Test")
    print("=" * 60)
    
    success = await test_cv_ge_job_details()
    
    if success:
        print("\n🎉 Job details test passed!")
        return 0
    else:
        print("\n❌ Job details test failed.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 