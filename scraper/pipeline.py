from dataclasses import asdict
from typing import List, Dict, Any, AsyncGenerator, Tuple, Optional, TypedDict, cast
import asyncio
import logging
from scraper.collector import Collector, PAGE_SIZE
from scraper.parser import Parser
from utils.output_manager import OutputManager
from contextlib import asynccontextmanager
from model.data_models import ParsedJobRow, ParsedJobView, JobDates, JobCompany, JobMetadata

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JobSummaryDict(TypedDict):
    id: str
    title: str
    location: str
    metadata: Dict[str, bool]
    company: Dict[str, str]
    dates: Dict[str, Optional[str]]

class JobDetailDict(TypedDict, total=False):
    id: str
    title: str
    dates: Dict[str, Optional[str]]
    description_path: str
    error: str

class MergedJobDict(JobSummaryDict, total=False):
    description_path: str
    error: str

class Pipeline:
    """Manages the end-to-end pipeline for collecting and processing jobs."""
    
    def __init__(
        self,
        output_dir: str,
        job_count: int,
        local: str = "ge",
        location_id: Optional[int] = None,
        category_id: Optional[int] = None,
        query: Optional[str] = None,
        has_salary: bool = False,
        batch_size: int = 10,
        max_concurrent_details: int = 5,
        data_dir: str = "data"
    ):
        self.output_manager = OutputManager(output_dir)
        self.collector = Collector(local=local, job_count=job_count, location_id=location_id, category_id=category_id, query=query, has_salary=has_salary)
        self.parser = Parser(data_dir=data_dir)
        self.batch_size = batch_size
        self.max_concurrent_details = max_concurrent_details
        self.job_count = job_count
        self.semaphore = asyncio.Semaphore(max_concurrent_details)
        self.logger = logging.getLogger(f"{__name__}.Pipeline")

    @asynccontextmanager
    async def _rate_limit(self):
        """Context manager for rate limiting."""
        async with self.semaphore:
            yield

    async def process_job_detail(self, job_id: str, job_url: str) -> Tuple[str, JobDetailDict]:
        """Process a single job detail with proper error handling."""
        async with self._rate_limit():
            try:
                html = await self.collector.fetch_detail_page(None, job_url)  # None as session will be managed inside
                job_detail, description = await self.parser.parse_job_detail(html, job_id)
                
                # Ensure job_detail has the correct type
                if not isinstance(job_detail, ParsedJobView):
                    raise TypeError(f"Expected ParsedJobView, got {type(job_detail)}")
                
                job_description_path = await self.output_manager.save_description(job_id, description)
                
                # Update the job_detail object
                job_detail_dict = asdict(job_detail)
                job_detail_dict["description_path"] = job_description_path
                
                # Format dates properly in the dictionary
                if job_detail_dict.get("dates") and isinstance(job_detail_dict["dates"], dict):
                    dates_dict = job_detail_dict["dates"]
                    for key, value in dates_dict.items():
                        if hasattr(value, "isoformat"):
                            dates_dict[key] = value.isoformat()
                
                return job_id, cast(JobDetailDict, job_detail_dict)
            except Exception as e:
                self.logger.error(f"Error processing job {job_id}: {str(e)}")
                return job_id, cast(JobDetailDict, {"id": job_id, "error": str(e)})
    
    async def job_details_generator(
        self, job_ids: List[str]
    ) -> AsyncGenerator[Tuple[str, JobDetailDict], None]:
        """Generate job details one at a time as they complete."""
        job_urls = [
            f"https://jobs.ge/{self.collector.local}/?view=jobs&id={job_id}" 
            for job_id in job_ids
        ]
        
        # Process all jobs concurrently but yield as they complete
        tasks = [
            self.process_job_detail(job_id, job_url) 
            for job_id, job_url in zip(job_ids, job_urls)
        ]
        
        for completed_task in asyncio.as_completed(tasks):
            job_id, job_detail = await completed_task
            self.logger.info(f"Completed detail processing for job: {job_id}")
            yield job_id, job_detail

    async def merge_job_data(
        self, summary: JobSummaryDict, detail: JobDetailDict
    ) -> MergedJobDict:
        """Merge summary and detail data into a single job record."""
        merged = cast(MergedJobDict, {**summary})
        
        # Only merge valid details (no error)
        if 'error' not in detail and detail:
            if 'description_path' in detail:
                merged['description_path'] = detail['description_path']
                
        return merged

    async def job_summaries_generator(
        self
    ) -> AsyncGenerator[Dict[str, JobSummaryDict], None]:
        """Generate job summaries page by page."""
        job_count_on_last_page = self.job_count % PAGE_SIZE
        job_summaries: Dict[str, JobSummaryDict] = {}
        
        page_num = 1
        async for html in self.collector.fetch_pages_generator():
            on_last_page = self.collector.total_pages == page_num
            self.logger.info(f"Processing page {page_num}/{self.collector.total_pages}")
            
            # Parse all jobs from this page
            for job in self.parser.parse_job_list(
                html,
                job_count_on_last_page if on_last_page else None
            ):
                # Ensure we have a valid ParsedJobRow
                if not isinstance(job, ParsedJobRow):
                    self.logger.warning(f"Expected ParsedJobRow, got {type(job)}")
                    continue
                
                # Convert to dictionary with proper date formatting
                job_dict = asdict(job)
                
                # Format dates properly in the dictionary
                if job_dict.get("dates") and isinstance(job_dict["dates"], dict):
                    dates_dict = job_dict["dates"]
                    for key, value in dates_dict.items():
                        if hasattr(value, "isoformat"):
                            dates_dict[key] = value.isoformat()
                
                job_summaries[job.id] = cast(JobSummaryDict, job_dict)
            
            # Yield the batch of summaries from this page
            yield job_summaries
            page_num += 1
            # Clear to avoid keeping everything in memory
            job_summaries = {}
    
    async def process_job_stream(
        self
    ) -> AsyncGenerator[Tuple[str, Dict[str, Any]], None]:
        """Stream processing of jobs from summary to details to saving."""
        all_job_ids: List[str] = []
        
        # Process job summaries and collect IDs
        async for summaries_batch in self.job_summaries_generator():
            all_job_ids.extend(summaries_batch.keys())
            
            # Yield each summary for immediate processing
            for job_id, summary in summaries_batch.items():
                self.logger.debug(f"Yielding summary for job {job_id}")
                yield job_id, summary
        
        self.logger.info(f"Collected {len(all_job_ids)} job IDs, starting detail processing")
        
        # Process details in parallel but controlled batches
        for i in range(0, len(all_job_ids), self.batch_size):
            batch = all_job_ids[i:i + self.batch_size]
            self.logger.info(f"Processing batch {i//self.batch_size + 1}/{(len(all_job_ids) + self.batch_size - 1)//self.batch_size}")
            
            # Process details asynchronously as they complete
            async for job_id, detail in self.job_details_generator(batch):
                self.logger.debug(f"Yielding detail for job {job_id}")
                yield job_id, detail

    async def run(self) -> None:
        """Execute the complete pipeline with streaming processing."""
        job_details: Dict[str, JobDetailDict] = {}  # Store details temporarily
        job_summaries: Dict[str, JobSummaryDict] = {}  # Store summaries temporarily
        processed_count = 0
        error_count = 0
        
        self.logger.info("Starting job processing pipeline")
        
        # Process the entire job stream
        async for job_id, data in self.process_job_stream():
            # Determine if this is a summary or detail based on content
            if isinstance(data, dict) and ('description_path' in data or 'error' in data):
                job_details[job_id] = cast(JobDetailDict, data)
                if 'error' in data:
                    error_count += 1
                    self.logger.warning(f"Job {job_id} has errors: {data.get('error')}")
            else:
                job_summaries[job_id] = cast(JobSummaryDict, data)
            
            # If we have both summary and detail for a job, merge and save
            if job_id in job_summaries and job_id in job_details:
                try:
                    merged_job = await self.merge_job_data(
                        job_summaries[job_id],
                        job_details[job_id]
                    )
                    await self.output_manager.save_job_temp(job_id, merged_job)
                    
                    # Clean up memory
                    del job_summaries[job_id]
                    del job_details[job_id]
                    processed_count += 1
                    
                    if processed_count % 10 == 0:
                        self.logger.info(f"Processed {processed_count} jobs so far")
                        
                except Exception as e:
                    self.logger.error(f"Error processing job {job_id}: {str(e)}")
                    error_count += 1
        
        # Handle any jobs that didn't get processed (missing summary or detail)
        remaining_jobs = set(job_summaries.keys()).union(set(job_details.keys()))
        if remaining_jobs:
            self.logger.warning(f"{len(remaining_jobs)} jobs had incomplete data and weren't fully processed")
        
        await self.output_manager.finalize()
        self.logger.info(f"Pipeline complete: {processed_count} jobs processed successfully, {error_count} errors")
