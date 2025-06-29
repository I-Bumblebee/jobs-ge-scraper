"""
Pipeline management for coordinating multi-platform job scraping.
"""

from .job_pipeline import JobPipeline
from .pipeline_manager import PipelineManager

__all__ = ['JobPipeline', 'PipelineManager'] 