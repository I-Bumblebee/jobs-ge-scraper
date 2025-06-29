import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from bs4 import BeautifulSoup

from ....data.models import (
    JobListing,
    JobDetails,
    Company,
    JobMetadata,
    JobDates,
    Location,
    Salary,
    Platform
)


class JobsGeParser:
    """Parser for Jobs.ge specific HTML structure."""
    
    def __init__(self):
        """Initialize the parser."""
        self.georgian_months = [
            "იანვარი", "თებერვალი", "მარტი", "აპრილი", "მაისი", "ივნისი",
            "ივლისი", "აგვისტო", "სექტემბერი", "ოქტომბერი", "ნოემბერი", "დეკემბერი"
        ]
        
        self.english_months = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
    
    def _extract_job_id(self, url: Optional[str]) -> Optional[str]:
        """Extract job ID from URL."""
        if not url:
            return None
        match = re.search(r"id=(\d+)", url)
        return match.group(1) if match else None
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse Georgian and English date strings."""
        if not date_str or date_str.strip() == "":
            return None
        
        try:
            parts = date_str.strip().split()
            if len(parts) < 2:
                return None
            
            day = int(parts[0])
            month_str = parts[1]
            
            month = None
            if month_str in self.georgian_months:
                month = self.georgian_months.index(month_str)
            elif month_str in self.english_months:
                month = self.english_months.index(month_str)
            
            if month is None:
                return None
            
            year = datetime.now().year
            return datetime(year, month + 1, day)
        except Exception:
            return None
    
    def _parse_metadata_from_images(self, images: List[str]) -> JobMetadata:
        """Parse job metadata from image sources."""
        return JobMetadata(
            is_expiring=any("exp" in src for src in images),
            was_recently_updated=any("upd" in src for src in images),
            has_salary_info=any("salary" in src for src in images),
            is_new=any("new" in src for src in images),
            is_in_region=any("reg" in src for src in images),
        )
    
    def parse_job_listings(self, soup: BeautifulSoup) -> List[JobListing]:
        """Parse job listings from the main page."""
        job_listings = []
        
        job_table = soup.find(id="job_list_table")
        if not job_table:
            return job_listings
        
        rows = job_table.find_all("tr")
        
        # Skip header row
        for row in rows[1:]:
            cells = row.find_all("td")
            if len(cells) < 6:
                continue
            
            try:
                # Title cell (index 1)
                title_cell = cells[1]
                job_link = title_cell.find("a")
                job_title = job_link.text.strip() if job_link else ""
                job_id = self._extract_job_id(job_link.get("href")) if job_link else None
                job_url = job_link.get("href") if job_link else ""
                
                if not job_id:
                    continue
                
                # Location
                location_element = title_cell.find("i")
                location_text = location_element.text.strip() if location_element else ""
                
                # Parse location
                location = Location(city=location_text)
                if "remote" in location_text.lower():
                    location.is_remote = True
                
                # Metadata from images
                metadata_images = [img.get("src", "") for img in title_cell.find_all("img")]
                metadata = self._parse_metadata_from_images(metadata_images)
                
                # Company info (cells 2 and 3)
                company_logo_cell = cells[2]
                company_cell = cells[3]
                
                company_logo_link = company_logo_cell.find("a")
                company_logo_img = company_logo_link.find("img") if company_logo_link else None
                company_logo_src = company_logo_img.get("src", "") if company_logo_img else ""
                
                company_link = company_cell.find("a")
                company_name = company_link.text.strip() if company_link else ""
                company_jobs_url = company_link.get("href", "") if company_link else ""
                
                company = Company(
                    name=company_name,
                    jobs_url=company_jobs_url,
                    logo_url=company_logo_src
                )
                
                # Dates (cells 4 and 5)
                publish_date_cell = cells[4]
                deadline_date_cell = cells[5]
                
                publish_date_str = publish_date_cell.text.strip() if publish_date_cell else ""
                deadline_date_str = deadline_date_cell.text.strip() if deadline_date_cell else ""
                
                dates = JobDates(
                    published=self._parse_date(publish_date_str),
                    deadline=self._parse_date(deadline_date_str),
                    scraped=datetime.now()
                )
                
                # Create job listing
                job_listing = JobListing(
                    id=job_id,
                    platform=Platform.JOBS_GE,
                    title=job_title,
                    location=location,
                    company=company,
                    metadata=metadata,
                    dates=dates,
                    url=job_url
                )
                
                job_listings.append(job_listing)
                
            except Exception as e:
                # Log error but continue processing other jobs
                print(f"Error parsing job listing: {str(e)}")
                continue
        
        return job_listings
    
    def parse_job_detail(self, soup: BeautifulSoup, job_id: str) -> Dict[str, Any]:
        """Parse detailed job information from job detail page."""
        try:
            # Extract title
            title_element = soup.find("h1")
            title = title_element.text.strip() if title_element else ""
            
            # Extract job description
            description_div = soup.find("div", class_="job-description") or soup.find("div", {"id": "job_description"})
            description = ""
            if description_div:
                description = description_div.get_text(strip=True)
            
            # Extract company information
            company_info = soup.find("div", class_="company-info")
            company_name = ""
            if company_info:
                company_link = company_info.find("a")
                company_name = company_link.text.strip() if company_link else ""
            
            # Extract dates
            date_info = soup.find("div", class_="job-dates")
            dates = JobDates(scraped=datetime.now())
            
            # Extract salary if available
            salary_element = soup.find("div", class_="salary") or soup.find(text=re.compile(r"\$|\₾|ლარი"))
            salary = None
            if salary_element:
                # Basic salary parsing - can be enhanced
                salary_text = str(salary_element)
                salary = Salary()
                # Add more sophisticated salary parsing here
            
            # Create job details
            job_details = JobDetails(
                id=job_id,
                platform=Platform.JOBS_GE,
                title=title,
                description=description,
                company=Company(name=company_name),
                dates=dates,
                salary=salary,
            )
            
            return job_details.to_dict()
            
        except Exception as e:
            return {
                "id": job_id,
                "platform": Platform.JOBS_GE.value,
                "error": str(e)
            } 