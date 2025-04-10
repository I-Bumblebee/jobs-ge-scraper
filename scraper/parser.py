import os
import json
from typing import Optional, Iterator
from bs4 import BeautifulSoup
import aiofiles
from datetime import datetime
from dataclasses import asdict
from model.data_models import JobCompany, JobDates, JobMetadata, ParsedJobRow, ParsedJobView

class Parser:
    """
    Parser for jobs.ge HTML content with memory-efficient handling of large descriptions.
    """
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize the parser.
        
        Args:
            data_dir: Directory to store job descriptions and other data
        """
        self.data_dir = data_dir
        self.descriptions_dir = os.path.join(data_dir, "descriptions")
        self.ensure_directories()
    
    def ensure_directories(self):
        """Create necessary directories if they don't exist."""
        os.makedirs(self.descriptions_dir, exist_ok=True)
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        if not date_str or date_str.strip() == "":
            return None

        georgian_months = [
            "იანვარი", "თებერვალი", "მარტი", "აპრილი", "მაისი", "ინვისი",
            "ივლისი", "აგვისტო", "სექტემბერი", "ოქტომბერი", "ნოემბერი", "დეკემბერი"
        ]

        english_months = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]

        try:
            parts = date_str.strip().split()
            if len(parts) < 2:
                return None

            day = int(parts[0])
            month_str = parts[1]

            month = None
            if month_str in georgian_months:
                month = georgian_months.index(month_str)
            elif month_str in english_months:
                month = english_months.index(month_str)

            if month is None:
                return None

            year = datetime.now().year
            return datetime(year, month + 1, day)
        except Exception:
            return None
    
    def parse_job_list(self, html: str) -> Iterator[ParsedJobRow]:
        """
        Parse job list HTML and yield job rows one at a time to conserve memory.
        
        Args:
            html: HTML content of the job list page
            
        Yields:
            ParsedJobRow objects, one at a time
        """
        soup = BeautifulSoup(html, 'html.parser')
        job_table = soup.find(id="job_list_table")
        
        if not job_table:
            return
            
        rows = job_table.find_all('tr')
        
        # Skip header row
        for row in rows[1:]:
            # Parse row similar to your JS implementation
            cells = row.find_all('td')
            if len(cells) < 6:
                continue
                
            # Star/favorite cell
            star_cell = cells[0]
            star_img = star_cell.find('img')
            is_favorite = star_img and "unstar" not in star_img.get('src', '')
            
            # Title cell
            title_cell = cells[1]
            job_link = title_cell.find('a')
            job_title = job_link.text.strip() if job_link else ""
            job_id = None
            if job_link and 'href' in job_link.attrs:
                # Extract ID from URL
                import re
                match = re.search(r'id=(\d+)', job_link.get('href', ''))
                job_id = match.group(1) if match else None
                
            location_element = title_cell.find('i')
            location = location_element.text.strip() if location_element else ""
            
            # Metadata from images
            metadata_images = [img.get('src', '') for img in title_cell.find_all('img')]
            metadata = JobMetadata(
                is_favorite=is_favorite,
                is_expiring=any("exp" in src for src in metadata_images),
                was_recently_updated=any("upd" in src for src in metadata_images),
                has_salary_info=any("salary" in src for src in metadata_images),
                is_new=any("new" in src for src in metadata_images),
                is_in_region=any("reg" in src for src in metadata_images)
            )
            
            # Company logo
            company_logo_cell = cells[2]
            company_logo_link = company_logo_cell.find('a')
            company_logo_img = company_logo_link.find('img') if company_logo_link else None
            company_logo_src = company_logo_img.get('src', '') if company_logo_img else ""
            
            # Company info
            company_cell = cells[3]
            company_link = company_cell.find('a')
            company_name = company_link.text.strip() if company_link else ""
            company_jobs_url = company_link.get('href', '') if company_link else ""
            
            # Dates
            publish_date_cell = cells[4]
            deadline_date_cell = cells[5]
            publish_date_str = publish_date_cell.text.strip() if publish_date_cell else ""
            deadline_date_str = deadline_date_cell.text.strip() if deadline_date_cell else ""
            
            dates = JobDates(
                published=self.parse_date(publish_date_str),
                deadline=self.parse_date(deadline_date_str)
            )
            
            job_row = ParsedJobRow(
                id=job_id,
                title=job_title,
                location=location,
                metadata=metadata,
                company=JobCompany(
                    name=company_name,
                    jobs_url=company_jobs_url,
                    logo_src=company_logo_src
                ),
                dates=dates
            )
            
            yield job_row
    
    async def parse_job_detail(self, html: str, job_id: str) -> ParsedJobView:
        """
        Parse job detail HTML and save large description to file.
        
        Args:
            html: HTML content of the job detail page
            job_id: Job ID for file naming
            
        Returns:
            ParsedJobView object with path to description file
        """
        soup = BeautifulSoup(html, 'html.parser')
        job_div = soup.find(id="job")
        
        if not job_div:
            raise ValueError(f"Job div not found for job ID {job_id}")
        
        # Extract title
        title_span = job_div.find('span')
        title = title_span.text.strip() if title_span else ""
        
        # Check if favorite
        star_icon = job_div.find('img')
        is_favorite = star_icon and "unstar" not in star_icon.get('src', '')
        
        # Find tables
        tables = job_div.find_all('table')
        if len(tables) < 2:
            raise ValueError(f"Required tables not found for job ID {job_id}")
        
        dtable = next((table for table in tables if table.get('class') and 'dtable' in table['class']), tables[1])
        table_rows = dtable.find_all('tr')
        
        if len(table_rows) < 4:
            raise ValueError(f"Required table rows not found for job ID {job_id}")
        
        # Parse dates
        date_row = table_rows[2]
        date_tags = date_row.find_all('b')
        
        dates = JobDates()
        if len(date_tags) >= 2:
            dates.published = self.parse_date(date_tags[0].text if date_tags[0] else "")
            dates.deadline = self.parse_date(date_tags[1].text if date_tags[1] else "")
        
        # Extract description and save to file
        description_row = table_rows[3]
        description_cell = description_row.find('td')
        description = description_cell.decode_contents() if description_cell else ""
        
        # Save description to file
        description_path = os.path.join(self.descriptions_dir, f"job-description-{job_id}.html")
        await self._save_description(description, description_path)
        
        return ParsedJobView(
            id=job_id,
            title=title,
            is_favorite=is_favorite,
            dates=dates,
            description_path=description_path
        )
    
    async def _save_description(self, description: str, path: str) -> None:
        """
        Save job description to file asynchronously.
        
        Args:
            description: HTML description content
            path: File path to save to
        """
        async with aiofiles.open(path, 'w', encoding='utf-8') as f:
            await f.write(description)
    
    async def save_job_summary(self, job: ParsedJobRow) -> None:
        """
        Save job summary to JSON file.
        
        Args:
            job: ParsedJobRow object to save
        """
        if not job.id:
            return
            
        summary_path = os.path.join(self.data_dir, f"job-summary-{job.id}.json")
        async with aiofiles.open(summary_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(asdict(job), default=str, ensure_ascii=False, indent=2))
    
    async def save_job_detail(self, job: ParsedJobView) -> None:
        """
        Save job detail to JSON file.
        
        Args:
            job: ParsedJobView object to save
        """
        detail_path = os.path.join(self.data_dir, f"job-detail-{job.id}.json")
        async with aiofiles.open(detail_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(asdict(job), default=str, ensure_ascii=False, indent=2))
