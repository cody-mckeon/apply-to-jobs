import yaml
from playwright.sync_api import sync_playwright

def save_login_state(cookies_path):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx = browser.new_context()
        page = ctx.new_page()
        page.goto("https://www.linkedin.com/login")
        print("▶ Please log in manually in the opened browser window.  ")
        page.wait_for_timeout(120000)  # gives you 2 minutes to complete any MFA/CAPTCHA
        ctx.storage_state(path=cookies_path)
        print(f"✅ Saved LinkedIn cookies to {cookies_path}")
        browser.close()

if __name__=="__main__":
    cfg = yaml.safe_load(open("config/config.yaml"))
    save_login_state(cfg["cookies_path"])
