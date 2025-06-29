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


class CvGeParser:
    """Parser for CV.ge specific HTML structure."""
    
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
        
        # Georgian abbreviated months used in CV.ge
        self.georgian_abbrev_months = {
            "იან": 1, "თებ": 2, "მარ": 3, "აპრ": 4, "მაი": 5, "ივნ": 6,
            "ივლ": 7, "აგვ": 8, "სექ": 9, "ოქტ": 10, "ნოე": 11, "დეკ": 12
        }
    
    def _extract_job_id(self, url: Optional[str]) -> Optional[str]:
        """Extract job ID from CV.ge URL."""
        if not url:
            return None
        # CV.ge URLs are like: /announcement/417196/some-title
        match = re.search(r"/announcement/(\d+)", url)
        return match.group(1) if match else None
    
    def _parse_date_range(self, date_str: str) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Parse Georgian date range like '25 ივნ - 20 ივლ'."""
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
        """Parse single Georgian date like '25 ივნ'."""
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
                elif month_str in self.english_months:
                    month = self.english_months.index(month_str) + 1
            
            if month is None:
                return None
            
            year = datetime.now().year
            return datetime(year, month, day)
        except Exception:
            return None
    
    def parse_job_listings(self, soup: BeautifulSoup) -> List[JobListing]:
        """Parse job listings from CV.ge main page."""
        job_listings = []
        
        # Find the item-listing container
        item_listing = soup.find("div", class_="item-listing")
        if not item_listing:
            return job_listings
        
        # Find all list-item divs
        list_items = item_listing.find_all("div", class_="list-item")
        
        for item in list_items:
            try:
                # Extract title and URL
                title_element = item.find("p", class_="list-item-title")
                if not title_element:
                    continue
                
                job_link = title_element.find("a", class_="announcement-list-item")
                if not job_link:
                    continue
                
                job_title = job_link.text.strip()
                job_url = job_link.get("href", "")
                job_id = self._extract_job_id(job_url)
                
                # Convert relative URL to absolute URL
                if job_url and not job_url.startswith("http"):
                    job_url = f"https://www.cv.ge{job_url}"
                
                if not job_id:
                    continue
                
                # Extract location from the tag
                location_element = item.find("span", class_="list-item-tag item-badge")
                location_text = location_element.text.strip() if location_element else ""
                
                # Parse location
                location = Location(city=location_text)
                if "remote" in location_text.lower():
                    location.is_remote = True
                
                # Extract company
                company_element = item.find("a", class_="list-item-company")
                company_name = company_element.text.strip() if company_element else ""
                company_url = company_element.get("href", "") if company_element else ""
                
                # Convert relative company URL to absolute URL
                if company_url and not company_url.startswith("http"):
                    company_url = f"https://www.cv.ge{company_url}"
                
                company = Company(
                    name=company_name,
                    jobs_url=company_url if company_url else "",
                    logo_url=""  # CV.ge doesn't show logos in listings
                )
                
                # Extract dates from the time element
                time_element = item.find("span", class_="list-item-time")
                date_text = ""
                if time_element:
                    # Get the text content, handling nested spans
                    date_text = time_element.get_text(strip=True)
                
                start_date, end_date = self._parse_date_range(date_text)
                
                dates = JobDates(
                    published=start_date,
                    deadline=end_date,
                    scraped=datetime.now()
                )
                
                # Check if it's a VIP listing
                vip_element = item.find("p", class_="list-item-location")
                is_vip = vip_element and "ვიპ" in vip_element.text
                
                # Create metadata
                metadata = JobMetadata(
                    is_expiring=False,  # CV.ge doesn't show expiring status in listings
                    was_recently_updated=False,
                    has_salary_info=False,  # Salary not shown in listings
                    is_new=False,
                    is_in_region=False,
                    is_vip=is_vip
                )
                
                # Create job listing
                job_listing = JobListing(
                    id=job_id,
                    platform=Platform.CV_GE,
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
                print(f"Error parsing CV.ge job listing: {str(e)}")
                continue
        
        return job_listings
    
    def parse_job_detail(self, soup: BeautifulSoup, job_id: str) -> Dict[str, Any]:
        """Parse detailed job information from CV.ge job detail page."""
        try:
            # Extract the main content
            entry_content = soup.find("div", class_="entry-content")
            if not entry_content:
                return {}
            
            # Extract description - the main text content
            description_text = entry_content.get_text(separator="\n", strip=True)
            
            # Extract company email from contact section
            contact_email = ""
            email_link = soup.find("a", href=lambda x: x and x.startswith("mailto:"))
            if email_link:
                contact_email = email_link.get("href", "").replace("mailto:", "")
            
            # Extract company name from sidebar
            company_name = ""
            company_widget = soup.find("aside", class_="widget_ci-company-info-widget")
            if company_widget:
                company_title = company_widget.find("p", class_="card-info-title")
                if company_title:
                    company_name = company_title.text.strip()
            
            # Parse salary information from description if present
            salary_info = self._extract_salary_from_text(description_text)
            
            # Extract requirements, responsibilities, etc. from description
            sections = self._parse_job_sections(description_text)
            
            return {
                "id": job_id,
                "description": description_text,
                "company_name": company_name,
                "contact_email": contact_email,
                "salary": salary_info,
                "requirements": sections.get("requirements", ""),
                "responsibilities": sections.get("responsibilities", ""),
                "conditions": sections.get("conditions", ""),
                "benefits": sections.get("benefits", ""),
                "scraped_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error parsing CV.ge job detail: {str(e)}")
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
    
    def _parse_job_sections(self, text: str) -> Dict[str, str]:
        """Parse different sections from job description text."""
        sections = {
            "requirements": "",
            "responsibilities": "",
            "conditions": "",
            "benefits": ""
        }
        
        # Keywords to identify sections in Georgian
        section_keywords = {
            "requirements": ["მოთხოვნები", "აუცილებელი მოთხოვნები", "კვალიფიკაცია"],
            "responsibilities": ["მოვალეობები", "სამუშაო მოვალეობები", "ფუნქციები"],
            "conditions": ["პირობები", "სამუშაო პირობები", "შეთავაზება"],
            "benefits": ["უპირატესობები", "ბენეფიტები", "დამატებითი პირობები"]
        }
        
        # Simple section extraction based on keywords
        lines = text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line starts a new section
            for section, keywords in section_keywords.items():
                for keyword in keywords:
                    if keyword in line and line.endswith(':'):
                        current_section = section
                        break
                if current_section == section:
                    break
            
            # Add content to current section
            if current_section and line not in [kw + ':' for keywords in section_keywords.values() for kw in keywords]:
                if sections[current_section]:
                    sections[current_section] += "\n" + line
                else:
                    sections[current_section] = line
        
        return sections 