import requests, re, csv, sys, os, time, json
from urllib.parse import urljoin, urlparse
from collections import deque, defaultdict
from datetime import datetime
import pandas as pd

# Setup path for debug
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from core.util.functions.debug import debug
from core.util.functions.config import config
from core.util.functions.env import env

interrupted = False

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
EXPORT_DIR = os.path.normpath(os.path.join(CURRENT_DIR, "exports"))
os.makedirs(EXPORT_DIR, exist_ok=True)

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
VALID_PAGE_EXTENSIONS = { '', '.html', '.htm', '.php', '.asp', '.aspx', '.jsp', '.jspx', '.cfm', '.cgi', '.pl', '.xhtml', '.shtml' }

DISABLE_TARGET_FILTER = env("DISABLE_TARGET_USERNAMES", "false").lower() == "true"
# TARGETS = config("target-usernames")
# DO_NOT_ALLOW = config("do-not-allow-in-username")
# EXCLUDE_EXTENSIONS = config("exclude-extensions")

with open(os.path.join(CURRENT_DIR, "config.json")) as f:
    CONFIG = json.load(f)

TARGETS = CONFIG.get("target-usernames", [])
DO_NOT_ALLOW = CONFIG.get("do-not-allow-in-username", [])
EXCLUDE_EXTENSIONS = CONFIG.get("exclude-extensions", [])

def should_skip(url):
    path = urlparse(url).path.lower()
    ext = os.path.splitext(path)[1]
    return ext in EXCLUDE_EXTENSIONS or (ext and ext not in VALID_PAGE_EXTENSIONS)

def is_valid_email(email):
    if DISABLE_TARGET_FILTER:
        return True
    username = email.split('@')[0].lower()
    return any(t in username for t in TARGETS) and not any(x in username for x in DO_NOT_ALLOW)

def save_all_results(all_results):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    export_path = os.path.join(EXPORT_DIR, f"{timestamp}_emails.csv")
    with open(export_path, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["#", "Website-#", "Website URL", "Email", "Found At URL"])
        idx = 1
        for site_num, site in enumerate(all_results, 1):
            for email, found_url in all_results[site]:
                writer.writerow([idx, site_num, site, email, found_url])
                idx += 1
    print(f"\nSaved results to {export_path}")
    debug(f"Saved results to {export_path}")

def crawl_site(website_url, email_threshold, timeout_minutes):
    queue = deque([(website_url, 0)])
    visited = set()
    found_emails = set()
    email_to_url = []
    domain = urlparse(website_url).netloc
    timeout_secs = timeout_minutes * 60
    start_time = time.time()

    try:
        while queue and (time.time() - start_time) < timeout_secs and len(found_emails) < email_threshold:
            current_url, level = queue.popleft()
            if current_url in visited or should_skip(current_url):
                continue
            visited.add(current_url)
            try:
                r = requests.get(current_url, timeout=10)
                text = r.text
                if int(env("DEBUG_LEVEL", 1)) >= 2:
                    debug(f"Fetched: {current_url}\n{text[:200]}")
            except Exception as e:
                debug(f"Request failed: {current_url} -> {e}")
                continue

            for email in set(EMAIL_REGEX.findall(text)):
                if is_valid_email(email) and email not in found_emails:
                    found_emails.add(email)
                    email_to_url.append((email, current_url))

            for link in re.findall(r'href=["\'](.*?)["\']', text):
                absolute = urljoin(current_url, link)
                parsed = urlparse(absolute)
                if parsed.netloc == domain and absolute not in visited:
                    queue.append((absolute, level + 1))

            debug(f"Checked {current_url} | Level {level} | Emails found: {len(found_emails)}")

    except KeyboardInterrupt:
        global interrupted
        interrupted = True
        debug("Interrupted during crawl of: " + website_url)
        return email_to_url

    if not queue:
        debug(f"Stopped crawling {website_url}: No more URLs to search.")
    elif time.time() - start_time >= timeout_secs:
        debug(f"Stopped crawling {website_url}: Timeout threshold reached.")
    elif len(found_emails) >= email_threshold:
        debug(f"Stopped crawling {website_url}: Email count threshold reached.")

    return email_to_url

# Read from CSV
input_csv = sys.argv[1] if len(sys.argv) > 1 else os.path.join(CURRENT_DIR, "website_input.csv")
df = pd.read_csv(input_csv)
all_results = defaultdict(list)

RESUME_FILE = f"{input_csv}--emails-resume.txt"
resume_from = 0

if os.path.exists(RESUME_FILE):
    print(f"\nResume file found: {RESUME_FILE}")
    choice = input("Do you want to resume from last stopped index? (y/n): ").strip().lower()
    if choice == 'y':
        with open(RESUME_FILE) as f:
            resume_from = int(f.read().strip())

for idx, row in df.iterrows():
    if idx < resume_from:
        continue

    website = row['Website URL'].strip()
    email_threshold = int(row['Email Threshold'])
    timeout_threshold = int(row['Timeout Threshold (minutes)'])
    print(f"\n[{idx+1}] Crawling: {website}")
    results = []

    try:
        results = crawl_site(website, email_threshold, timeout_threshold)
    except KeyboardInterrupt:
        print(f"\nPaused. Resume info saved to {RESUME_FILE}")
        with open(RESUME_FILE, 'w') as f:
            f.write(str(idx))
        all_results[website].extend(results)  # `results` still has scraped emails
        break

    all_results[website].extend(results)
    if interrupted:
        break


save_all_results(all_results)
