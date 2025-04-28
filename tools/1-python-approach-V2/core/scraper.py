import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from core.util.functions.email_extractor import extract_emails

class EmailScraper:
    def __init__(self, base_url):
        self.base_url = self._normalize_url(base_url)
        self.domain = self._extract_domain(self.base_url)
        self.visited_urls = set()
        self.emails = set()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
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
        
        while urls_to_visit and len(self.emails) < email_threshold:
            # Check timeout
            if time.time() - start_time > timeout_seconds:
                print(f"Timeout reached after {timeout_seconds} seconds")
                break
                
            # Get next URL
            current_url = urls_to_visit.pop(0)
            if current_url in self.visited_urls:
                continue
                
            print(f"Scraping: {current_url}")
            self.visited_urls.add(current_url)
            
            try:
                # Fetch page
                response = requests.get(current_url, headers=self.headers, timeout=10)
                if response.status_code != 200:
                    continue
                    
                # Parse HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract emails
                page_emails = extract_emails(response.text, self.domain)
                self.emails.update(page_emails)
                
                # Print progress
                if page_emails:
                    print(f"Found {len(page_emails)} emails. Total: {len(self.emails)}")
                
                # Check if we've reached the threshold
                if len(self.emails) >= email_threshold:
                    print(f"Email threshold reached: {email_threshold}")
                    break
                
                # Get more links to visit
                new_links = self._get_links(soup, current_url)
                urls_to_visit.extend(new_links)
                
            except Exception as e:
                print(f"Error processing {current_url}: {str(e)}")
        
        # Return list of emails
        return list(self.emails)
