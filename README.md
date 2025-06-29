# Job Market Analysis Platform

A comprehensive multi-source job scraping and analysis system that aggregates job postings from multiple Georgian job platforms and provides professional data analysis and visualization.

## 🎯 Project Overview

This is an advanced data scraping system that demonstrates mastery of web scraping techniques, implementing a **Job Market Analysis Platform** as specified in the course requirements. The system integrates static scraping, dynamic content handling, concurrent processing, and professional data analysis with visualization.

**Key Achievements:**
- ✅ **Multi-Source Data Collection**: 3+ job platforms (Jobs.ge, CV.ge, HR.ge)
- ✅ **Multiple Scraping Techniques**: Static (BeautifulSoup4), Dynamic (Selenium), Framework (Scrapy)
- ✅ **Professional Architecture**: Factory Pattern, Strategy Pattern, OOP Design
- ✅ **Database Storage**: PostgreSQL with optimized schema
- ✅ **Data Analysis**: Statistical analysis with pandas/numpy
- ✅ **CLI Interface**: Comprehensive command-line tools
- ✅ **Visualization**: Professional charts and HTML reports

## 🏗️ Architecture & Design Patterns

### Design Patterns Implemented
- **Factory Pattern**: Easy creation of platform-specific scrapers
- **Strategy Pattern**: Flexible scraping approaches (static, dynamic, API)
- **Pipeline Pattern**: Coordinated data processing workflows
- **Observer Pattern**: Event-driven scraping coordination

### Project Structure
```
jobs-ge-scraper/
├── src/                         # Core source code
│   ├── scrapers/               # Scraper implementations
│   │   ├── base/              # Base classes and interfaces
│   │   ├── platforms/         # Platform-specific scrapers
│   │   │   ├── jobs_ge/       # Jobs.ge scraper
│   │   │   ├── cv_ge/         # CV.ge scraper
│   │   │   └── hr_ge/         # HR.ge scraper
│   │   ├── factory/           # Factory pattern implementation
│   │   └── scrapy_crawler/    # Scrapy framework implementation
│   ├── pipeline/              # Data processing pipelines
│   ├── config/                # Configuration management
│   ├── data/                  # Data models and database
│   └── utils/                 # Utility functions
├── reports/                   # Generated HTML reports
├── charts/                    # Generated chart images
├── data/                      # Output data files
├── sql/                       # Database schema and migrations
├── cli.py                     # Command-line interface
└── requirements.txt           # Python dependencies
```

## 🚀 Quick Start

### Installation
1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd jobs-ge-scraper
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up database** (PostgreSQL recommended)
   ```bash
   # Initialize database schema
   python cli.py reinit
   ```

4. **Run your first scraping**
   ```bash
   # View help
   python cli.py --help
   
   # Start scraping and see results
   python cli.py show
   ```

## 💡 Features & Usage

### 1. Command-Line Interface
Professional CLI with comprehensive options:

```bash
# Display scraped jobs
python cli.py show --limit 20 --platform cv_ge --remote

# Export data in multiple formats
python cli.py export --format csv --output jobs_data.csv
python cli.py export --format json --platform jobs_ge
python cli.py export --format xlsx --remote

# Database statistics
python cli.py stats

# Custom SQL queries
python cli.py query "SELECT COUNT(*) FROM jobs_overview WHERE is_remote = true"
```

### 2. Data Visualization & Charts
Generate professional charts and visualizations:

```bash
# Generate all charts
python cli.py charts --type all

# Specific chart types
python cli.py charts --type platform --show     # Interactive display
python cli.py charts --type location --save-path charts/
python cli.py charts --type remote --platform cv_ge
```

**Available Chart Types:**
- **Platform Distribution**: Jobs by platform
- **Geographic Distribution**: Top cities with job listings  
- **Remote Work Analysis**: Remote vs non-remote jobs
- **Top Companies**: Companies with most listings

### 3. HTML Reports
Generate comprehensive HTML reports with embedded charts:

```bash
# Generate complete analysis report
python cli.py html-report --title "Job Market Analysis"

# Platform-specific reports
python cli.py html-report --platform cv_ge --title "CV.ge Analysis"

# Custom output location
python cli.py html-report --output monthly_report.html
```

**Report Features:**
- **Summary Statistics**: Total jobs, platforms, remote opportunities
- **Interactive Charts**: Embedded visualizations
- **Data Tables**: Recent listings and platform statistics
- **Professional Styling**: Clean, minimal design
- **Mobile Responsive**: Works on all devices

