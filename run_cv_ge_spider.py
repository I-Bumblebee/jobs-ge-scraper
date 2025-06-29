#!/usr/bin/env python3
"""
Simple script to run the CV.ge Scrapy spider.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_cv_ge_spider(max_jobs=10, output_format='json', output_file=None):
    """Run the CV.ge Scrapy spider with specified parameters."""
    
    # Change to the scrapy_crawler directory
    scrapy_dir = Path(__file__).parent / "src" / "scrapers" / "scrapy_crawler"
    
    if not scrapy_dir.exists():
        print(f"❌ Scrapy directory not found: {scrapy_dir}")
        return False
    
    print(f"🚀 Running CV.ge Spider")
    print(f"📁 Working directory: {scrapy_dir}")
    print(f"🎯 Max jobs: {max_jobs}")
    print(f"📄 Output format: {output_format}")
    
    # Build scrapy command
    cmd = [
        sys.executable, "-m", "scrapy", "crawl", "cv_ge",
        "-a", f"max_jobs={max_jobs}"
    ]
    
    # Add output options
    if output_file:
        if output_format == 'json':
            cmd.extend(["-o", f"{output_file}.json"])
        elif output_format == 'csv':
            cmd.extend(["-o", f"{output_file}.csv"])
        elif output_format == 'xml':
            cmd.extend(["-o", f"{output_file}.xml"])
    
    print(f"🔧 Command: {' '.join(cmd)}")
    print("=" * 60)
    
    try:
        # Change to scrapy directory
        original_cwd = os.getcwd()
        os.chdir(scrapy_dir)
        
        # Run scrapy
        result = subprocess.run(cmd, capture_output=False, text=True)
        
        # Return to original directory
        os.chdir(original_cwd)
        
        if result.returncode == 0:
            print("\n✅ Spider completed successfully!")
            if output_file:
                print(f"📁 Output saved to: {output_file}.{output_format}")
            return True
        else:
            print(f"\n❌ Spider failed with return code: {result.returncode}")
            return False
            
    except Exception as e:
        print(f"❌ Error running spider: {str(e)}")
        os.chdir(original_cwd)  # Make sure we return to original directory
        return False


def main():
    """Main function with command line interface."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run CV.ge Scrapy Spider")
    parser.add_argument("--max-jobs", type=int, default=10, 
                        help="Maximum number of jobs to scrape (default: 10)")
    parser.add_argument("--output-format", choices=['json', 'csv', 'xml'], default='json',
                        help="Output format (default: json)")
    parser.add_argument("--output-file", type=str, 
                        help="Output file name (without extension)")
    parser.add_argument("--quick", action="store_true",
                        help="Quick test with 5 jobs")
    
    args = parser.parse_args()
    
    # Quick test mode
    if args.quick:
        args.max_jobs = 5
        print("🏃‍♂️ Quick test mode: scraping 5 jobs")
    
    # Set default output file if not specified
    if not args.output_file and args.output_format != 'json':
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output_file = f"cv_ge_jobs_{timestamp}"
    
    success = run_cv_ge_spider(
        max_jobs=args.max_jobs,
        output_format=args.output_format,
        output_file=args.output_file
    )
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main() 