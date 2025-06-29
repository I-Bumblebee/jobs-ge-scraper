import re
from typing import List, Dict, Any, Optional, Tuple
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


class SsGeParser:
    """Parser for jobs.ss.ge specific HTML structure."""
    
    def __init__(self):
        """Initialize the parser."""
        self.georgian_months = [
            "იანვარი", "თებერვალი", "მარტი", "აპრილი", "მაისი", "ივნისი",
            "ივლისი", "აგვისტო", "სექტემბერი", "ოქტომბერი", "ნოემბერი", "დეკემბერი"
        ]
        
        # Georgian abbreviated months used in jobs.ss.ge
        self.georgian_abbrev_months = {
            "იანვარი": 1, "თებერვალი": 2, "მარტი": 3, "აპრილი": 4, "მაისი": 5, "ივნისი": 6,
            "ივლისი": 7, "აგვისტო": 8, "სექტემბერი": 9, "ოქტომბერი": 10, "ნოემბერი": 11, "დეკემბერი": 12
        }
    
    def _extract_job_id(self, url: Optional[str]) -> Optional[str]:
        """Extract job ID from jobs.ss.ge URL."""
        if not url:
            return None
        # jobs.ss.ge URLs need to be analyzed from actual structure
        match = re.search(r"/vacancies/(\d+)", url)
        if not match:
            # Try alternative patterns
            match = re.search(r"id=(\d+)", url)
        return match.group(1) if match else None
    
    def _parse_date_range(self, date_str: str) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Parse Georgian date range like '25 ივნისი - 29 ივლისი'."""
        if not date_str or date_str.strip() == "":
            return None, None
        
        try:
            # Remove extra whitespace and split by dash
            date_str = date_str.strip()
            if " - " in date_str:
                start_str, end_str = date_str.split(" - ", 1)
            else:
                start_str = date_str
                end_str = ""
            
            start_date = self._parse_single_date(start_str.strip())
            end_date = self._parse_single_date(end_str.strip()) if end_str else None
            
            return start_date, end_date
        except Exception:
            return None, None
    
    def _parse_single_date(self, date_str: str) -> Optional[datetime]:
        """Parse single Georgian date like '25 ივნისი'."""
        if not date_str or date_str.strip() == "":
            return None
        
        try:
            parts = date_str.strip().split()
            if len(parts) < 2:
                return None
            
            day = int(parts[0])
            month_str = parts[1]
            
            # Check Georgian months
            month = self.georgian_abbrev_months.get(month_str)
            
            if month is None:
                return None
            
            year = datetime.now().year
            return datetime(year, month, day)
        except Exception:
            return None
    
    def parse_job_listings(self, soup: BeautifulSoup) -> List[JobListing]:
        """Parse job listings from jobs.ss.ge page."""
        job_listings = []
        
        # Find job cards using the structure from the user's HTML
        # <div class="sc-28f268a4-2 udaGZ">
        job_items = soup.find_all("div", class_="sc-28f268a4-2 udaGZ")
        
        for item in job_items:
            try:
                # Extract title from h2 with class "sc-64e43013-0 jkUKFK title"
                title_element = item.find("h2", class_=lambda x: x and "title" in x)
                if not title_element:
                    continue
                
                job_title = title_element.text.strip()
                
                # For jobs.ss.ge, we'll need to extract the job URL and ID differently
                # Let's look for any link in the job card that might contain the job URL
                job_url = ""
                job_id = ""
                
                # Try to find the main job link - this might be a wrapper around the entire card
                job_link = item.find_parent("a")
                if job_link:
                    job_url = job_link.get("href", "")
                else:
                    # Alternative: look for any link within the job card
                    job_link = item.find("a")
                    if job_link:
                        job_url = job_link.get("href", "")
                
                # Convert relative URL to absolute URL
                if job_url and not job_url.startswith("http"):
                    job_url = f"https://jobs.ss.ge{job_url}"
                
                # Extract job ID from URL or generate one from the title
                job_id = self._extract_job_id(job_url)
                if not job_id:
                    # Generate an ID based on title hash as fallback
                    import hashlib
                    job_id = str(abs(hash(job_title)) % 1000000)
                
                # Extract price/salary information
                # <span class="sc-64e43013-0 hdwvnh price"><span class="sc-64e43013-0 gPiPQh">2,800 - 3,000 ₾</span> თვეში</span>
                salary_element = item.find("span", class_=lambda x: x and "price" in x)
                salary = None
                if salary_element:
                    salary_text = salary_element.text.strip()
                    salary = self._parse_salary(salary_text)
                
                # Extract experience level
                # <div class="sc-28f268a4-7 fdLhIc"><span class="sc-56753db7-0 sc-56753db7-2694 gLXqhQ lfaeoF"></span><span class="sc-64e43013-0 jMGSUP">3 წლამდე</span></div>
                experience_element = item.find("span", class_="sc-64e43013-0 jMGSUP")
                experience_level = experience_element.text.strip() if experience_element else ""
                
                # Extract description from the long text section
                # <div class="sc-28f268a4-1 dnKFnl sc-64e43013-0 cQtEWp">ავეჯის ქართული საწარმო Litten Tree...</div>
                desc_element = item.find("div", class_=lambda x: x and "sc-28f268a4-1" in x)
                description = desc_element.text.strip() if desc_element else ""
                short_description = description[:200] + "..." if len(description) > 200 else description
                
                # Extract date information
                # Last section: <div><span class="sc-56753db7-0 sc-56753db7-2047 gLXqhQ icLjxU"></span><span class="sc-64e43013-0 jMGSUP">25 ივნისი - 29 ივლისი</span></div>
                date_spans = item.find_all("span", class_="sc-64e43013-0 jMGSUP")
                date_text = ""
                for span in date_spans:
                    # Look for date-like text (contains Georgian months)
                    text = span.text.strip()
                    if any(month in text for month in self.georgian_months):
                        date_text = text
                        break
                
                start_date, end_date = self._parse_date_range(date_text)
                
                dates = JobDates(
                    published=start_date,
                    deadline=end_date,
                    scraped=datetime.now()
                )
                
                # Extract company information - not visible in the provided HTML structure
                # We'll set it to a default for now
                company = Company(
                    name="Unknown Company",
                    jobs_url="",
                    logo_url=""
                )
                
                # Extract location - not clearly visible in the provided structure
                location = Location(city="თბილისი")  # Default to Tbilisi
                
                # Check for urgent/featured flags
                # <div class="sc-28f268a4-5 jwtPQI sc-64e43013-0 gZOyTX">სასწრაფოდ</div>
                urgent_element = item.find("div", class_=lambda x: x and "sc-28f268a4-5" in x)
                is_urgent = bool(urgent_element and "სასწრაფოდ" in urgent_element.text)
                
                # Create metadata
                metadata = JobMetadata(
                    is_expiring=False,
                    was_recently_updated=False,
                    has_salary_info=bool(salary),
                    is_new=False,
                    is_in_region=True,
                    is_urgent=is_urgent,
                    is_vip=False
                )
                
                # Create job listing
                job_listing = JobListing(
                    id=job_id,
                    platform=Platform.SS_GE,
                    title=job_title,
                    url=job_url,
                    short_description=short_description,
                    company=company,
                    location=location,
                    salary=salary,
                    dates=dates,
                    metadata=metadata
                )
                
                job_listings.append(job_listing)
                
            except Exception as e:
                # Log the error but continue processing other jobs
                print(f"Error parsing job listing: {str(e)}")
                continue
        
        return job_listings
    
    def _parse_salary(self, salary_text: str) -> Optional[Salary]:
        """Parse salary information from text like '2,800 - 3,000 ₾ თვეში'."""
        if not salary_text:
            return None
        
        try:
            # Remove currency symbol and period indicator
            clean_text = salary_text.replace("₾", "").replace("თვეში", "").strip()
            
            # Look for range pattern like "2,800 - 3,000"
            range_match = re.search(r"([\d,]+)\s*-\s*([\d,]+)", clean_text)
            if range_match:
                min_amount = int(range_match.group(1).replace(",", ""))
                max_amount = int(range_match.group(2).replace(",", ""))
                
                return Salary(
                    min_amount=min_amount,
                    max_amount=max_amount,
                    currency="GEL",
                    period="monthly"
                )
            
            # Look for single amount
            single_match = re.search(r"([\d,]+)", clean_text)
            if single_match:
                amount = int(single_match.group(1).replace(",", ""))
                
                return Salary(
                    min_amount=amount,
                    max_amount=amount,
                    currency="GEL",
                    period="monthly"
                )
        
        except Exception:
            pass
        
        return None
    
    def parse_job_detail(self, soup: BeautifulSoup, job_id: str) -> Dict[str, Any]:
        """Parse detailed job information from jobs.ss.ge job detail page."""
        try:
            # For now, return basic structure since we need to see the actual detail page structure
            return {
                "id": job_id,
                "platform": "jobs.ss.ge",
                "title": "Job Detail",
                "description": "Full job description",
                "requirements": [],
                "responsibilities": [],
                "benefits": [],
                "skills": [],
                "contact_info": {}
            }
        except Exception as e:
            return {
                "id": job_id,
                "error": str(e)
            } 