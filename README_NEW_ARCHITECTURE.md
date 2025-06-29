# Multi-Platform Job Scraper

A flexible, extensible job scraping system built with Factory and Strategy design patterns, supporting multiple job platforms with OOP principles.

## 🏗️ Architecture Overview

This project implements a clean, modular architecture using proven design patterns:

- **Factory Pattern**: Easy creation of platform-specific scrapers
- **Strategy Pattern**: Flexible scraping approaches (static, dynamic, API)
- **Pipeline Pattern**: Coordinated data processing workflows
- **OOP Design**: Clean inheritance, abstraction, and encapsulation

## 📁 Project Structure

```
src/
├── scrapers/                    # Scraper implementations
│   ├── base/                   # Base classes and interfaces
│   │   ├── scraper_interface.py    # Scraper interface definition
│   │   ├── base_scraper.py         # Base scraper implementation
│   │   └── scraper_strategy.py     # Strategy pattern implementation
│   ├── platforms/              # Platform-specific implementations
│   │   ├── jobs_ge/           # Jobs.ge scraper
│   │   ├── indeed/            # Indeed scraper (template)
│   │   └── linkedin/          # LinkedIn scraper (template)
│   └── factory/               # Factory pattern implementation
│       └── scraper_factory.py    # Scraper factory
├── data/                      # Data models and database
│   ├── models.py             # Platform-agnostic data models
│   └── database.py           # Database management (future)
├── pipeline/                 # Pipeline management
│   ├── job_pipeline.py       # Main pipeline coordinator
│   └── pipeline_manager.py   # Multi-pipeline manager
├── config/                   # Configuration management
│   ├── settings.py           # Application settings
│   └── platform_configs.py   # Platform-specific configs
└── utils/                    # Utility functions
    ├── output_manager.py     # Enhanced output management
    └── logger.py            # Logging utilities
```

## 🚀 Key Features

### 1. Factory Pattern Implementation
```python
from src.scrapers.factory.scraper_factory import ScraperFactory, ScraperType

# Easy scraper creation
scraper = ScraperFactory.create_scraper(ScraperType.JOBS_GE)
indeed_scraper = ScraperFactory.create_scraper(ScraperType.INDEED)  # When implemented
```

### 2. Strategy Pattern for Scraping Methods
```python
from src.scrapers.factory.scraper_factory import ScraperFactory

# Different strategies for different needs
static_strategy = ScraperFactory.create_strategy("static", max_concurrent=5)
dynamic_strategy = ScraperFactory.create_strategy("dynamic", headless=True)
api_strategy = ScraperFactory.create_strategy("api", api_key="your_key")

# Use strategies with scrapers
scraper = ScraperFactory.create_scraper(ScraperType.JOBS_GE, strategy=static_strategy)
```

### 3. Multi-Platform Pipeline System
```python
from src.pipeline.pipeline_manager import PipelineManager
from src.scrapers.factory.scraper_factory import ScraperType

manager = PipelineManager()

# Create pipeline for multiple platforms
pipeline = manager.create_pipeline(
    name="multi_platform_jobs",
    platforms=[ScraperType.JOBS_GE, ScraperType.INDEED],
    config=ScrapingConfig(job_count=100)
)

# Run the pipeline
results = await manager.run_pipeline("multi_platform_jobs")
```

### 4. Flexible Configuration System
```python
from src.config.settings import PipelineSettings, SettingsManager

# Create and save configurations
settings = PipelineSettings(
    job_count=50,
    platforms=["jobs_ge"],
    category_id="6",  # IT/Programming
    has_salary=True
)

manager = SettingsManager()
manager.save_pipeline_settings("it_jobs", settings)
```

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd jobs-ge-scraper
   ```

2. **Install dependencies**
   ```bash
   pip install -r src/requirements.txt
   ```

3. **Run the demonstration**
   ```bash
   python new_main.py
   ```

## 💡 Usage Examples

### Basic Scraping
```python
import asyncio
from src.scrapers.factory.scraper_factory import ScraperFactory, ScraperType
from src.scrapers.base.scraper_interface import ScrapingConfig

async def basic_scraping():
    # Create scraper
    scraper = ScraperFactory.create_scraper(ScraperType.JOBS_GE)
    
    # Configure scraping
    config = ScrapingConfig(
        job_count=20,
        location_id="17",  # Remote jobs
        category_id="6",   # IT/Programming
        has_salary=True
    )
    
    # Scrape jobs
    async for job in scraper.get_job_listings(config):
        print(f"Found job: {job['title']} at {job['company']['name']}")

asyncio.run(basic_scraping())
```

### Advanced Pipeline Usage
```python
import asyncio
from src.pipeline.pipeline_manager import PipelineManager
from src.scrapers.base.scraper_interface import ScrapingConfig
from src.scrapers.factory.scraper_factory import ScraperType

