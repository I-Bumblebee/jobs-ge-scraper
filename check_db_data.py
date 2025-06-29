#!/usr/bin/env python3
"""
Simple script to check and display scraped data from the database.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config.database import SessionLocal, test_connection
from sqlalchemy import text


def check_database_data():
    """Check and display scraped data from the database."""
    
    print("🔍 Checking Database Data")
    print("="*50)
    
    # Test connection
    if not test_connection():
        print("❌ Cannot connect to database!")
        return
    
    session = SessionLocal()
    
    try:
        # 1. Show table counts
        print("\n📊 Table Counts:")
        tables = ['job_listings', 'job_details', 'companies', 'scraping_results']
        for table in tables:
            count = session.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()[0]
            print(f"   • {table}: {count} records")
        
        # 2. Show jobs by platform
        print("\n🌐 Jobs by Platform:")
        result = session.execute(text("""
            SELECT platform, COUNT(*) as count 
            FROM job_listings 
            GROUP BY platform 
            ORDER BY count DESC
        """))
        for row in result:
            print(f"   • {row[0]}: {row[1]} jobs")
        
        # 3. Show sample job listings
        print("\n📋 Sample Job Listings (first 5):")
        result = session.execute(text("""
            SELECT platform, title, company_name, city, published_date 
            FROM job_listings 
            ORDER BY scraped_date DESC 
            LIMIT 5
        """))
        
        for i, row in enumerate(result, 1):
            platform, title, company, city, published = row
            published_str = published.strftime('%Y-%m-%d') if published else 'N/A'
            print(f"   {i}. [{platform.upper()}] {title}")
            print(f"      Company: {company or 'N/A'}")
            print(f"      Location: {city or 'N/A'}")
            print(f"      Published: {published_str}")
            print()
        
        # 4. Show recent scraping activity
        print("🕒 Recent Scraping Activity:")
        result = session.execute(text("""
            SELECT platform, COUNT(*) as count, MAX(scraped_date) as last_scraped
            FROM job_listings 
            WHERE scraped_date >= NOW() - INTERVAL '24 hours'
            GROUP BY platform
            ORDER BY last_scraped DESC
        """))
        
        for row in result:
            platform, count, last_scraped = row
            last_str = last_scraped.strftime('%Y-%m-%d %H:%M:%S') if last_scraped else 'N/A'
            print(f"   • {platform}: {count} jobs (last: {last_str})")
        
        # 5. Show companies with most jobs
        print("\n🏢 Top Companies (by job count):")
        result = session.execute(text("""
            SELECT company_name, COUNT(*) as job_count, platform
            FROM job_listings 
            WHERE company_name IS NOT NULL AND company_name != ''
            GROUP BY company_name, platform
            ORDER BY job_count DESC
            LIMIT 10
        """))
        
        for row in result:
            company, count, platform = row
            print(f"   • {company} ({platform}): {count} jobs")
        
        # 6. Show salary information (if any)
        print("\n💰 Salary Information:")
        result = session.execute(text("""
            SELECT COUNT(*) as total_jobs,
                   COUNT(CASE WHEN salary_min IS NOT NULL THEN 1 END) as jobs_with_salary
            FROM job_listings
        """))
        
        total, with_salary = result.fetchone()
        salary_percentage = (with_salary / total * 100) if total > 0 else 0
        print(f"   • Total jobs: {total}")
        print(f"   • Jobs with salary info: {with_salary} ({salary_percentage:.1f}%)")
        
        if with_salary > 0:
            result = session.execute(text("""
                SELECT platform, AVG(salary_min) as avg_min, AVG(salary_max) as avg_max, COUNT(*) as count
                FROM job_listings 
                WHERE salary_min IS NOT NULL 
                GROUP BY platform
            """))
            
            for row in result:
                platform, avg_min, avg_max, count = row
                print(f"   • {platform}: Avg salary {avg_min:.0f}-{avg_max:.0f} ({count} jobs)")
        
    except Exception as e:
        print(f"❌ Error querying database: {e}")
    
    finally:
        session.close()


def show_specific_table(table_name: str, limit: int = 10):
    """Show content of a specific table."""
    print(f"\n📋 Content of '{table_name}' table (first {limit} rows):")
    print("="*60)
    
    if not test_connection():
        print("❌ Cannot connect to database!")
        return
    
    session = SessionLocal()
    
    try:
        # Get column names first
        result = session.execute(text(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}' AND table_schema = 'public'
            ORDER BY ordinal_position
        """))
        columns = [row[0] for row in result]
        
        if not columns:
            print(f"❌ Table '{table_name}' not found or has no columns")
            return
        
        # Get actual data
        columns_str = ', '.join(columns)
        result = session.execute(text(f"SELECT {columns_str} FROM {table_name} LIMIT {limit}"))
        
        # Print headers
        print(" | ".join(f"{col:<15}" for col in columns[:6]))  # Show first 6 columns
        print("-" * 90)
        
        # Print data
        for row in result:
            values = []
            for i, val in enumerate(row[:6]):  # Show first 6 columns
                if val is None:
                    values.append("NULL".ljust(15))
                else:
                    str_val = str(val)
                    if len(str_val) > 15:
                        str_val = str_val[:12] + "..."
                    values.append(str_val.ljust(15))
            print(" | ".join(values))
    
    except Exception as e:
        print(f"❌ Error querying table '{table_name}': {e}")
    
    finally:
        session.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--table" and len(sys.argv) > 2:
            table_name = sys.argv[2]
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10
            show_specific_table(table_name, limit)
        else:
            print("Usage: python check_db_data.py [--table TABLE_NAME [LIMIT]]")
    else:
        check_database_data() 