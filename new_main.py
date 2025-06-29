"""
New main entry point for the multi-platform job scraper.
Demonstrates the Factory and Strategy design patterns in action.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.pipeline.pipeline_manager import PipelineManager
from src.scrapers.factory.scraper_factory import ScraperFactory, ScraperType
from src.scrapers.base.scraper_interface import ScrapingConfig
from src.scrapers.base.scraper_strategy import StaticScraperStrategy, DynamicScraperStrategy
from src.config.settings import PipelineSettings, SettingsManager
from src.utils.logger import setup_logging, ScrapingLogger


# Platform-specific configurations
PLATFORM_CONFIGS = {
    "jobs_ge_it_remote": {
        "platforms": ["jobs_ge"],
        "job_count": 50,
        "category_id": "6",  # IT/Programming
        "location_id": "17",  # Remote
        "has_salary": True,
        "locale": "ge"
    },
    "jobs_ge_tbilisi_all": {
        "platforms": ["jobs_ge"],
        "job_count": 100,
        "location_id": "1",  # Tbilisi
        "locale": "ge"
    },
    "jobs_ge_finance": {
        "platforms": ["jobs_ge"],
        "job_count": 30,
        "category_id": "3",  # Finance, Statistics
        "location_id": "1",  # Tbilisi
        "has_salary": True,
        "locale": "ge"
    }
}


async def demonstrate_factory_pattern():
    """Demonstrate the Factory pattern for creating scrapers."""
    print("\n" + "="*60)
    print("DEMONSTRATING FACTORY PATTERN")
    print("="*60)
    
    # Show available scrapers
    available_scrapers = ScraperFactory.get_available_scrapers()
    print("\nAvailable scrapers:")
    for scraper_type, description in available_scrapers.items():
        print(f"  - {scraper_type}: {description}")
    
    # Create different scrapers using the factory
    print("\nCreating scrapers using Factory pattern:")
    
    try:
        # Create Jobs.ge scraper with default strategy
        jobs_ge_scraper = ScraperFactory.create_scraper(ScraperType.JOBS_GE)
        print(f"✓ Created {jobs_ge_scraper.platform_name} scraper")
        print(f"  - Strategy: {jobs_ge_scraper.strategy.__class__.__name__}")
        print(f"  - Supported locations: {len(jobs_ge_scraper.supported_locations)} locations")
        print(f"  - Supported categories: {len(jobs_ge_scraper.supported_categories)} categories")
        
    except Exception as e:
        print(f"✗ Error creating scraper: {str(e)}")


async def demonstrate_strategy_pattern():
    """Demonstrate the Strategy pattern for different scraping approaches."""
    print("\n" + "="*60)
    print("DEMONSTRATING STRATEGY PATTERN")
    print("="*60)
    
    # Create different strategies
    static_strategy = ScraperFactory.create_strategy("static", max_concurrent=3, timeout=20)
    dynamic_strategy = ScraperFactory.create_strategy("dynamic", max_concurrent=2, timeout=30, headless=True)
    
    print(f"\nCreated strategies:")
    print(f"  - Static strategy: {static_strategy.__class__.__name__} (Method: {static_strategy.method_type.value})")
    print(f"  - Dynamic strategy: {dynamic_strategy.__class__.__name__} (Method: {dynamic_strategy.method_type.value})")
    
    # Create scrapers with different strategies
    print(f"\nCreating scrapers with different strategies:")
    
    static_scraper = ScraperFactory.create_scraper(ScraperType.JOBS_GE, strategy=static_strategy)
    print(f"✓ Jobs.ge scraper with static strategy")
    
    dynamic_scraper = ScraperFactory.create_scraper(ScraperType.JOBS_GE, strategy=dynamic_strategy)
    print(f"✓ Jobs.ge scraper with dynamic strategy")


async def demonstrate_pipeline_system():
    """Demonstrate the full pipeline system."""
    print("\n" + "="*60)
    print("DEMONSTRATING PIPELINE SYSTEM")
    print("="*60)
    
    # Initialize pipeline manager
    manager = PipelineManager(base_output_dir="data/output_demo")
    
    print(f"\nInitialized Pipeline Manager")
    print(f"Available platforms: {list(manager.get_available_platforms().keys())}")
    
    # Create pipelines for different configurations
    print(f"\nCreating pipelines...")
    
    for config_name, config_data in PLATFORM_CONFIGS.items():
        try:
            platforms = [ScraperType(p) for p in config_data["platforms"]]
            
            scraping_config = ScrapingConfig(
                job_count=config_data["job_count"],
                location_id=config_data.get("location_id"),
                category_id=config_data.get("category_id"),
                has_salary=config_data.get("has_salary", False),
                locale=config_data.get("locale", "en"),
                max_concurrent=3,
                batch_size=5
            )
            
            pipeline = manager.create_pipeline(
                name=config_name,
                platforms=platforms,
                config=scraping_config,
                max_concurrent_details=3
            )
            
            print(f"✓ Created pipeline: {config_name}")
            
        except Exception as e:
            print(f"✗ Error creating pipeline {config_name}: {str(e)}")
    
    # Show pipeline status
    print(f"\nPipeline Status:")
    pipelines = manager.list_pipelines()
    for name, status in pipelines.items():
        print(f"  - {name}: {status['status']} (platforms: {status['platforms']})")
    
    return manager


async def run_sample_scraping(manager: PipelineManager, pipeline_name: str = "jobs_ge_it_remote"):
    """Run a sample scraping operation."""
    print("\n" + "="*60)
    print(f"RUNNING SAMPLE SCRAPING: {pipeline_name}")
    print("="*60)
    
    # Set up logging for this operation
    scraping_logger = ScrapingLogger(platform="jobs_ge", operation="demo_scraping")
    scraping_logger.log_start(f"Demo scraping with pipeline: {pipeline_name}")
    
    try:
        # Run the pipeline
        results = await manager.run_pipeline(pipeline_name)
        
        if 'errors' in results and results['errors']:
            scraping_logger.log_error(f"Pipeline completed with errors", 
                                     error_count=len(results['errors']))
            for error in results['errors']:
                print(f"  ✗ Error: {error}")
        else:
            scraping_logger.log_success(
                "Pipeline completed successfully",
                total_jobs=results.get('total_jobs_found', 0),
                details_fetched=results.get('total_details_fetched', 0),
                duration=results.get('duration_seconds', 0)
            )
        
        # Show results summary
        print(f"\nScraping Results:")
        print(f"  - Total jobs found: {results.get('total_jobs_found', 0)}")
        print(f"  - Details fetched: {results.get('total_details_fetched', 0)}")
        print(f"  - Duration: {results.get('duration_seconds', 0):.2f} seconds")
        print(f"  - Platforms: {results.get('platforms', [])}")
        
        if 'errors' in results:
            print(f"  - Errors: {len(results['errors'])}")
        
        # Show pipeline status
        pipeline_status = manager.get_pipeline_status(pipeline_name)
        if 'output_dir' in pipeline_status:
            print(f"  - Output directory: {pipeline_status['output_dir']}")
        
        scraping_logger.log_completion("Demo scraping completed")
        
        return results
        
    except Exception as e:
        scraping_logger.log_error("Sample scraping failed", exception=e)
        print(f"✗ Scraping failed: {str(e)}")
        return None


async def demonstrate_configuration_management():
    """Demonstrate configuration management."""
    print("\n" + "="*60)
    print("DEMONSTRATING CONFIGURATION MANAGEMENT")
    print("="*60)
    
    # Initialize settings manager
    settings_manager = SettingsManager(config_dir="config_demo")
    
    print(f"\nSettings Manager initialized")
    
    # Create and save some example configurations
    print(f"\nCreating example configurations...")
    
    settings_manager.create_default_pipeline_configs()
    
    # Load and display configurations
    configs = settings_manager.list_pipeline_configurations()
    print(f"\nAvailable pipeline configurations:")
    for config_name in configs:
        config = settings_manager.load_pipeline_settings(config_name)
        if config:
            print(f"  - {config_name}:")
            print(f"    Platforms: {config.platforms}")
            print(f"    Job count: {config.job_count}")
            print(f"    Locale: {config.locale}")
            if config.category_id:
                print(f"    Category: {config.category_id}")
            if config.location_id:
                print(f"    Location: {config.location_id}")


async def main():
    """Main demonstration function."""
    print("="*60)
    print("MULTI-PLATFORM JOB SCRAPER DEMONSTRATION")
    print("Factory and Strategy Design Patterns")
    print("="*60)
    
    # Set up logging
    logger = setup_logging(level="INFO", log_file="demo_scraping")
    logger.info("Starting job scraper demonstration")
    
    try:
        # Demonstrate each component
        await demonstrate_factory_pattern()
        await demonstrate_strategy_pattern()
        await demonstrate_configuration_management()
        
        # Demonstrate the full pipeline system
        manager = await demonstrate_pipeline_system()
        
        # Ask user if they want to run actual scraping
        print("\n" + "="*60)
        print("OPTIONAL: LIVE SCRAPING DEMONSTRATION")
        print("="*60)
        
        print("\nThis will perform actual web scraping from jobs.ge")
        print("The operation will:")
        print("  - Fetch real job listings")
        print("  - Save data to files")
        print("  - Take 30-60 seconds to complete")
        
        response = input("\nDo you want to run live scraping? (y/n): ").lower().strip()
        
        if response == 'y':
            results = await run_sample_scraping(manager)
            if results:
                print(f"\n✓ Live scraping completed successfully!")
                print(f"Check the output directory for results.")
        else:
            print("Skipping live scraping demonstration.")
        
        print("\n" + "="*60)
        print("DEMONSTRATION COMPLETE")
        print("="*60)
        
        print("\nKey Features Demonstrated:")
        print("✓ Factory Pattern - Easy creation of platform-specific scrapers")
        print("✓ Strategy Pattern - Flexible scraping approaches (static, dynamic, API)")
        print("✓ OOP Design - Clean inheritance and abstraction")
        print("✓ Pipeline System - Coordinated multi-platform scraping")
        print("✓ Configuration Management - Flexible settings and presets")
        print("✓ Error Handling - Robust error management")
        print("✓ Logging System - Comprehensive operation tracking")
        
        print("\nTo add new platforms:")
        print("1. Create a new scraper class inheriting from BaseScraper")
        print("2. Implement the required abstract methods")
        print("3. Register it with the ScraperFactory")
        print("4. The pipeline system will automatically support it!")
        
        logger.info("Job scraper demonstration completed successfully")
        
    except Exception as e:
        logger.error(f"Demonstration failed: {str(e)}", exc_info=True)
        print(f"\n✗ Demonstration failed: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 