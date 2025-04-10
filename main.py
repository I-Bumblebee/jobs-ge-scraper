from scraper.pipeline import Pipeline
from datetime import datetime
import asyncio


categories = {
    "All Categories": "",
    "Administration/Management": "1",
    "Finance, Statistics": "3",
    "Sales/Procurement": "2",
    "PR/Marketing": "4",
    "General Technical Staff": "18",
    "Logistics/Transport/Distribution": "5",
    "Construction/Repair": "11",
    "Cleaning": "16",
    "Security/Safety": "17",
    "IT/Programming": "6",
    "Media/Publishing": "13",
    "Education": "12",
    "Law": "7",
    "Medicine/Pharmacy": "8",
    "Beauty/Fashion": "14",
    "Food": "10",
    "Other": "9"
}

locations = {
    "Any Location": "",
    "Tbilisi": "1",
    "Abkhazeti AR": "15",
    "Adjara AR": "14",
    "Guria": "9",
    "Imereti": "8",
    "Kakheti": "3",
    "Kvemo Kartli": "5",
    "Mtskheta-Mtianeti": "4",
    "Racha-Lechkhumi, Lw. Svaneti": "12",
    "Samegrelo-Zemo Svaneti": "13",
    "Samtskhe-Javakheti": "7",
    "Shida Kartli": "6",
    "Abroad": "16",
    "Remote": "17"
}

async def main():
    timestamp = datetime.now().strftime("%Y_%m_%d__%H_%M_%S")
    output_path = f"data/output_{timestamp}"

    pipeline = Pipeline(
        output_dir=output_path,
        job_count=2,
        locale="ge",
        batch_size=10,
        has_salary=True,
        location_id=locations["Remote"],
        category_id=categories["IT/Programming"],
        max_concurrent_details=5
    )

    await pipeline.run()

if __name__ == "__main__":
    asyncio.run(main())
