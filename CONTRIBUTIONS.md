# Contributions

### Mikheil Dzuliashvili - **mishodzuliashvili**
- **Feature:** Implemented async parser for jobs.ge with HTML and metadata extraction. [Link to PR](https://github.com/I-Bumblebee/jobs-ge-scraper/pull/1)
- **Refactor:** Extracted job ID logic to a helper function, added logging, and improved docstrings. [Link to Commit](https://github.com/I-Bumblebee/jobs-ge-scraper/commit/229e61cee2e4fcec99dc5d72b623a7d32a8fe0e3)
- **Feature:** Created a simple GUI using Tkinter to display the collected data. [Link to PR](https://github.com/I-Bumblebee/jobs-ge-scraper/pull/4)

### Luka Oniani - **lukabatoni**
- **Feature:** Added async Collector class for scraping jobs.ge with retries and rate limiting. [Link to PR](https://github.com/I-Bumblebee/jobs-ge-scraper/pull/2)
- **Added example usage to README.md.** [Link to Commit](https://github.com/I-Bumblebee/jobs-ge-scraper/commit/c8c9fc4eb13f5d78e2dfc77258ce1cdbd1f4eb7d)

### Luka Trapaidze - **I-Bumblebee**
- **Feature:** Composed collector and parser into a pipeline that uses generators and temporary files to be memory efficient [Link to PR](https://github.com/I-Bumblebee/jobs-ge-scraper/pull/3)
- **Refactor:** Used `asynccontextmanager` for coroutine control. [Link to Commit](https://github.com/I-Bumblebee/jobs-ge-scraper/commit/7fcd95768bfb5da7f47424f1e01b1cc2af69cbd6)
- **Implemented atomic output manager to persist intermediate data on disk and compose final output.** [Link to Commit](https://github.com/I-Bumblebee/jobs-ge-scraper/commit/a61107547c6fc1437bee1fc748f22fcd301020af)


### Note

- All contributions are made to the `main` branch.
- For detailed information about each contribution, please refer to the respective pull requests and commits on GitHub.
