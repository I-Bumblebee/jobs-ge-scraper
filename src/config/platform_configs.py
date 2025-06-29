from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum


class PlatformType(Enum):
    """Supported platform types."""
    JOBS_GE = "jobs_ge"
    INDEED = "indeed"
    LINKEDIN = "linkedin"
    GLASSDOOR = "glassdoor"
    STACK_OVERFLOW = "stack_overflow"


@dataclass
class PlatformConfig:
    """Configuration for a specific scraping platform."""
    
    platform_type: PlatformType
    base_url: str
    default_locale: str = "en"
    
    # Request settings
    rate_limit_delay: float = 1.0
    max_retries: int = 3
    timeout: int = 30
    
    # Platform-specific headers
    headers: Dict[str, str] = field(default_factory=dict)
    
    # Authentication (if required)
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    
    # Scraping strategy preferences
    preferred_strategy: str = "static"  # static, dynamic, api
    
    # Platform-specific settings
    custom_settings: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'platform_type': self.platform_type.value,
            'base_url': self.base_url,
            'default_locale': self.default_locale,
            'rate_limit_delay': self.rate_limit_delay,
            'max_retries': self.max_retries,
            'timeout': self.timeout,
            'headers': self.headers,
            'api_key': self.api_key,
            'username': self.username,
            'password': self.password,
            'preferred_strategy': self.preferred_strategy,
            'custom_settings': self.custom_settings,
        }


class PlatformConfigManager:
    """Manager for platform-specific configurations."""
    
    def __init__(self):
        """Initialize with default platform configurations."""
        self._configs: Dict[PlatformType, PlatformConfig] = {}
        self._load_default_configs()
    
    def _load_default_configs(self):
        """Load default configurations for all supported platforms."""
        
        # Jobs.ge configuration
        jobs_ge_config = PlatformConfig(
            platform_type=PlatformType.JOBS_GE,
            base_url="https://jobs.ge",
            default_locale="ge",
            rate_limit_delay=1.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Connection": "keep-alive",
            },
            custom_settings={
                "page_size": 300,
                "categories": {
                    "All Categories": "",
                    "Administration/Management": "1",
                    "Finance, Statistics": "3",
                    "Sales/Procurement": "2",
                    "PR/Marketing": "4",
                    "General Technical Staff": "18",
                    "Logistics/Transport/Distribution": "5",
                    "Construction/Repair": "11",
                    "Cleaning": "16",
                    "Security/Safety": "17",
                    "IT/Programming": "6",
                    "Media/Publishing": "13",
                    "Education": "12",
                    "Law": "7",
                    "Medicine/Pharmacy": "8",
                    "Beauty/Fashion": "14",
                    "Food": "10",
                    "Other": "9"
                },
                "locations": {
                    "Any Location": "",
                    "Tbilisi": "1",
                    "Abkhazeti AR": "15",
                    "Adjara AR": "14",
                    "Guria": "9",
                    "Imereti": "8",
                    "Kakheti": "3",
                    "Kvemo Kartli": "5",
                    "Mtskheta-Mtianeti": "4",
                    "Racha-Lechkhumi, Lw. Svaneti": "12",
                    "Samegrelo-Zemo Svaneti": "13",
                    "Samtskhe-Javakheti": "7",
                    "Shida Kartli": "6",
                    "Abroad": "16",
                    "Remote": "17"
                }
            }
        )
        self._configs[PlatformType.JOBS_GE] = jobs_ge_config
        
        # Indeed configuration (placeholder for future implementation)
        indeed_config = PlatformConfig(
            platform_type=PlatformType.INDEED,
            base_url="https://indeed.com",
            default_locale="en",
            rate_limit_delay=2.0,  # Indeed is stricter
            preferred_strategy="dynamic",  # Indeed often requires JavaScript
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
            custom_settings={
                "requires_javascript": True,
                "pagination_type": "scroll",
            }
        )
        self._configs[PlatformType.INDEED] = indeed_config
        
        # LinkedIn configuration (placeholder)
        linkedin_config = PlatformConfig(
            platform_type=PlatformType.LINKEDIN,
            base_url="https://linkedin.com",
            default_locale="en",
            rate_limit_delay=3.0,  # LinkedIn is very strict
            preferred_strategy="api",  # Prefer API when available
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            },
            custom_settings={
                "requires_login": True,
                "api_available": True,
            }
        )
        self._configs[PlatformType.LINKEDIN] = linkedin_config
    
    def get_config(self, platform_type: PlatformType) -> Optional[PlatformConfig]:
        """Get configuration for a specific platform."""
        return self._configs.get(platform_type)
    
    def update_config(self, platform_type: PlatformType, config: PlatformConfig):
        """Update configuration for a platform."""
        self._configs[platform_type] = config
    
    def get_all_configs(self) -> Dict[PlatformType, PlatformConfig]:
        """Get all platform configurations."""
        return self._configs.copy()
    
    def get_supported_platforms(self) -> List[PlatformType]:
        """Get list of supported platforms."""
        return list(self._configs.keys())
    
    def get_categories_for_platform(self, platform_type: PlatformType) -> Dict[str, str]:
        """Get category mappings for a platform."""
        config = self.get_config(platform_type)
        if config and 'categories' in config.custom_settings:
            return config.custom_settings['categories']
        return {}
    
    def get_locations_for_platform(self, platform_type: PlatformType) -> Dict[str, str]:
        """Get location mappings for a platform."""
        config = self.get_config(platform_type)
        if config and 'locations' in config.custom_settings:
            return config.custom_settings['locations']
        return {} 