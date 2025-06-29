"""
Configuration management for the job scraping system.
"""

from .settings import PipelineSettings, GlobalSettings
from .platform_configs import PlatformConfig

__all__ = ['PipelineSettings', 'GlobalSettings', 'PlatformConfig'] 