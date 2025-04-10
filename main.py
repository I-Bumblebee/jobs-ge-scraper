from scraper.pipeline import Pipeline
"""main.py"""
import asyncio

async def main():
    pipeline = Pipeline(
        output_dir="data/output",
        job_count=2,
        locale="ge",
        batch_size=10,
        max_concurrent_details=5
    )
    await pipeline.run()

if __name__ == "__main__":
    asyncio.run(main())
