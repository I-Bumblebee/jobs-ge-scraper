# CV.ge Scrapy Spider

A simple Scrapy spider for scraping job listings from cv.ge, the Georgian job portal.

## Features

- ✅ Scrapes job listings from cv.ge
- ✅ Uses existing cv_ge_parser for reliable data extraction
- ✅ Handles pagination (up to 24 pages)
- ✅ Respects rate limits with built-in delays
- ✅ Exports to JSON, CSV, or XML formats
- ✅ Configurable job count limit
- ✅ Built-in data validation and deduplication

## Quick Start

### 1. Basic Usage

Run the spider from the project root:

```bash
python run_cv_ge_spider.py --quick
```

This will scrape 5 jobs as a test.

### 2. Custom Job Count

```bash
python run_cv_ge_spider.py --max-jobs 20
```

### 3. Save to File

```bash
python run_cv_ge_spider.py --max-jobs 50 --output-format csv --output-file my_jobs
```

### 4. Direct Scrapy Command

You can also run the spider directly using Scrapy:

```bash
cd src/scrapers/scrapy_crawler
python -m scrapy crawl cv_ge -a max_jobs=10
```

## Command Line Options

- `--max-jobs`: Maximum number of jobs to scrape (default: 10)
- `--output-format`: Output format - json, csv, or xml (default: json)
- `--output-file`: Output file name without extension
- `--quick`: Quick test mode (scrapes 5 jobs)

## Output Format

The spider extracts the following information for each job:

```json
{
  "id": "417196",
  "platform": "CV_GE",
  "title": "Software Developer",
  "url": "https://www.cv.ge/announcement/417196/...",
  "company_name": "Tech Company",
  "company_url": "https://www.cv.ge/company/...",
  "location_city": "Tbilisi",
  "location_is_remote": false,
  "is_vip": true,
  "published_date": "2024-01-15T10:30:00",
  "deadline_date": "2024-02-15T23:59:59",
  "scraped_date": "2024-01-20T12:45:30"
}
```

## Configuration

The spider respects the following settings:

- **Download Delay**: 1 second between requests
- **Concurrent Requests**: Max 2 per domain
- **AutoThrottle**: Enabled for adaptive delays
- **Robots.txt**: Respects robots.txt rules
- **HTTP Caching**: Enabled for 1 hour

## Architecture

The spider leverages the existing project architecture:

```
cv.ge Spider Architecture
├── CvGeSpider (scrapy.Spider)
│   ├── Uses CvGeParser from existing codebase
│   ├── Converts JobListing objects to Scrapy Items
│   └── Handles pagination and rate limiting
├── JobValidationPipeline
│   ├── Validates required fields
│   └── Cleans data
└── JobStoragePipeline
    ├── Logs job information
    └── Handles output formatting
```

## Examples

### Example 1: Quick Test

```bash
python run_cv_ge_spider.py --quick
```

Output: Console logs with 5 jobs

### Example 2: Export to CSV

```bash
python run_cv_ge_spider.py --max-jobs 25 --output-format csv --output-file cv_jobs
```

Output: `cv_jobs.csv` with 25 jobs

### Example 3: Large Scraping Session

```bash
python run_cv_ge_spider.py --max-jobs 100 --output-format json --output-file full_scrape
```

Output: `full_scrape.json` with up to 100 jobs

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure you're running from the project root directory
2. **No Jobs Found**: Check if cv.ge is accessible and the site structure hasn't changed
3. **Rate Limiting**: The spider has built-in delays, but cv.ge may still rate limit aggressive scraping

### Debug Mode

Run with Scrapy's debug logging:

```bash
cd src/scrapers/scrapy_crawler
python -m scrapy crawl cv_ge -a max_jobs=5 -L DEBUG
```

### Spider Statistics

The spider provides detailed statistics at the end:

```
INFO: Spider closed (finished).
INFO: Crawled 5 requests
INFO: Scraped 5 items
INFO: CV.ge Spider closed. Total jobs scraped: 5
```

## Extending the Spider

To add more functionality:

1. **Custom Fields**: Edit `items.py` to add new fields
2. **Additional Parsing**: Modify `parse_job_detail()` for more detailed extraction
3. **Custom Pipelines**: Add new pipelines in `pipelines.py`
4. **Export Formats**: Scrapy supports many export formats out of the box

## Notes

- The spider respects cv.ge's robots.txt
- Built-in rate limiting prevents overloading the server
- Uses the existing cv_ge_parser for consistent data extraction
- Handles Georgian date formats and text encoding
- Automatically deduplicates jobs by ID
