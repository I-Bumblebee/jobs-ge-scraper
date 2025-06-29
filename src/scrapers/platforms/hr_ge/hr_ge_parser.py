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


class HrGeParser:
    """Parser for HR.ge specific HTML structure."""
    
    def __init__(self):
        """Initialize the parser."""
        self.georgian_months = [
            "იანვარი", "თებერვალი", "მარტი", "აპრილი", "მაისი", "ივნისი",
            "ივლისი", "აგვისტო", "სექტემბერი", "ოქტომბერი", "ნოემბერი", "დეკემბერი"
        ]
        
        # Georgian abbreviated months used in HR.ge
        self.georgian_abbrev_months = {
            "იან": 1, "თებ": 2, "მარ": 3, "აპრ": 4, "მაი": 5, "ივნ": 6,
            "ივლ": 7, "აგვ": 8, "სექ": 9, "ოქტ": 10, "ნოე": 11, "დეკ": 12
        }
    
    def _extract_job_id(self, url: Optional[str]) -> Optional[str]:
        """Extract job ID from HR.ge URL."""
        if not url:
            return None
        # HR.ge URLs are like: /announcement/417493/Local-Friend--Experience-Host
        match = re.search(r"/announcement/(\d+)", url)
        return match.group(1) if match else None
    
    def _parse_date_range(self, date_str: str) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Parse Georgian date range like '27 ივნ - 26 ივლ'."""
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
        """Parse single Georgian date like '27 ივნ'."""
        if not date_str or date_str.strip() == "":
            return None
        
        try:
            parts = date_str.strip().split()
            if len(parts) < 2:
                return None
            
            day = int(parts[0])
            month_str = parts[1]
            
            # Check abbreviated Georgian months
            month = self.georgian_abbrev_months.get(month_str)
            if month is None:
                # Check full month names
                if month_str in self.georgian_months:
                    month = self.georgian_months.index(month_str) + 1
            
            if month is None:
                return None
            
            year = datetime.now().year
            return datetime(year, month, day)
        except Exception:
            return None
    
    def parse_job_listings(self, soup: BeautifulSoup) -> List[JobListing]:
        """Parse job listings from HR.ge main page."""
        job_listings = []
        
        # Find the job listings container using the provided xpath
        # /html/body/app-root/app-layout-main/div/div/app-ann-search/div/div[3]/div[2]/app-spinner/div/div
        listings_container = soup.find("app-spinner")
        if not listings_container:
            return job_listings
        
        # Find all job announcement items directly (they're spread across multiple containers)
        job_items = listings_container.find_all("app-announcement-item")
        
        for item in job_items:
            try:
                # Extract title and URL from the title link
                title_link = item.find("a", class_="title title-link--without-large-size")
                if not title_link:
                    continue
                
                job_url = title_link.get("href", "")
                
                # Extract job title from the title frame
                title_frame = title_link.find("div", class_="title--bold-desktop")
                if not title_frame:
                    continue
                
                job_title = title_frame.text.strip()
                job_id = self._extract_job_id(job_url)
                
                # Convert relative URL to absolute URL
                if job_url and not job_url.startswith("http"):
                    job_url = f"https://www.hr.ge{job_url}"
                
                if not job_id:
                    continue
                
                # Extract location information
                location_container = item.find("hrra-announcement-location")
                location_text = ""
                if location_container:
                    location_items = location_container.find_all("span", class_="locaion-item")
                    location_parts = [loc.text.strip() for loc in location_items]
                    location_text = ", ".join(location_parts)
                
                # Parse location
                location = Location(city=location_text)
                if "remote" in location_text.lower():
                    location.is_remote = True
                
                # Extract company information
                company_element = item.find("a", class_="company__title")
                company_name = company_element.text.strip() if company_element else ""
                company_url = company_element.get("href", "") if company_element else ""
                
                # Convert relative company URL to absolute URL
                if company_url and not company_url.startswith("http"):
                    company_url = f"https://www.hr.ge{company_url}"
                
                # Extract company logo
                logo_element = item.find("img", class_="company-logo__img")
                logo_url = logo_element.get("src", "") if logo_element else ""
                
                company = Company(
                    name=company_name,
                    jobs_url=company_url if company_url else "",
                    logo_url=logo_url if logo_url else ""
                )
                
                # Extract dates from the date section
                date_section = item.find("div", class_="date")
                date_text = ""
                if date_section:
                    # Extract the date spans
                    date_spans = date_section.find_all("span")
                    if len(date_spans) >= 2:
                        start_date_text = date_spans[0].text.strip().replace(" - ", "")
                        end_date_text = date_spans[1].text.strip()
                        date_text = f"{start_date_text} - {end_date_text}"
                
                start_date, end_date = self._parse_date_range(date_text)
                
                dates = JobDates(
                    published=start_date,
                    deadline=end_date,
                    scraped=datetime.now()
                )
                
                # Check if it's a VIP listing
                ann_type_element = date_section.find("div", class_="ann-type") if date_section else None
                is_vip = bool(ann_type_element and "ვიპ" in ann_type_element.text)
                
                # Create metadata
                metadata = JobMetadata(
                    is_expiring=False,
                    was_recently_updated=False,
                    has_salary_info=False,  # Salary not shown in listings
                    is_new=False,
                    is_in_region=False,
                    is_vip=is_vip
                )
                
                # Create job listing
                job_listing = JobListing(
                    id=job_id,
                    platform=Platform.HR_GE,
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
                print(f"Error parsing HR.ge job listing: {str(e)}")
                continue
        
        return job_listings
    
    def parse_job_detail(self, soup: BeautifulSoup, job_id: str) -> Dict[str, Any]:
        """Parse detailed job information from HR.ge job detail page."""
        try:
            # Find the main content tile using the provided xpath
            # /html/body/app-root/app-layout-main/div/div/app-ann-details-page/app-spinner/div/div/div/div/div[2]/div[2]
            content_tile = soup.find("div", class_="tile tile--with-logo")
            if not content_tile:
                return {}
            
            # Extract job title
            title_container = content_tile.find("div", class_="ann-title-container__text")
            job_title = title_container.text.strip() if title_container else ""
            
            # Extract location information
            location_container = content_tile.find("hrra-announcement-location")
            location_text = ""
            if location_container:
                location_items = location_container.find_all("span", class_="locaion-item")
                location_parts = [loc.text.strip() for loc in location_items]
                location_text = ", ".join(location_parts)
            
            # Extract company name
            company_element = content_tile.find("a", class_="company-name__link")
            company_name = company_element.text.strip() if company_element else ""
            
            # Extract job details (employment type, etc.)
            details_list = content_tile.find("ul", class_="list")
            employment_type = ""
            if details_list:
                list_items = details_list.find_all("li", class_="list__item")
                employment_type = list_items[0].text.strip() if list_items else ""
            
            # Extract requirements
            requirements_section = content_tile.find("div", class_="requirements")
            requirements_text = ""
            if requirements_section:
                req_list = requirements_section.find("ul", class_="list")
                if req_list:
                    req_items = req_list.find_all("li", class_="list__item")
                    requirements_parts = []
                    for item in req_items:
                        # Extract the requirement text, excluding bullet points
                        type_span = item.find("span", class_="type")
                        if type_span:
                            requirements_parts.append(type_span.text.strip())
                    requirements_text = "; ".join(requirements_parts)
            
            # Extract job description
            description_section = content_tile.find("div", class_="description")
            description_text = ""
            if description_section:
                # Extract all text content, preserving structure
                description_text = description_section.get_text(separator="\n", strip=True)
            
            # Extract dates from additional info
            additional_info = content_tile.find("div", class_="additional-info")
            date_text = ""
            if additional_info:
                date_container = additional_info.find("div", class_="additional-info__date")
                if date_container:
                    date_spans = date_container.find_all("span")
                    if len(date_spans) >= 2:
                        start_date_text = date_spans[0].text.strip().replace(" - ", "")
                        end_date_text = date_spans[1].text.strip()
                        date_text = f"{start_date_text} - {end_date_text}"
            
            start_date, end_date = self._parse_date_range(date_text)
            
            # Check if it's VIP
            is_vip = False
            if additional_info:
                ann_type = additional_info.find("div", class_="additional-info__ann-type")
                is_vip = ann_type and "ვიპ" in ann_type.text
            
            return {
                "id": job_id,
                "title": job_title,
                "description": description_text,
                "company_name": company_name,
                "location": location_text,
                "employment_type": employment_type,
                "requirements": requirements_text,
                "published_date": start_date.isoformat() if start_date else None,
                "deadline_date": end_date.isoformat() if end_date else None,
                "is_vip": is_vip,
                "scraped_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error parsing HR.ge job detail: {str(e)}")
            return {"id": job_id, "error": str(e)}
    
    def _extract_salary_from_text(self, text: str) -> Optional[Dict[str, str]]:
        """Extract salary information from job description text."""
        if not text:
            return None
        
        # Look for Georgian lari patterns
        lari_patterns = [
            r"ხელფასი[:\s]+(\d+(?:-\d+)?)\s*ლარი",
            r"(\d+(?:-\d+)?)\s*ლარი",
            r"ხელფასი[:\s]+(\d+(?:-\d+)?)",
            r"(\d+)\s*-\s*(\d+)\s*ლარი",
        ]
        
        for pattern in lari_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return {
                    "amount": match.group(1),
                    "currency": "GEL",
                    "raw_text": match.group(0)
                }
        
        return None 