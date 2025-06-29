from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import yaml
from pathlib import Path


@dataclass
class PipelineSettings:
    """Settings for a single scraping pipeline."""
    
    # Basic configuration
    job_count: int = 20
    platforms: List[str] = field(default_factory=lambda: ["jobs_ge"])
    locale: str = "ge"
    
    # Search filters
    location_id: Optional[str] = None
    category_id: Optional[str] = None
    query: Optional[str] = None
    has_salary: bool = False
    
    # Performance settings
    max_concurrent: int = 5
    max_concurrent_details: int = 5
    batch_size: int = 10
    rate_limit_delay: float = 1.0
    max_retries: int = 3
    
    # Output settings
    output_format: str = "json"
    include_descriptions: bool = True
    save_html: bool = False
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PipelineSettings':
        """Create settings from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return {
            field.name: getattr(self, field.name)
            for field in self.__dataclass_fields__.values()
        }


@dataclass
class GlobalSettings:
    """Global application settings."""
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    # Database
    database_url: Optional[str] = None
    use_database: bool = False
    
    # Output
    base_output_dir: str = "data/output"
    cleanup_temp_files: bool = True
    
    # Performance
    default_timeout: int = 30
    default_user_agent: str = "JobScraper/1.0"
    
    # Features
    enable_caching: bool = True
    cache_duration_hours: int = 24
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GlobalSettings':
        """Create settings from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return {
            field.name: getattr(self, field.name)
            for field in self.__dataclass_fields__.values()
        }


class SettingsManager:
    """Manager for loading and saving configuration settings."""
    
    def __init__(self, config_dir: str = "config"):
        """
        Initialize settings manager.
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.global_settings_file = self.config_dir / "global.yaml"
        self.pipelines_file = self.config_dir / "pipelines.yaml"
    
    def load_global_settings(self) -> GlobalSettings:
        """Load global settings from file."""
        if self.global_settings_file.exists():
            with open(self.global_settings_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            return GlobalSettings.from_dict(data)
        else:
            # Create default settings file
            settings = GlobalSettings()
            self.save_global_settings(settings)
            return settings
    
    def save_global_settings(self, settings: GlobalSettings) -> None:
        """Save global settings to file."""
        with open(self.global_settings_file, 'w', encoding='utf-8') as f:
            yaml.dump(settings.to_dict(), f, default_flow_style=False)
    
    def load_pipeline_settings(self, name: str) -> Optional[PipelineSettings]:
        """Load settings for a specific pipeline."""
        if not self.pipelines_file.exists():
            return None
        
        with open(self.pipelines_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
        
        pipeline_data = data.get('pipelines', {}).get(name)
        if pipeline_data:
            return PipelineSettings.from_dict(pipeline_data)
        
        return None
    
    def save_pipeline_settings(self, name: str, settings: PipelineSettings) -> None:
        """Save settings for a specific pipeline."""
        # Load existing data
        data = {'pipelines': {}}
        if self.pipelines_file.exists():
            with open(self.pipelines_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {'pipelines': {}}
        
        # Update pipeline settings
        data['pipelines'][name] = settings.to_dict()
        
        # Save back to file
        with open(self.pipelines_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False)
    
    def list_pipeline_configurations(self) -> List[str]:
        """List all saved pipeline configurations."""
        if not self.pipelines_file.exists():
            return []
        
        with open(self.pipelines_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
        
        return list(data.get('pipelines', {}).keys())
    
    def create_default_pipeline_configs(self) -> None:
        """Create some default pipeline configurations."""
        # Jobs.ge IT jobs
        it_settings = PipelineSettings(
            job_count=50,
            platforms=["jobs_ge"],
            category_id="6",  # IT/Programming
            location_id="17",  # Remote
            has_salary=True,
            locale="ge"
        )
        self.save_pipeline_settings("jobs_ge_it_remote", it_settings)
        
        # Jobs.ge Tbilisi all categories
        tbilisi_settings = PipelineSettings(
            job_count=100,
            platforms=["jobs_ge"],
            location_id="1",  # Tbilisi
            locale="ge"
        )
        self.save_pipeline_settings("jobs_ge_tbilisi_all", tbilisi_settings)
        
        # Multi-platform setup (when other platforms are implemented)
        multi_settings = PipelineSettings(
            job_count=30,
            platforms=["jobs_ge"],  # Will expand when other platforms are ready
            category_id="6",  # IT/Programming
            has_salary=True,
            max_concurrent=3,  # Lower for multiple platforms
            locale="en"
        )
        self.save_pipeline_settings("multi_platform_it", multi_settings) 