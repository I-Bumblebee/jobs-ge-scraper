import asyncio
import json
import os
from typing import Dict, Any
import aiofiles


class OutputManager:
    """Manages the output of jobs data using an efficient temporary file approach."""
    
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.descriptions_dir = os.path.join(output_dir, "descriptions")
        self.temp_dir = os.path.join(output_dir, "temp")
        self.final_jobs_file = os.path.join(output_dir, "jobs.json")
        self._ensure_directories()

    def _ensure_directories(self):
        """Create necessary directories if they don't exist."""
        os.makedirs(self.descriptions_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)

    async def save_description(self, job_id: str, description: str) -> str:
        """Save job description to a file and return the path."""
        description_path = os.path.join(self.descriptions_dir, f"job-description-{job_id}.html")
        async with aiofiles.open(description_path, 'w', encoding='utf-8') as f:
            await f.write(description)
        return description_path

    async def save_job_temp(self, job_id: str, job_data: Dict[str, Any]):
        """Save job data to a temporary file."""
        temp_path = os.path.join(self.temp_dir, f"job-{job_id}.json")
        async with aiofiles.open(temp_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(job_data, default=str, ensure_ascii=False, indent=2))

    async def finalize(self):
        """Combine all temporary files into a single final JSON file."""
        all_jobs = []
        
        # Read all temporary files
        async def read_temp_file(filename):
            filepath = os.path.join(self.temp_dir, filename)
            async with aiofiles.open(filepath, 'r', encoding='utf-8') as f:
                content = await f.read()
                return json.loads(content)

        # Get list of all temporary files
        temp_files = [f for f in os.listdir(self.temp_dir) if f.endswith('.json')]
        
        # Read all files concurrently
        tasks = [read_temp_file(filename) for filename in temp_files]
        job_data = await asyncio.gather(*tasks)
        all_jobs.extend(job_data)

        # Write final file
        async with aiofiles.open(self.final_jobs_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(all_jobs, default=str, ensure_ascii=False, indent=2))

        # Cleanup temporary files
        for filename in temp_files:
            os.remove(os.path.join(self.temp_dir, filename))
        os.rmdir(self.temp_dir)
