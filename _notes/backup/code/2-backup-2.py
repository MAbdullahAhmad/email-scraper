import requests, re, csv, sys, os
from urllib.parse import urljoin, urlparse
from collections import deque
from datetime import datetime

# Setup path for debug
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from core.util.functions.debug import debug
from core.util.functions.config import config
from core.util.functions.env import env

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
EXPORT_DIR = os.path.normpath(os.path.join(CURRENT_DIR, "../../../exports"))
os.makedirs(EXPORT_DIR, exist_ok=True)

emails = set()
visited = set()
queue = deque()

url = input("Enter URL: ").strip()
parsed_domain = urlparse(url).netloc
queue.append((url, 0))

# Improved regex to catch tight patterns too
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

# Extensions to skip
SKIP_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.svg', '.css', '.js', '.ico', '.woff', '.woff2', '.ttf', '.eot', '.otf', '.webp', '.mp4', '.mp3', '.avi', '.mov', '.pdf', '.zip', '.rar', '.tar', '.gz'}

def should_skip(url):
  path = urlparse(url).path.lower()
  ext = os.path.splitext(path)[1]
  if ext and ext not in ('.html', '.htm', '.php', '.asp', '.aspx', '.jsp', '.cfm'):
    return True
  return False

def save_emails():
  timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
  export_path = os.path.join(EXPORT_DIR, f"{timestamp}_emails.csv")
  with open(export_path, "w", newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(["#", "Email"])
    for idx, email in enumerate(sorted(emails), 1):
      writer.writerow([idx, email])
  print(f"\nSaved {len(emails)} emails to {export_path}")
  debug(f"Saved {len(emails)} emails to {export_path}")

try:
  page_count = 0
  while queue:
    current_url, level = queue.popleft()
    if current_url in visited:
      continue
    visited.add(current_url)

    if should_skip(current_url):
      debug(f"Skipped non-page URL: {current_url}")
      continue

    try:
      r = requests.get(current_url, timeout=int(env("REQUEST_TIMEOUT", 5)))
      text_content = r.text
      if int(env("DEBUG_LEVEL", 1)) >= 2:
        debug(f"Response from {current_url}:\n{text_content}")
    except Exception as e:
      debug(f"Failed to fetch {current_url}: {e}")
      continue

    found_emails = set(EMAIL_REGEX.findall(text_content))
    emails.update(found_emails)

    links = re.findall(r'href=["\'](.*?)["\']', text_content)
    for link in links:
      absolute_link = urljoin(current_url, link)
      parsed_link = urlparse(absolute_link)
      if parsed_link.netloc == parsed_domain and absolute_link not in visited:
        queue.append((absolute_link, level + 1))

    page_count += 1
    short_url = current_url if len(current_url) <= 50 else current_url[:47] + '...'
    print(f"Page {page_count} | Level {level} | Total Emails {len(emails)} | {short_url}")
    debug(f"Page {page_count}, Level {level}, URL: {current_url}, Emails found so far: {len(emails)}")

except KeyboardInterrupt:
  print("\nInterrupted by user.")

finally:
  save_emails()
