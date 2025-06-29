# Contributions

## Recent Development (Current Final Project Phase)

### Mikheil Dzuliashvili - **mishodzuliashvili**

#### Core Infrastructure & Database

- **Feature:** Implemented async parser for jobs.ge with HTML and metadata extraction. [Link to PR](https://github.com/I-Bumblebee/jobs-ge-scraper/pull/1)
- **Refactor:** Extracted job ID logic to a helper function, added logging, and improved docstrings. [Link to Commit](https://github.com/I-Bumblebee/jobs-ge-scraper/commit/229e61cee2e4fcec99dc5d72b623a7d32a8fe0e3)
- **Feature:** Created a simple GUI using Tkinter to display the collected data. [Link to PR](https://github.com/I-Bumblebee/jobs-ge-scraper/pull/4)

#### CV.ge Scraper Development

- **Feature:** Implemented CV.ge scraper with job listing and detail parsing capabilities
- **Feature:** Added CV.ge parser for job listings and details extraction
- **Feature:** Extended job scraping capabilities by adding CV_GE platform and VIP job metadata flag
- **Enhancement:** Enhanced CV.ge scraping functionality with additional job configurations and multi-strategy support
- **Feature:** Added test script for CV.ge job details fetching functionality
- **Integration:** Registered CV.ge scraper in the scraper factory for enhanced job scraping capabilities
- **Testing:** Introduced comprehensive test suite for CV.ge scraper functionality, including basic and live scraping tests

#### Database Integration

- **Feature:** Introduced database utility script and configuration for PostgreSQL integration, including connection testing, table management, and custom query execution
- **Feature:** Added SQL initialization script for job scraping database and updated requirements.txt to include psycopg2-binary
- **Maintenance:** Updated .gitignore to include additional file patterns for Python, database, Docker, logs, IDE, OS, Jupyter Notebooks, pytest, and mypy

#### Scrapy Integration

- **Major Feature:** Introduced Scrapy integration for Jobs.ge scraper, including spider, items, pipelines, and comprehensive documentation for setup and usage
- **Feature:** Implemented initial Scrapy configuration and CV.ge spider for job listings scraping
- **Feature:** Added initial Scrapy crawler and spiders packages for job scraping
- **Documentation:** Added README.md for CV.ge Scrapy spider detailing features, usage, and configuration
- **Feature:** Implemented job processing pipelines for validation, storage, and duplicate filtering in Scrapy crawler
- **Feature:** Added custom spider and downloader middleware for Scrapy crawler, including user agent rotation and response logging
- **Feature:** Introduced JobItem and JobDetailItem classes for structured job data representation in Scrapy crawler
- **Feature:** Added script to run CV.ge Scrapy spider with command line interface for job scraping
- **Maintenance:** Updated .scrapy/ to .gitignore to exclude Scrapy-related files from version control

#### Dependencies & Maintenance

- **Maintenance:** Updated requirements.txt to include pandas and pyyaml dependencies
- **Maintenance:** Updated .gitignore to exclude log files and remove demo_scraping.log
- **Documentation:** Added details about contributions

### Luka Oniani - **lukabatoni**

#### Core Architecture & Design Patterns

- **Feature:** Added async Collector class for scraping jobs.ge with retries and rate limiting. [Link to PR](https://github.com/I-Bumblebee/jobs-ge-scraper/pull/2)
- **Documentation:** Added example usage to README.md. [Link to Commit](https://github.com/I-Bumblebee/jobs-ge-scraper/commit/c8c9fc4eb13f5d78e2dfc77258ce1cdbd1f4eb7d)

#### Multi-Platform Scraper System

- **Feature:** Added configuration for job scraping pipelines and enhanced pipeline processing logic
- **Feature:** Implemented a scraper for Jobs.ge with configuration and parsing logic
- **Architecture:** Introduced pipeline management system for coordinating multi-platform job scraping
- **Feature:** Implemented data models and base scraper for job scraping functionality
- **Feature:** Added configuration management and logging utilities for job scraping system
- **Architecture:** Initialized core modules for multi-platform job scraping system
- **Feature:** Added new main entry point for multi-platform job scraper, demonstrating Factory and Strategy design patterns
- **Feature:** Added logging and requirements files for job scraper demonstration
- **Documentation:** Added comprehensive project documentation and quick start guide for multi-platform job scraper

#### Data Visualization & Analytics

- **Feature:** Added chart generation functionality to visualize job data with various filters and options
- **Feature:** Added new job data visualization charts including distribution and timeline graphics
- **Feature:** Implemented HTML report generation for job market analysis with embedded charts and data tables
- **Maintenance:** Deleted outdated QUICK_START_GUIDE.md and README_NEW_ARCHITECTURE.md files to streamline documentation

#### Database Operations

- **Feature:** Implemented main database scraping script and quick query utility for job data exploration
- **Feature:** Added check_db_data script for database data verification and exploration

#### Documentation & Maintenance

- **Documentation:** Updated readme file
- **Maintenance:** Added pandas to requirements

### Luka Trapaidze - **I-Bumblebee**

#### Pipeline & Memory Management

- **Feature:** Composed collector and parser into a pipeline that uses generators and temporary files to be memory efficient [Link to PR](https://github.com/I-Bumblebee/jobs-ge-scraper/pull/3)
- **Refactor:** Used `asynccontextmanager` for coroutine control. [Link to Commit](https://github.com/I-Bumblebee/jobs-ge-scraper/commit/7fcd95768bfb5da7f47424f1e01b1cc2af69cbd6)
- **Feature:** Implemented atomic output manager to persist intermediate data on disk and compose final output. [Link to Commit](https://github.com/I-Bumblebee/jobs-ge-scraper/commit/a61107547c6fc1437bee1fc748f22fcd301020af)

#### HR.ge Scraper Development

- **Feature:** Added HR.ge module with full scraping capabilities
- **Integration:** Registered HR.ge scraper for multi-platform support
- **Testing:** Added HR.ge scraper test suite
- **Enhancement:** Renamed entrypoint file for better organization

#### CLI Interface & Database Integration

- **Feature:** Added CLI for Jobs Scraper with commands to display, export, and manage job data, including database statistics and custom queries
- **Refactor:** Replaced OutputManager with DatabaseOutputManager in JobPipeline and PipelineManager, removing file-based output handling for database integration
- **Feature:** Load environment variables from .env file for database configuration
- **Maintenance:** Deleted unused scripts and GUI components to streamline project structure

#### Code Quality & Maintenance

- **Maintenance:** Removed file saving logic from the parser
- **Maintenance:** Removed `is_favorite` data as it is not relevant to scraping
- **Maintenance:** Added .gitignore files
- **Maintenance:** Fixed typo in word `local` to `locale`
- **Maintenance:** Added requirements.txt
- **Maintenance:** Added example usage
- **Maintenance:** Squashed requirements.txt for better organization
- **Maintenance:** Deleted unused scripts and main_db.py to eliminate code duplication

#### Project Initialization

- **Foundation:** Initial project setup and repository initialization

---

## Original Contributions (Initial Phase)

### Mikheil Dzuliashvili - **mishodzuliashvili**

- **Feature:** Implemented async parser for jobs.ge with HTML and metadata extraction. [Link to PR](https://github.com/I-Bumblebee/jobs-ge-scraper/pull/1)
- **Refactor:** Extracted job ID logic to a helper function, added logging, and improved docstrings. [Link to Commit](https://github.com/I-Bumblebee/jobs-ge-scraper/commit/229e61cee2e4fcec99dc5d72b623a7d32a8fe0e3)
- **Feature:** Created a simple GUI using Tkinter to display the collected data. [Link to PR](https://github.com/I-Bumblebee/jobs-ge-scraper/pull/4)

### Luka Oniani - **lukabatoni**

- **Feature:** Added async Collector class for scraping jobs.ge with retries and rate limiting. [Link to PR](https://github.com/I-Bumblebee/jobs-ge-scraper/pull/2)
- **Added example usage to README.md.** [Link to Commit](https://github.com/I-Bumblebee/jobs-ge-scraper/commit/c8c9fc4eb13f5d78e2dfc77258ce1cdbd1f4eb7d)

### Luka Trapaidze - **I-Bumblebee**

- **Feature:** Composed collector and parser into a pipeline that uses generators and temporary files to be memory efficient [Link to PR](https://github.com/I-Bumblebee/jobs-ge-scraper/pull/3)
- **Refactor:** Used `asynccontextmanager` for coroutine control. [Link to Commit](https://github.com/I-Bumblebee/jobs-ge-scraper/commit/7fcd95768bfb5da7f47424f1e01b1cc2af69cbd6)
- **Implemented atomic output manager to persist intermediate data on disk and compose final output.** [Link to Commit](https://github.com/I-Bumblebee/jobs-ge-scraper/commit/a61107547c6fc1437bee1fc748f22fcd301020af)

---

## Summary

This project has evolved significantly from its initial concept to a comprehensive multi-platform job scraping system. Key achievements include:

- **Multi-Platform Support:** Complete integration of Jobs.ge, CV.ge, and HR.ge scrapers
- **Dual Architecture:** Both traditional async scraping and Scrapy framework integration
- **Database Integration:** Full PostgreSQL integration with proper data management
- **Data Visualization:** Advanced charting and HTML report generation capabilities
- **CLI Interface:** Comprehensive command-line interface for data management and analysis
- **Testing:** Extensive test coverage across all scraping platforms
- **Documentation:** Comprehensive documentation and setup guides

### Note

- All contributions are made to the `main` branch and `final-project` branch.
- For detailed information about each contribution, please refer to the respective pull requests and commits on GitHub.
- Recent development work primarily focuses on the `final-project` branch with regular merges to maintain code quality.
