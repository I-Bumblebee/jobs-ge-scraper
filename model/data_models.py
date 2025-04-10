from typing import Optional
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class JobDates:
    published: Optional[datetime] = None
    deadline: Optional[datetime] = None

@dataclass
class JobMetadata:
    is_expiring: bool = False
    was_recently_updated: bool = False
    has_salary_info: bool = False
    is_new: bool = False
    is_in_region: bool = False

@dataclass
class JobCompany:
    name: Optional[str] = None
    jobs_url: Optional[str] = None
    logo_src: Optional[str] = None

@dataclass
class ParsedJobRow:
    id: Optional[str] = None
    title: Optional[str] = None
    location: Optional[str] = None
    metadata: JobMetadata = None
    company: JobCompany = None
    dates: JobDates = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = JobMetadata()
        if self.company is None:
            self.company = JobCompany()
        if self.dates is None:
            self.dates = JobDates()

@dataclass
class ParsedJobView:
    id: str = ""
    title: str = ""
    dates: JobDates = None
    description_path: str = ""
    
    def __post_init__(self):
        if self.dates is None:
            self.dates = JobDates()
