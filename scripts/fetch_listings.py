import os
import sqlite3
import yaml
from datetime import datetime
from playwright.sync_api import sync_playwright


def load_config(config_path="config/config.yaml"):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def init_db(db_path):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(
        '''
        CREATE TABLE IF NOT EXISTS job_listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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

def fetch_recent_jobs(linkedin_url, cookies_path=None, headless=True):
    jobs = []
    with sync_playwright() as p:
        # Launch Browser
        browser = p.chromium.launch(headless=headless)

        # Load stored session
        context_args = {}
        if cookies_path and os.path.exists(cookies_path):
            context_args['storage_state'] = cookies_path
        context = browser.new_context(**context_args)
        page = context.new_page()

        # Navigate and wait for content
        page.goto(linkedin_url, timeout=60000, wait_until='domcontentloaded')
        # Ensure the job list container is present
        page.wait_for_selector('li[data-occludable-job-id]', timeout=60000)

        print("▶ Page title:", page.title())
        print("▶ Page URL:", page.url)
        page.screenshot(path="debug.png", full_page=True)
        # Save full page HTML for inspection
        with open("debug.html", "w", encoding="utf-8") as f:
            f.write(page.content())


        # Scroll to bottom to trigger lazy-loading
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)
        
        # Select each job card by its data attribute
        cards = page.query_selector_all('li[data-occludable-job-id]')
        print(f"▶ Found {len(cards)} job cards on the page")

        jobs = []
        for card in cards:
            link_el = card.query_selector('a.job-card-container__link')
            if not link_el:
                continue
            href = link_el.get_attribute('href')
            # Build absolute URL
            link = href if href.startswith('http') else f"https://www.linkedin.com{href}"
            title = link_el.inner_text().strip()

            # Company name
            comp_el = card.query_selector('div.artdeco-entity-lockup__subtitle span')
            company = comp_el.inner_text().strip() if comp_el else ''

            # Location
            loc_el = card.query_selector('div.artdeco-entity-lockup__caption span')
            location = loc_el.inner_text().strip() if loc_el else ''

            jobs.append({
                'title': title,
                'company': company,
                'location': location,
                'link': link,
            })

        print(f"▶ Extracted {len(jobs)} jobs after parsing")

        # Persist updated session if cookies file provided
        if cookies_path:
            context.storage_state(path=cookies_path)
        browser.close()
        return jobs


def save_jobs_to_db(jobs, db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    for job in jobs:
        try:
            c.execute(
                '''
                INSERT INTO job_listings (title, company, location, link, fetched_at)
                VALUES (?, ?, ?, ?, ?)
                ''',
                (job['title'], job['company'], job['location'], job['link'], datetime.utcnow().isoformat())
            )
        except sqlite3.IntegrityError:
            # duplicate link, skip
            continue
    conn.commit()
    conn.close()


if __name__ == "__main__":
    cfg = load_config()
    db_path = cfg.get('db_path', 'data/applied_jobs.db')
    init_db(db_path)

    linkedin_url = cfg.get('linkedin_url')
    cookies_path = cfg.get('cookies_path', 'config/linkedin_cookies.json')

    if not linkedin_url:
        raise ValueError("linkedin_url must be set in config/config.yaml")

    jobs = fetch_recent_jobs(linkedin_url, cookies_path=cookies_path)
    save_jobs_to_db(jobs, db_path)
    print(f"Fetched and saved {len(jobs)} job listings.")
