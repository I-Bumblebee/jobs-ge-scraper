import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os
import asyncio
from main import main as run_scraper

DATA_DIR = "data"


class JobViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Jobs.ge Scraper Viewer")
        self.geometry("800x600")

        self.job_list = []
        self.output_path = ""

        self.create_widgets()

    def create_widgets(self):
        top_frame = ttk.Frame(self)
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        # Buttons for scraping and loading data
        scrape_btn = ttk.Button(
            top_frame, text="Run Scraper", command=self.run_scraper_async
        )
        scrape_btn.pack(side=tk.LEFT)

        load_btn = ttk.Button(
            top_frame, text="Load Latest", command=self.load_latest_data
        )
        load_btn.pack(side=tk.LEFT, padx=5)

        # Job list Treeview (table format)
        self.job_tree = ttk.Treeview(
            self, columns=("title", "company", "published", "deadline"), show="headings"
        )
        self.job_tree.heading("title", text="Title")
        self.job_tree.heading("company", text="Company")
        self.job_tree.heading("published", text="Published")
        self.job_tree.heading("deadline", text="Deadline")
        self.job_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Bind double click on the job tree to show job details
        self.job_tree.bind("<Double-1>", self.show_job_detail)

    def run_scraper_async(self):
        self.after(100, lambda: asyncio.run(self._scrape_and_load()))

    async def _scrape_and_load(self):
        # Run the scraper function (imported from main)
        await run_scraper()
        self.load_latest_data()

    def load_latest_data(self):
        try:
            # Find subdirectories starting with "output_"
            subdirs = [d for d in os.listdir(DATA_DIR) if d.startswith("output_")]
            if not subdirs:
                messagebox.showwarning("No Data", "No output directories found.")
                return

            # Sort and pick the latest subdirectory
            subdirs.sort(reverse=True)
            latest_dir = os.path.join(DATA_DIR, subdirs[0])
            self.output_path = latest_dir

            # Path to the JSON file with the job data
            json_path = os.path.join(latest_dir, "jobs.json")
            if not os.path.exists(json_path):
                messagebox.showerror("Error", f"No jobs.json found in {latest_dir}")
                return

            # Load the job data from the JSON file
            with open(json_path, "r", encoding="utf-8") as f:
                self.job_list = json.load(f)

            # Update the job list display
            self.update_tree()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update_tree(self):
        # Clear existing items in the Treeview
        for i in self.job_tree.get_children():
            self.job_tree.delete(i)

        # Insert new jobs into the Treeview
        for job in self.job_list:
            self.job_tree.insert(
                "",
                tk.END,
                values=(
                    job.get("title", ""),
                    job.get("company", {}).get("name", ""),
                    job["dates"].get("published", ""),
                    job["dates"].get("deadline", ""),
                ),
            )

    def show_job_detail(self, event):
        # Get the selected job from the treeview
        selected = self.job_tree.selection()
        if not selected:
            return

        # Get the job index and fetch the job data
        index = self.job_tree.index(selected[0])
        job = self.job_list[index]

        # Create a new window for job details
        win = tk.Toplevel(self)
        win.title(job.get("title", "Job Details"))
        win.geometry("600x400")

        # ScrolledText widget for displaying job description
        text = scrolledtext.ScrolledText(win, wrap=tk.WORD)
        text.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        # Path to the job description file
        description_path = os.path.join(
            self.output_path, "descriptions", f"job-description-{job['id']}.html"
        )

        # Check if the description file exists
        if os.path.exists(description_path):
            with open(description_path, "r", encoding="utf-8") as f:
                description = f.read()
            text.insert(tk.END, description)
        else:
            text.insert(tk.END, "No description available.")


if __name__ == "__main__":
    app = JobViewer()
    app.mainloop()
