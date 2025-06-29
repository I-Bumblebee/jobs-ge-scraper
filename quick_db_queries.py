#!/usr/bin/env python3
"""
Quick database queries to explore scraped job data.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config.database import SessionLocal, test_connection
from sqlalchemy import text


def run_query(query_name: str):
    """Run predefined queries."""
    
    if not test_connection():
        print("❌ Cannot connect to database!")
        return
    
    session = SessionLocal()
    
    queries = {
        "count": "SELECT COUNT(*) as total_jobs FROM job_listings",
        
        "platforms": """
            SELECT platform, COUNT(*) as job_count 
            FROM job_listings 
            GROUP BY platform 
            ORDER BY job_count DESC
        """,
        
        "companies": """
            SELECT company_name, platform, COUNT(*) as job_count 
            FROM job_listings 
            WHERE company_name IS NOT NULL 
            GROUP BY company_name, platform 
            ORDER BY job_count DESC 
            LIMIT 15
        """,
        
        "recent": """
            SELECT platform, title, company_name, scraped_date
            FROM job_listings 
            ORDER BY scraped_date DESC 
            LIMIT 10
        """,
        
        "jobs_ge": """
            SELECT title, company_name, published_date, url
            FROM job_listings 
            WHERE platform = 'jobs_ge'
            ORDER BY scraped_date DESC
            LIMIT 10
        """,
        
        "cv_ge": """
            SELECT title, company_name, city, url
            FROM job_listings 
            WHERE platform = 'cv_ge'
            ORDER BY scraped_date DESC
            LIMIT 10
        """,
        
        "hr_ge": """
            SELECT title, company_name, city, url
            FROM job_listings 
            WHERE platform = 'hr_ge'
            ORDER BY scraped_date DESC
            LIMIT 10
        """,
        
        "locations": """
            SELECT city, COUNT(*) as job_count
            FROM job_listings 
            WHERE city IS NOT NULL AND city != ''
            GROUP BY city 
            ORDER BY job_count DESC
            LIMIT 10
        """,
        
        "today": """
            SELECT platform, COUNT(*) as jobs_today
            FROM job_listings 
            WHERE DATE(scraped_date) = CURRENT_DATE
            GROUP BY platform
        """,
        
        "details": """
            SELECT 
                id, platform, title, company_name, city, 
                published_date, scraped_date
            FROM job_listings 
            ORDER BY scraped_date DESC 
            LIMIT 5
        """
    }
    
    if query_name not in queries:
        print(f"❌ Query '{query_name}' not found!")
        print(f"Available queries: {', '.join(queries.keys())}")
        return
    
    try:
        print(f"🔍 Running query: {query_name}")
        print("="*50)
        
        result = session.execute(text(queries[query_name]))
        rows = result.fetchall()
        
        if not rows:
            print("No results found.")
            return
        
        # Print headers
        columns = result.keys()
        print(" | ".join(f"{col:<20}" for col in columns))
        print("-" * (len(columns) * 23))
        
        # Print data
        for row in rows:
            values = []
            for val in row:
                if val is None:
                    values.append("NULL".ljust(20))
                else:
                    str_val = str(val)
                    if len(str_val) > 20:
                        str_val = str_val[:17] + "..."
                    values.append(str_val.ljust(20))
            print(" | ".join(values))
        
        print(f"\nTotal rows: {len(rows)}")
        
    except Exception as e:
        print(f"❌ Error running query: {e}")
    
    finally:
        session.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        query_name = sys.argv[1]
        run_query(query_name)
    else:
        print("🔍 Available Database Queries:")
        print("="*40)
        print("Usage: python quick_db_queries.py QUERY_NAME")
        print("\nAvailable queries:")
        print("  count      - Total job count")
        print("  platforms  - Jobs by platform")
        print("  companies  - Top companies")
        print("  recent     - Most recent jobs")
        print("  jobs_ge    - Jobs.ge listings")
        print("  cv_ge      - CV.ge listings")
        print("  hr_ge      - HR.ge listings")
        print("  locations  - Jobs by location")
        print("  today      - Jobs scraped today")
        print("  details    - Detailed job info")
        print("\nExample: python quick_db_queries.py platforms") 