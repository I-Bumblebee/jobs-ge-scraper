from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum


class Platform(Enum):
    """Supported job platforms."""
    JOBS_GE = "jobs_ge"
    INDEED = "indeed"
    LINKEDIN = "linkedin"
    GLASSDOOR = "glassdoor"
    STACK_OVERFLOW = "stack_overflow"


@dataclass
class JobDates:
    """Job-related dates."""
    published: Optional[datetime] = None
    deadline: Optional[datetime] = None
    updated: Optional[datetime] = None
    scraped: Optional[datetime] = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with ISO format dates."""
        return {
            "published": self.published.isoformat() if self.published else None,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "updated": self.updated.isoformat() if self.updated else None,
            "scraped": self.scraped.isoformat() if self.scraped else None,
        }


@dataclass
class JobMetadata:
    """Job metadata flags and information."""
    is_expiring: bool = False
    was_recently_updated: bool = False
    has_salary_info: bool = False
    is_new: bool = False
    is_in_region: bool = False
    is_remote: bool = False
    is_featured: bool = False
    is_urgent: bool = False
    
    def to_dict(self) -> Dict[str, bool]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class Company:
    """Company information."""
    name: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    description: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    location: Optional[str] = None
    jobs_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class Salary:
    """Salary information."""
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    currency: Optional[str] = None
    period: Optional[str] = None  # hourly, monthly, yearly
    is_negotiable: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class Location:
    """Location information."""
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    is_remote: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class JobListing:
    """Basic job listing information from search results."""
    id: str
    platform: Platform
    title: str
    location: Location = field(default_factory=Location)
    company: Company = field(default_factory=Company)
    metadata: JobMetadata = field(default_factory=JobMetadata)
    dates: JobDates = field(default_factory=JobDates)
    salary: Optional[Salary] = None
    job_type: Optional[str] = None  # full-time, part-time, contract, etc.
    category: Optional[str] = None
    url: Optional[str] = None
    short_description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "platform": self.platform.value,
            "title": self.title,
            "location": self.location.to_dict(),
            "company": self.company.to_dict(),
            "metadata": self.metadata.to_dict(),
            "dates": self.dates.to_dict(),
            "salary": self.salary.to_dict() if self.salary else None,
            "job_type": self.job_type,
            "category": self.category,
            "url": self.url,
            "short_description": self.short_description,
        }


@dataclass
class JobDetails:
    """Detailed job information."""
    id: str
    platform: Platform
    title: str
    description: str
    requirements: List[str] = field(default_factory=list)
    responsibilities: List[str] = field(default_factory=list)
    benefits: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    experience_level: Optional[str] = None
    education_level: Optional[str] = None
    location: Location = field(default_factory=Location)
    company: Company = field(default_factory=Company)
    salary: Optional[Salary] = None
    dates: JobDates = field(default_factory=JobDates)
    metadata: JobMetadata = field(default_factory=JobMetadata)
    url: Optional[str] = None
    application_url: Optional[str] = None
    contact_info: Dict[str, str] = field(default_factory=dict)
    description_file_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "platform": self.platform.value,
            "title": self.title,
            "description": self.description,
            "requirements": self.requirements,
            "responsibilities": self.responsibilities,
            "benefits": self.benefits,
            "skills": self.skills,
            "experience_level": self.experience_level,
            "education_level": self.education_level,
            "location": self.location.to_dict(),
            "company": self.company.to_dict(),
            "salary": self.salary.to_dict() if self.salary else None,
            "dates": self.dates.to_dict(),
            "metadata": self.metadata.to_dict(),
            "url": self.url,
            "application_url": self.application_url,
            "contact_info": self.contact_info,
            "description_file_path": self.description_file_path,
        }


@dataclass
class ScrapingResult:
    """Result of a scraping operation."""
    platform: Platform
    total_jobs_found: int
    successful_scrapes: int
    failed_scrapes: int
    start_time: datetime
    end_time: Optional[datetime] = None
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "platform": self.platform.value,
            "total_jobs_found": self.total_jobs_found,
            "successful_scrapes": self.successful_scrapes,
            "failed_scrapes": self.failed_scrapes,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "errors": self.errors,
        } 