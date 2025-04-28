import re
import time
import random
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from core.util.functions.email_extractor import extract_emails, is_main_email

class EmailScraper:
    def __init__(self, base_url):
        self.base_url = self._normalize_url(base_url)
        self.domain = self._extract_domain(self.base_url)
        self.visited_urls = set()
        self.emails = set()
        # Rotate between different user agents to avoid blocking
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:53.0) Gecko/20100101 Firefox/53.0',
            'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0; Trident/5.0)',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15',
            'Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148'
        ]
    
    def _get_headers(self):
        """Get random user agent headers to avoid detection"""
        user_agent = random.choice(self.user_agents)
        return {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def _normalize_url(self, url):
        """Ensure URL has proper scheme"""
        if not url.startswith(('http://', 'https://')):
            return 'http://' + url
        return url
    
    def _extract_domain(self, url):
        """Extract domain from URL"""
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        # Remove www. if present
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    
    def get_domain(self):
        """Return the domain of the website"""
        return self.domain
    
    def _is_valid_url(self, url):
        """Check if URL is valid and belongs to the same domain"""
        parsed_url = urlparse(url)
        return bool(parsed_url.netloc) and self.domain in parsed_url.netloc
    
    def _get_links(self, soup, current_url):
        """Extract all links from the page"""
        links = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            full_url = urljoin(current_url, href)
            if self._is_valid_url(full_url) and full_url not in self.visited_urls:
                links.append(full_url)
        return links
    
    def _extract_emails_from_page(self, html_content):
        """Extract emails from page content"""
        # Use the improved email extractor
        page_emails = extract_emails(html_content, self.domain)
        
        # Filter to only include "main" emails
        main_emails = [email for email in page_emails if is_main_email(email)]
        
        return main_emails
    
    def _try_contact_page(self):
        """Try to directly access common contact page URLs"""
        contact_paths = [
            '/contact', '/contact-us', '/contact.html', '/contact-us.html',
            '/contactus', '/contactus.html', '/about/contact', '/get-in-touch',
            '/reach-us', '/connect', '/about-us/contact', '/contact.php'
        ]
        
        emails = []
        for path in contact_paths:
            contact_url = urljoin(self.base_url, path)
            if contact_url in self.visited_urls:
                continue
                
            print(f"  Trying contact page: {contact_url}")
            self.visited_urls.add(contact_url)
            
            try:
                # Add a delay to avoid being blocked
                time.sleep(random.uniform(1.0, 3.0))
                
                response = requests.get(contact_url, headers=self._get_headers(), timeout=10)
                if response.status_code == 200:
                    page_emails = self._extract_emails_from_page(response.text)
                    if page_emails:
                        print(f"  Found {len(page_emails)} emails on contact page")
                        emails.extend(page_emails)
            except Exception as e:
                print(f"  Error accessing contact page: {str(e)}")
                
        return emails
    
    def scrape_with_thresholds(self, email_threshold, timeout_seconds):
        """
        Scrape website for emails with thresholds
        
        Args:
            email_threshold: Number of emails to find before stopping
            timeout_seconds: Maximum time allowed for scraping in seconds
            
        Returns:
            List of found emails
        """
        start_time = time.time()
        urls_to_visit = [self.base_url]
        
        print(f"Starting scrape of {self.base_url}")
        print(f"Looking for up to {email_threshold} main emails")
        print(f"Timeout set to {timeout_seconds} seconds")
        
        # First try direct contact pages for efficiency
        contact_emails = self._try_contact_page()
        self.emails.update(contact_emails)
        
        # If we already have enough emails from contact pages, return early
        if len(self.emails) >= email_threshold:
            print(f"Found sufficient emails from contact pages: {len(self.emails)}")
            return list(self.emails)
        
        # Otherwise continue with regular crawling
        while urls_to_visit and len(self.emails) < email_threshold:
            # Check timeout
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout_seconds:
                print(f"Timeout reached after {elapsed_time:.2f} seconds")
                break
                
            # Get next URL
            current_url = urls_to_visit.pop(0)
            if current_url in self.visited_urls:
                continue
                
            print(f"Scraping: {current_url}")
            self.visited_urls.add(current_url)
            
            try:
                # Add a delay between requests to avoid being blocked
                time.sleep(random.uniform(0.5, 2.0))
                
                # Fetch page with random user agent
                response = requests.get(current_url, headers=self._get_headers(), timeout=10)
                if response.status_code != 200:
                    print(f"  Status code: {response.status_code}, skipping")
                    continue
                    
                # Parse HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract emails
                page_emails = self._extract_emails_from_page(response.text)
                
                # Add new emails to our set
                new_emails = set(page_emails) - self.emails
                self.emails.update(new_emails)
                
                # Print progress
                if new_emails:
                    print(f"  Found {len(new_emails)} new main emails. Total: {len(self.emails)}")
                    for email in new_emails:
                        print(f"    - {email}")
                
                # Check if we've reached the threshold
                if len(self.emails) >= email_threshold:
                    print(f"Email threshold reached: {email_threshold}")
                    break
                
                # Get more links to visit
                new_links = self._get_links(soup, current_url)
                urls_to_visit.extend(new_links)
                
                # Print progress on links
                if new_links:
                    print(f"  Found {len(new_links)} new links to explore")
                
            except requests.exceptions.RequestException as e:
                print(f"  Request error for {current_url}: {str(e)}")
            except Exception as e:
                print(f"  Error processing {current_url}: {str(e)}")
        
        # Return list of emails
        return list(self.emails)