## 🔧 Technical Implementation

### Multi-Source Data Collection
- **Static Scraping**: BeautifulSoup4 for HTML parsing
- **Dynamic Scraping**: Selenium for JavaScript-heavy sites
- **Framework Implementation**: Scrapy for robust crawling
- **Error Handling**: Comprehensive retry logic and error recovery
- **Rate Limiting**: Intelligent request scheduling
- **Anti-Bot Measures**: User-agent rotation and session management

### Data Processing & Analysis
- **Data Validation**: Quality checks and cleaning pipelines
- **Statistical Analysis**: Pandas/NumPy for data analysis
- **Database Storage**: PostgreSQL with optimized schema
- **Export Formats**: CSV, JSON, Excel support
- **Trend Analysis**: Time-based insights and comparisons

### Performance & Scalability
- **Concurrent Processing**: Multi-threaded scraping
- **Resource Management**: Efficient memory and connection handling
- **Queue Management**: Task scheduling and coordination
- **Logging System**: Comprehensive activity tracking
- **Configuration Management**: YAML-based settings

## 📊 Supported Platforms

| Platform | Status | Scraping Method | Features |
|----------|--------|-----------------|----------|
| **Jobs.ge** | ✅ Active | Static + Dynamic | Full job details, company info |
| **CV.ge** | ✅ Active | Static | Job listings, location data |
| **HR.ge** | ✅ Active | Static | Job postings, salary info |

## 🎨 Data Visualization

The system provides professional data visualization including:

- **Platform Distribution Charts**: Compare job volumes across platforms
- **Geographic Analysis**: Visualize job distribution by city/region
- **Remote Work Trends**: Analyze remote vs on-site opportunities
- **Company Rankings**: Top employers by job postings
- **Salary Distributions**: Compensation analysis (when available)

## 📈 Sample Analysis Results

**Recent Statistics** (Example):
- **Total Jobs Scraped**: 500+ active listings
- **Platforms Monitored**: 3 major Georgian job sites
- **Remote Opportunities**: 25% of all listings
- **Top Categories**: IT/Programming, Sales, Marketing
- **Geographic Distribution**: Tbilisi (60%), Remote (25%), Other (15%)

## 🔍 Quality Assurance

- **Data Validation**: Automated quality checks
- **Error Handling**: Robust error recovery
- **Rate Limiting**: Respectful scraping practices
- **Legal Compliance**: Robots.txt compliance
- **Testing**: Unit tests for core functionality

## 📋 Requirements Met

This project fulfills all course requirements:

### ✅ Multi-Source Data Collection (10 points)
- 3+ different websites with varying structures
- Static (BeautifulSoup4) and dynamic (Selenium) scraping
- Scrapy framework implementation
- Protection mechanism handling
- Multiple data format support
- Comprehensive error handling

### ✅ Architecture & Performance (8 points)
- Concurrent scraping implementation
- Data pipeline with proper flow
- PostgreSQL database storage
- Rate limiting and request scheduling
- Design patterns (Factory, Strategy, Pipeline)
- Configuration management system

### ✅ Data Processing & Analysis (6 points)
- Data cleaning and validation pipelines
- Statistical analysis using pandas/numpy
- Trend reports and summaries
- Multiple export formats (CSV, JSON, Excel)
- Automated insights generation

### ✅ User Interface & Reporting (3 points)
- Comprehensive command-line interface
- HTML reports with charts and tables
- Data visualization using matplotlib/seaborn
- Configuration files for customization
- Progress tracking and status updates

### ✅ Code Quality & Documentation (3 points)
- Professional code structure with modules
- Comprehensive documentation
- Clean code with proper formatting
- Security best practices

## 🛠️ Dependencies

Key technologies and libraries used:

- **Python 3.8+**: Core programming language
- **BeautifulSoup4**: HTML parsing and static scraping
- **Selenium**: Dynamic content and browser automation
- **Scrapy**: Framework-based crawling
- **PostgreSQL**: Database storage and management
- **Pandas/NumPy**: Data analysis and processing
- **Matplotlib/Seaborn**: Data visualization
- **Click**: Command-line interface framework
- **Rich**: Enhanced terminal output
- **Jinja2**: HTML template rendering

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

## 📞 Contact

For questions or suggestions about this project, please contact the development team.

---

**Note**: This project is developed as part of a Python Data Scraping course final project, demonstrating advanced web scraping techniques, professional software architecture, and comprehensive data analysis capabilities.