async def advanced_pipeline():
    manager = PipelineManager(base_output_dir="data/my_output")
    
    # Create multiple pipelines
    configs = {
        "it_remote": ScrapingConfig(
            job_count=50,
            category_id="6",
            location_id="17",
            has_salary=True
        ),
        "finance_tbilisi": ScrapingConfig(
            job_count=30,
            category_id="3",
            location_id="1"
        )
    }
    
    for name, config in configs.items():
        manager.create_pipeline(
            name=name,
            platforms=[ScraperType.JOBS_GE],
            config=config
        )
    
    # Run all pipelines concurrently
    results = await manager.run_all_pipelines()
    
    for pipeline_name, result in results.items():
        print(f"{pipeline_name}: {result['total_jobs_found']} jobs found")

asyncio.run(advanced_pipeline())
```

## 🔧 Adding New Platforms

Adding support for a new job platform is straightforward:

### 1. Create Platform Scraper
```python
# src/scrapers/platforms/new_platform/new_platform_scraper.py
from ...base.base_scraper import BaseScraper
from ....data.models import JobListing, Platform

class NewPlatformScraper(BaseScraper):
    @property
    def platform_name(self) -> str:
        return "New Platform"
    
    async def _build_listing_url(self, config, page=1) -> str:
        # Build URL for listings
        pass
    
    async def _parse_job_listing(self, soup) -> List[JobListing]:
        # Parse job listings
        pass
    
    # Implement other required methods...
```

### 2. Register with Factory
```python
# src/scrapers/factory/scraper_factory.py
from ..platforms.new_platform.new_platform_scraper import NewPlatformScraper

# Add to registration function
ScraperFactory.register_scraper(ScraperType.NEW_PLATFORM, NewPlatformScraper)
```

### 3. Use Immediately
```python
# Now available for use!
scraper = ScraperFactory.create_scraper(ScraperType.NEW_PLATFORM)
```

## 📊 Output Formats

The system supports multiple output formats:
- **JSON**: Complete job data with all fields
- **CSV**: Tabular format for spreadsheet analysis
- **Summary Reports**: Statistical analysis and insights
- **Individual Descriptions**: Separate HTML files for job descriptions

## 🔍 Platform Support

Currently implemented:
- ✅ **Jobs.ge**: Complete implementation with static scraping
- 🚧 **Indeed**: Template ready for implementation
- 🚧 **LinkedIn**: Template ready for implementation
- 🚧 **Glassdoor**: Template ready for implementation

## 🧪 Testing

```bash
# Run the demonstration to see all features
python new_main.py

# The demo includes:
# - Factory pattern demonstration
# - Strategy pattern examples
# - Configuration management
# - Optional live scraping
```

## 📝 Configuration

### Global Settings
```yaml
# config/global.yaml
log_level: INFO
base_output_dir: data/output
default_timeout: 30
enable_caching: true
```

### Pipeline Settings
```yaml
# config/pipelines.yaml
pipelines:
  it_jobs:
    job_count: 50
    platforms: ["jobs_ge"]
    category_id: "6"
    has_salary: true
    locale: "ge"
```

## 🔄 Migration from Old System

To migrate from the old system:

1. **Replace imports**:
   ```python
   # Old
   from scraper.pipeline import Pipeline
   
   # New
   from src.pipeline.pipeline_manager import PipelineManager
   ```

2. **Update configuration**:
   ```python
   # Old
   pipeline = Pipeline(output_dir="data", job_count=20)
   
   # New
   manager = PipelineManager()
   pipeline = manager.create_pipeline(
       name="migration",
       platforms=[ScraperType.JOBS_GE],
       config=ScrapingConfig(job_count=20)
   )
   ```

3. **Run with new system**:
   ```python
   # Old
   await pipeline.run()
   
   # New
   results = await manager.run_pipeline("migration")
   ```

## 🤝 Contributing

1. Follow the existing patterns (Factory, Strategy, OOP)
2. Add comprehensive tests for new platforms
3. Update documentation
4. Ensure backward compatibility where possible

## 📚 Design Patterns Used

- **Factory Pattern**: `ScraperFactory` creates appropriate scrapers
- **Strategy Pattern**: Different scraping strategies (static, dynamic, API)
- **Pipeline Pattern**: `JobPipeline` coordinates data flow
- **Template Method**: `BaseScraper` defines scraping workflow
- **Observer Pattern**: Logging system for monitoring operations

## 🏆 Benefits of New Architecture

1. **Extensibility**: Easy to add new platforms
2. **Maintainability**: Clean separation of concerns
3. **Testability**: Modular design enables unit testing
4. **Flexibility**: Multiple strategies for different scenarios
5. **Scalability**: Pipeline system supports concurrent operations
6. **Configuration**: Flexible settings management
7. **Monitoring**: Comprehensive logging and reporting

This architecture is designed to grow with your needs while maintaining clean, professional code standards. 