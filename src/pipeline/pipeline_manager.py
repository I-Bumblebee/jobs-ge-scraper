import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from .job_pipeline import JobPipeline
from ..scrapers.base.scraper_interface import ScrapingConfig
from ..scrapers.factory.scraper_factory import ScraperFactory, ScraperType
from ..config.settings import PipelineSettings


class PipelineManager:
    """
    Manager for coordinating multiple job scraping pipelines.
    Supports running multiple configurations or platforms simultaneously.
    """
    
    def __init__(self):
        """
        Initialize the pipeline manager.
        """
        self.logger = logging.getLogger(f"{__name__}.PipelineManager")
        self.pipelines: Dict[str, JobPipeline] = {}
    
    def create_pipeline(
        self,
        name: str,
        platforms: List[ScraperType],
        config: ScrapingConfig,
        max_concurrent_details: int = 5
    ) -> JobPipeline:
        """
        Create a new pipeline with the given configuration.
        
        Args:
            name: Pipeline name/identifier
            platforms: List of platforms to scrape
            config: Scraping configuration
            max_concurrent_details: Maximum concurrent detail requests
            
        Returns:
            Created pipeline instance
        """
        pipeline = JobPipeline(
            platforms=platforms,
            config=config,
            max_concurrent_details=max_concurrent_details
        )
        
        self.pipelines[name] = pipeline
        self.logger.info(f"Created pipeline '{name}' with platforms: {[p.value for p in platforms]}")
        
        return pipeline
    
    def create_pipeline_from_settings(self, name: str, settings: PipelineSettings) -> JobPipeline:
        """
        Create a pipeline from settings configuration.
        
        Args:
            name: Pipeline name
            settings: Pipeline settings
            
        Returns:
            Created pipeline instance
        """
        platforms = [ScraperType(p) for p in settings.platforms]
        config = ScrapingConfig(
            job_count=settings.job_count,
            location_id=settings.location_id,
            category_id=settings.category_id,
            query=settings.query,
            has_salary=settings.has_salary,
            max_concurrent=settings.max_concurrent,
            batch_size=settings.batch_size,
            locale=settings.locale
        )
        
        return self.create_pipeline(
            name=name,
            platforms=platforms,
            config=config,
            max_concurrent_details=settings.max_concurrent_details
        )
    
    async def run_pipeline(self, name: str) -> Dict[str, Any]:
        """
        Run a specific pipeline by name.
        
        Args:
            name: Pipeline name
            
        Returns:
            Pipeline execution results
        """
        if name not in self.pipelines:
            raise ValueError(f"Pipeline '{name}' not found")
        
        pipeline = self.pipelines[name]
        self.logger.info(f"Starting pipeline '{name}'")
        
        try:
            results = await pipeline.run_full_pipeline()
            self.logger.info(f"Pipeline '{name}' completed successfully")
            return results
            
        except Exception as e:
            error_msg = f"Pipeline '{name}' failed: {str(e)}"
            self.logger.error(error_msg)
            return {
                'name': name,
                'status': 'failed',
                'error': error_msg,
                'timestamp': datetime.now().isoformat()
            }
    
    async def run_multiple_pipelines(self, pipeline_names: List[str]) -> Dict[str, Any]:
        """
        Run multiple pipelines concurrently.
        
        Args:
            pipeline_names: List of pipeline names to run
            
        Returns:
            Results from all pipelines
        """
        tasks = []
        for name in pipeline_names:
            if name in self.pipelines:
                task = self.run_pipeline(name)
                tasks.append((name, task))
            else:
                self.logger.warning(f"Pipeline '{name}' not found, skipping")
        
        results = {}
        for name, task in tasks:
            try:
                result = await task
                results[name] = result
            except Exception as e:
                results[name] = {
                    'status': 'failed',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
        
        return results
    
    async def run_all_pipelines(self) -> Dict[str, Any]:
        """
        Run all registered pipelines concurrently.
        
        Returns:
            Results from all pipelines
        """
        pipeline_names = list(self.pipelines.keys())
        self.logger.info(f"Running all pipelines: {pipeline_names}")
        
        return await self.run_multiple_pipelines(pipeline_names)
    
    def get_pipeline_status(self, name: str) -> Dict[str, Any]:
        """
        Get status information for a pipeline.
        
        Args:
            name: Pipeline name
            
        Returns:
            Pipeline status information
        """
        if name not in self.pipelines:
            return {'status': 'not_found'}
        
        pipeline = self.pipelines[name]
        return {
            'status': 'registered',
            'platforms': [p.value for p in pipeline.platforms],
            'config': {
                'job_count': pipeline.config.job_count,
                'locale': pipeline.config.locale,
                'batch_size': pipeline.config.batch_size,
            },
            'database_enabled': True
        }
    
    def list_pipelines(self) -> Dict[str, Dict[str, Any]]:
        """
        List all registered pipelines and their status.
        
        Returns:
            Dictionary of pipeline statuses
        """
        return {
            name: self.get_pipeline_status(name) 
            for name in self.pipelines.keys()
        }
    
    def get_available_platforms(self) -> Dict[str, str]:
        """
        Get available scraping platforms.
        
        Returns:
            Dictionary of platform names and descriptions
        """
        return ScraperFactory.get_available_scrapers() 