import asyncio
import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
import aiofiles
from datetime import datetime


class OutputManager:
    """
    Enhanced output manager for handling job scraping data.
    Supports multiple output formats and efficient file management.
    """
    
    def __init__(self, output_dir: str):
        """
        Initialize the output manager.
        
        Args:
            output_dir: Base directory for all output files
        """
        self.output_dir = Path(output_dir)
        self.descriptions_dir = self.output_dir / "descriptions"
        self.temp_dir = self.output_dir / "temp"
        self.reports_dir = self.output_dir / "reports"
        
        # Output file paths
        self.final_jobs_file = self.output_dir / "jobs.json"
        self.summary_file = self.output_dir / "summary.json"
        
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create necessary directories if they don't exist."""
        for directory in [self.output_dir, self.descriptions_dir, self.temp_dir, self.reports_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    async def save_description(self, job_id: str, description: str, format: str = "html") -> str:
        """
        Save job description to a file.
        
        Args:
            job_id: Unique job identifier
            description: Job description content
            format: File format (html, txt, md)
            
        Returns:
            Path to the saved description file
        """
        filename = f"job-description-{job_id}.{format}"
        description_path = self.descriptions_dir / filename
        
        async with aiofiles.open(description_path, 'w', encoding='utf-8') as f:
            await f.write(description)
        
        return str(description_path)
    
    async def save_job_temp(self, job_id: str, job_data: Dict[str, Any]):
        """
        Save job data to a temporary file.
        
        Args:
            job_id: Unique job identifier
            job_data: Job data dictionary
        """
        temp_path = self.temp_dir / f"job-{job_id}.json"
        
        async with aiofiles.open(temp_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(job_data, default=str, ensure_ascii=False, indent=2))
    
    async def save_batch_temp(self, batch_data: List[Dict[str, Any]], batch_id: str):
        """
        Save a batch of jobs to a temporary file.
        
        Args:
            batch_data: List of job data dictionaries
            batch_id: Unique batch identifier
        """
        temp_path = self.temp_dir / f"batch-{batch_id}.json"
        
        async with aiofiles.open(temp_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(batch_data, default=str, ensure_ascii=False, indent=2))
    
    async def save_summary(self, summary_data: Dict[str, Any]):
        """
        Save pipeline execution summary.
        
        Args:
            summary_data: Summary data dictionary
        """
        async with aiofiles.open(self.summary_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(summary_data, default=str, ensure_ascii=False, indent=2))
    
    async def finalize(self, cleanup_temp: bool = True) -> Dict[str, Any]:
        """
        Combine all temporary files into final output and cleanup.
        
        Args:
            cleanup_temp: Whether to remove temporary files after finalization
            
        Returns:
            Summary of the finalization process
        """
        finalization_summary = {
            'start_time': datetime.now().isoformat(),
            'total_files_processed': 0,
            'total_jobs': 0,
            'errors': []
        }
        
        try:
            all_jobs = []
            
            # Read all temporary files
            temp_files = list(self.temp_dir.glob("*.json"))
            finalization_summary['total_files_processed'] = len(temp_files)
            
            for temp_file in temp_files:
                try:
                    async with aiofiles.open(temp_file, 'r', encoding='utf-8') as f:
                        content = await f.read()
                        data = json.loads(content)
                        
                        # Handle both single jobs and batches
                        if isinstance(data, list):
                            all_jobs.extend(data)
                        else:
                            all_jobs.append(data)
                            
                except Exception as e:
                    error_msg = f"Error reading {temp_file.name}: {str(e)}"
                    finalization_summary['errors'].append(error_msg)
            
            finalization_summary['total_jobs'] = len(all_jobs)
            
            # Write final combined file
            async with aiofiles.open(self.final_jobs_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(all_jobs, default=str, ensure_ascii=False, indent=2))
            
            # Create additional output formats
            await self._create_csv_output(all_jobs)
            await self._create_summary_report(all_jobs, finalization_summary)
            
            # Cleanup temporary files if requested
            if cleanup_temp:
                for temp_file in temp_files:
                    temp_file.unlink()
                
                # Remove temp directory if empty
                try:
                    self.temp_dir.rmdir()
                except OSError:
                    pass  # Directory not empty, leave it
            
            finalization_summary['end_time'] = datetime.now().isoformat()
            finalization_summary['output_files'] = {
                'jobs_json': str(self.final_jobs_file),
                'jobs_csv': str(self.output_dir / "jobs.csv"),
                'summary': str(self.summary_file),
                'descriptions_dir': str(self.descriptions_dir)
            }
            
        except Exception as e:
            error_msg = f"Finalization failed: {str(e)}"
            finalization_summary['errors'].append(error_msg)
            finalization_summary['end_time'] = datetime.now().isoformat()
        
        # Save finalization summary
        await self.save_summary(finalization_summary)
        
        return finalization_summary
    
    async def _create_csv_output(self, jobs_data: List[Dict[str, Any]]):
        """Create CSV output from jobs data."""
        if not jobs_data:
            return
        
        import csv
        csv_path = self.output_dir / "jobs.csv"
        
        # Define CSV columns based on common job fields
        columns = [
            'id', 'platform', 'title', 'company_name', 'location_city', 
            'location_is_remote', 'published_date', 'deadline_date', 
            'has_salary_info', 'job_type', 'category', 'url'
        ]
        
        # Write CSV file
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=columns)
            writer.writeheader()
            
            for job in jobs_data:
                row = {}
                for col in columns:
                    if col == 'company_name':
                        row[col] = job.get('company', {}).get('name', '')
                    elif col == 'location_city':
                        row[col] = job.get('location', {}).get('city', '')
                    elif col == 'location_is_remote':
                        row[col] = job.get('location', {}).get('is_remote', False)
                    elif col == 'published_date':
                        row[col] = job.get('dates', {}).get('published', '')
                    elif col == 'deadline_date':
                        row[col] = job.get('dates', {}).get('deadline', '')
                    elif col == 'has_salary_info':
                        row[col] = job.get('metadata', {}).get('has_salary_info', False)
                    else:
                        row[col] = job.get(col, '')
                
                writer.writerow(row)
    
    async def _create_summary_report(self, jobs_data: List[Dict[str, Any]], finalization_summary: Dict[str, Any]):
        """Create a summary report with statistics."""
        if not jobs_data:
            return
        
        # Calculate statistics
        stats = {
            'total_jobs': len(jobs_data),
            'platforms': {},
            'companies': {},
            'locations': {},
            'categories': {},
            'with_salary': 0,
            'remote_jobs': 0,
            'new_jobs': 0,
        }
        
        for job in jobs_data:
            # Platform stats
            platform = job.get('platform', 'unknown')
            stats['platforms'][platform] = stats['platforms'].get(platform, 0) + 1
            
            # Company stats
            company = job.get('company', {}).get('name', 'unknown')
            stats['companies'][company] = stats['companies'].get(company, 0) + 1
            
            # Location stats
            location = job.get('location', {}).get('city', 'unknown')
            stats['locations'][location] = stats['locations'].get(location, 0) + 1
            
            # Category stats
            category = job.get('category', 'unknown')
            stats['categories'][category] = stats['categories'].get(category, 0) + 1
            
            # Feature stats
            metadata = job.get('metadata', {})
            if metadata.get('has_salary_info'):
                stats['with_salary'] += 1
            if metadata.get('is_new'):
                stats['new_jobs'] += 1
            
            location_data = job.get('location', {})
            if location_data.get('is_remote'):
                stats['remote_jobs'] += 1
        
        # Sort statistics by count
        for key in ['platforms', 'companies', 'locations', 'categories']:
            stats[key] = dict(sorted(stats[key].items(), key=lambda x: x[1], reverse=True))
        
        # Create report
        report = {
            'generation_time': datetime.now().isoformat(),
            'finalization_summary': finalization_summary,
            'statistics': stats,
            'top_companies': dict(list(stats['companies'].items())[:10]),
            'top_locations': dict(list(stats['locations'].items())[:10]),
        }
        
        # Save report
        report_path = self.reports_dir / "summary_report.json"
        async with aiofiles.open(report_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(report, default=str, ensure_ascii=False, indent=2))
    
    def get_output_info(self) -> Dict[str, Any]:
        """Get information about output directory and files."""
        info = {
            'output_dir': str(self.output_dir),
            'directories': {
                'descriptions': str(self.descriptions_dir),
                'temp': str(self.temp_dir),
                'reports': str(self.reports_dir),
            },
            'files': {},
            'exists': {}
        }
        
        # Check which files exist
        files_to_check = {
            'jobs_json': self.final_jobs_file,
            'jobs_csv': self.output_dir / "jobs.csv",
            'summary': self.summary_file,
            'summary_report': self.reports_dir / "summary_report.json",
        }
        
        for name, path in files_to_check.items():
            info['files'][name] = str(path)
            info['exists'][name] = path.exists()
            if path.exists():
                info[f'{name}_size'] = path.stat().st_size
        
        # Count files in directories
        info['description_files_count'] = len(list(self.descriptions_dir.glob("*"))) if self.descriptions_dir.exists() else 0
        info['temp_files_count'] = len(list(self.temp_dir.glob("*"))) if self.temp_dir.exists() else 0
        
        return info 