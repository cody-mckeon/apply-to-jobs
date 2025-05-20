import os
import sqlite3
import yaml
from datetime import datetime


def load_config(config_path="config/config.yaml"):
    """
    Load settings from the YAML config file.
    """
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def init_filtered_table(db_path):
    """
    Create the filtered_jobs table if it doesn't exist.
    """
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS filtered_jobs (
            id INTEGER PRIMARY KEY,
            title TEXT,
            company TEXT,
            location TEXT,
            link TEXT UNIQUE,
            fetched_at TEXT
        )
        '''
    )
    conn.commit()
    conn.close()


def filter_jobs(db_path, include_keywords, exclude_keywords):
    """
    Read from job_listings, filter based on include/exclude keywords,
    and insert passing rows into filtered_jobs.
    Returns the number of jobs added.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Ensure filtered_jobs exists
    init_filtered_table(db_path)

    # Fetch all listings
    cur.execute("SELECT * FROM job_listings")
    rows = cur.fetchall()

    added = 0
    for row in rows:
        title_lower = row['title'].lower()
        # include if any include keyword matches
        if not any(kw.lower() in title_lower for kw in include_keywords):
            continue
        # exclude if any exclude keyword matches
        if any(kw.lower() in title_lower for kw in exclude_keywords):
            continue

        try:
            cur.execute(
                '''
                INSERT INTO filtered_jobs (id, title, company, location, link, fetched_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ''',
                (
                    row['id'], row['title'], row['company'],
                    row['location'], row['link'], row['fetched_at']
                )
            )
            added += 1
        except sqlite3.IntegrityError:
            # skip duplicates
            continue

    conn.commit()
    conn.close()
    return added


def main():
    cfg = load_config()
    db_path = cfg.get('db_path', 'data/applied_jobs.db')
    include_keywords = cfg.get('include_keywords', [])
    exclude_keywords = cfg.get('exclude_keywords', [])

    print(f"▶ Filtering jobs using include={include_keywords} exclude={exclude_keywords}")
    count = filter_jobs(db_path, include_keywords, exclude_keywords)
    print(f"▶ Added {count} jobs to filtered_jobs table in {db_path}")


if __name__ == '__main__':
    main()

