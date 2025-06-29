# 🚀 Quick Start Guide - New Architecture

## Installation & Setup
```bash
# Install dependencies
pip install -r src/requirements.txt

# Run the interactive demo
python new_main.py
```

## Basic Usage

### Old Way (Before Refactoring)
```python
from scraper.pipeline import Pipeline

pipeline = Pipeline(
    output_dir="data/output",
    job_count=20,
    locale="ge",
    category_id="6"  # IT jobs
)
await pipeline.run()
```

### New Way (After Refactoring)
```python
from src.pipeline.pipeline_manager import PipelineManager
from src.scrapers.factory.scraper_factory import ScraperType
from src.scrapers.base.scraper_interface import ScrapingConfig

# Create pipeline manager
manager = PipelineManager(base_output_dir="data/output")

# Create pipeline with Factory pattern
pipeline = manager.create_pipeline(
    name="it_jobs",
    platforms=[ScraperType.JOBS_GE],  # Easy to add more platforms!
    config=ScrapingConfig(
        job_count=20,
        locale="ge",
        category_id="6"
    )
)

# Run the pipeline
results = await manager.run_pipeline("it_jobs")
```

## Adding New Platforms

### Step 1: Create Scraper Class
```python
# src/scrapers/platforms/indeed/indeed_scraper.py
from ...base.base_scraper import BaseScraper

class IndeedScraper(BaseScraper):
    @property
    def platform_name(self) -> str:
        return "Indeed"
    
    async def _build_listing_url(self, config, page=1) -> str:
        # Build Indeed URL
        return f"https://indeed.com/jobs?q={config.query}"
    
    async def _parse_job_listing(self, soup) -> List[JobListing]:
        # Parse Indeed jobs
        pass
```

### Step 2: Register with Factory
```python
# In scraper_factory.py
ScraperFactory.register_scraper(ScraperType.INDEED, IndeedScraper)
```

### Step 3: Use Immediately
```python
# Multi-platform scraping!
pipeline = manager.create_pipeline(
    name="multi_platform",
    platforms=[ScraperType.JOBS_GE, ScraperType.INDEED],
    config=ScrapingConfig(job_count=50)
)
```

## Strategy Pattern Usage

```python
# Different strategies for different needs
static_strategy = ScraperFactory.create_strategy("static")      # Fast, simple
dynamic_strategy = ScraperFactory.create_strategy("dynamic")    # JavaScript support
api_strategy = ScraperFactory.create_strategy("api")           # Official APIs

# Use strategy with scraper
scraper = ScraperFactory.create_scraper(
    ScraperType.JOBS_GE, 
    strategy=dynamic_strategy
)
```

## Key Advantages

| Feature | Old System | New System |
|---------|------------|------------|
| Adding platforms | Requires refactoring | Create class + register |
| Code reuse | Duplicated logic | Shared base classes |
| Flexibility | Single approach | Multiple strategies |
| Configuration | Hard-coded | YAML-based |
| Testing | Tightly coupled | Modular, testable |

## Ready to Scale! 🎯

Your refactored scraper now supports:
- ✅ **Easy platform addition**
- ✅ **Multiple scraping strategies** 
- ✅ **Clean OOP architecture**
- ✅ **Factory and Strategy patterns**
- ✅ **Professional code structure**

Run `python new_main.py` to see it in action! 