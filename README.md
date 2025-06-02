This repository contains a Python-based automation pipeline to fetch recent job postings from LinkedIn, filter for entry-level roles, and automatically apply to them using LinkedIn’s Easy Apply feature.

## Create and Activate Virtual Environment
python3 -m venv venv
source venv/bin/activate      # on macOS/Linux

pip install playwright pyyaml

playwright install

## Workflow usage
python3 scripts/login_and_save_cookies.py

python3 scripts/fetch_listings.py

### Verify in SQLite CLI
sqlite3 data/applied_jobs.db
.tables
SELECT * FROM job_listings LIMIT 5;
.exit

### Filter Listings to Entry Level
python3 scripts/filter_listings.py

### Verify in SQLite 
sqlite3 data/applied_jobs.db
SELECT * FROM filtered_jobs;
.exit

