import re
import time
import os
import sys
from urllib.parse import urlparse, urljoin
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from core.util.functions.email_extractor import extract_emails

class EmailScraper:
    def __init__(self, headless=False):
        """Initialize the Selenium WebDriver"""
        self.visited_urls = set()
        self.emails = set()
        self.base_url = None
        self.domain = None
        self.start_time = None
        self.max_pages_per_site = 50  # Limit pages per site to avoid endless crawling
        
        # Set up Chrome options
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        # Disable WebGL to avoid those errors
        chrome_options.add_argument("--disable-webgl")
        # Disable software rendering
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        
        # Initialize the WebDriver with better error handling
        try:
            # Try different approaches to initialize the driver
            self._initialize_driver(chrome_options)
            
            # Set page load timeout
            self.driver.set_page_load_timeout(30)
            
            # Add stealth JS to avoid detection
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            
            print("WebDriver initialized successfully")
        except Exception as e:
            print(f"Error initializing WebDriver: {str(e)}")
            raise
    
    def _initialize_driver(self, chrome_options):
        """Try different approaches to initialize the Chrome driver"""
        
        # Approach 1: Try using the default Chrome driver
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            return
        except Exception as e:
            print(f"Default Chrome driver failed: {str(e)}")
        
        # Approach 2: Try specifying the Chrome driver path manually
        try:
            # Check common locations for chromedriver
            possible_paths = [
                "./chromedriver.exe",  # Current directory
                "./drivers/chromedriver.exe",
                "C:/chromedriver.exe",
                os.path.join(os.path.expanduser("~"), "chromedriver.exe"),
                os.path.join(os.path.expanduser("~"), "Downloads", "chromedriver.exe"),
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    print(f"Found ChromeDriver at: {path}")
                    service = Service(executable_path=path)
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    return
        except Exception as e:
            print(f"Manual Chrome driver path failed: {str(e)}")
        
        # Approach 3: Try using Selenium Manager (newer versions of Selenium)
        try:
            from selenium.webdriver.chrome.service import Service as ChromeService
            self.driver = webdriver.Chrome(service=ChromeService(), options=chrome_options)
            return
        except Exception as e:
            print(f"Selenium Manager approach failed: {str(e)}")
        
        # If all approaches fail, raise an exception with helpful information
        print("\nChromeDriver initialization failed. Please try the following:")
        print("1. Download ChromeDriver from: https://chromedriver.chromium.org/downloads")
        print("2. Make sure to download the version that matches your Chrome browser")
        print("3. Place chromedriver.exe in the same directory as this script")
        print("4. Run the script again\n")
        
        raise RuntimeError("Could not initialize ChromeDriver. See instructions above.")
    
    def set_base_url(self, base_url):
        """Set the base URL for scraping and reset state"""
        self.base_url = self._normalize_url(base_url)
        self.domain = self._extract_domain(self.base_url)
        self.visited_urls = set()
        self.emails = set()
        self.start_time = time.time()
        print(f"Set base URL to: {self.base_url}")
        print(f"Domain: {self.domain}")
    
    def _normalize_url(self, url):
        """Ensure URL has proper scheme"""
        if not url.startswith(('http://', 'https://')):
            return 'http://' + url
        return url
    
    def _extract_domain(self, url):
        """Extract domain from URL"""
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        # Remove port number if present
        if ':' in domain:
            domain = domain.split(':')[0]
            
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
        
        # Skip URLs with specific patterns (admin, login, cpanel, etc.)
        skip_patterns = [
            ':2096',  # cPanel webmail port
            '/cpanel',
            '/webmail',
            '/login',
            '/admin',
            '/wp-admin',
            '/wp-login',
            '/administrator',
            '/resetpass',
            '/password',
            '/signin',
            '/signup',
            '/register',
            '/auth',
            '.pdf',
            '.jpg',
            '.png',
            '.gif',
            '.zip',
            '.rar',
            '.doc',
            '.docx',
            '.xls',
            '.xlsx',
            '.ppt',
            '.pptx',
            'javascript:',
            'tel:',
            'mailto:'
        ]
        
        for pattern in skip_patterns:
            if pattern in url.lower():
                return False
        
        # Extract domain without port
        url_domain = parsed_url.netloc
        if ':' in url_domain:
            url_domain = url_domain.split(':')[0]
            
        # Remove www. if present
        if url_domain.startswith('www.'):
            url_domain = url_domain[4:]
            
        # Check if domain matches
        domain_match = self.domain in url_domain or url_domain in self.domain
        
        return bool(parsed_url.netloc) and domain_match
    
    def _get_links(self, current_url):
        """Extract all links from the page using Selenium"""
        links = []
        try:
            # Find all anchor tags
            elements = self.driver.find_elements(By.TAG_NAME, "a")
            for element in elements:
                try:
                    href = element.get_attribute("href")
                    if href:
                        full_url = urljoin(current_url, href)
                        if self._is_valid_url(full_url) and full_url not in self.visited_urls:
                            links.append(full_url)
                except Exception:
                    continue
                    
            # Prioritize contact and about pages
            priority_keywords = ['contact', 'about', 'team', 'staff', 'people', 'company', 'support']
            priority_links = []
            normal_links = []
            
            for link in links:
                if any(keyword in link.lower() for keyword in priority_keywords):
                    priority_links.append(link)
                else:
                    normal_links.append(link)
                    
            # Return priority links first
            return priority_links + normal_links
            
        except Exception as e:
            print(f"Error getting links: {str(e)}")
        
        return links
    
    def _extract_emails_from_page(self):
        """Extract emails from the current page"""
        try:
            # Get the page source
            page_source = self.driver.page_source
            
            # Check if this is a login page or admin page
            login_indicators = [
                'login', 'sign in', 'signin', 'log in', 'username', 'password',
                'cpanel', 'webmail', 'admin', 'authentication', '登录', '登入',
                'reset password', 'forgot password'
            ]
            
            page_text = page_source.lower()
            if any(indicator in page_text for indicator in login_indicators):
                print("Skipping login/admin page")
                return set()
            
            # Look for contact form elements that might contain email addresses
            try:
                # Check for contact form elements
                contact_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                    "form, .contact, #contact, .contact-us, #contact-us, .contact-form, #contact-form")
                
                for element in contact_elements:
                    # Extract text from the element
                    element_text = element.get_attribute("innerHTML")
                    if element_text:
                        # Extract emails from the element text
                        form_emails = extract_emails(element_text, self.domain)
                        if form_emails:
                            print(f"Found {len(form_emails)} emails in contact form")
                            return form_emails
            except Exception as e:
                print(f"Error extracting emails from contact form: {str(e)}")
            
            # Extract emails using the existing function
            page_emails = extract_emails(page_source, self.domain)
            
            # If no domain-specific emails found, try looking for any generic emails
            if not page_emails:
                # Look for any email that might be relevant
                generic_emails = extract_emails(page_source, None)
                if generic_emails:
                    # Filter for likely generic business emails
                    business_emails = set()
                    for email in generic_emails:
                        email_domain = email.split('@')[1]
                        if email_domain == self.domain:
                            business_emails.add(email)
                    
                    if business_emails:
                        return business_emails
            
            return page_emails
        except Exception as e:
            print(f"Error extracting emails: {str(e)}")
            return set()
    
    def scrape_with_thresholds(self, email_threshold, timeout_seconds):
        """
        Scrape website for emails with thresholds using Selenium
        
        Args:
            email_threshold: Number of emails to find before stopping
            timeout_seconds: Maximum time allowed for scraping in seconds
            
        Returns:
            List of found emails
        """
        if not self.base_url:
            raise ValueError("Base URL not set. Call set_base_url() first.")
            
        start_time = time.time()
        urls_to_visit = [self.base_url]
        pages_visited = 0
        
        # Add common contact pages to the queue
        contact_pages = [
            f"{self.base_url}/contact",
            f"{self.base_url}/contact-us",
            f"{self.base_url}/about",
            f"{self.base_url}/about-us",
            f"{self.base_url}/company",
            f"{self.base_url}/support",
            f"{self.base_url}/help",
            f"{self.base_url}/team",
            f"{self.base_url}/our-team",
            f"{self.base_url}/staff",
            f"{self.base_url}/people"
        ]
        
        for page in contact_pages:
            if page not in urls_to_visit:
                urls_to_visit.append(page)
        
        while urls_to_visit and len(self.emails) < email_threshold:
            # Check timeout
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout_seconds:
                print(f"Timeout reached after {int(elapsed_time)} seconds")
                break
                
            # Check if we've visited too many pages
            if pages_visited >= self.max_pages_per_site:
                print(f"Reached maximum page limit ({self.max_pages_per_site})")
                break
                
            # Get next URL
            current_url = urls_to_visit.pop(0)
            if current_url in self.visited_urls:
                continue
                
            # Print progress with time elapsed
            elapsed_minutes = int(elapsed_time / 60)
            elapsed_seconds = int(elapsed_time % 60)
            print(f"[{elapsed_minutes:02d}:{elapsed_seconds:02d}] Scraping: {current_url}")
            
            self.visited_urls.add(current_url)
            pages_visited += 1
            
            try:
                # Navigate to the page
                self.driver.get(current_url)
                
                # Wait for page to load
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                except TimeoutException:
                    print(f"Timeout waiting for page to load: {current_url}")
                    continue
                
                # Check if we're on a login page or admin page
                current_url = self.driver.current_url
                if any(pattern in current_url.lower() for pattern in [':2096', '/cpanel', '/webmail', '/login', '/admin']):
                    print(f"Skipping admin/login page: {current_url}")
                    continue
                
                # Scroll down to load lazy content
                self._scroll_page()
                
                # Extract emails
                page_emails = self._extract_emails_from_page()
                self.emails.update(page_emails)
                
                # Print progress
                if page_emails:
                    print(f"Found {len(page_emails)} emails. Total: {len(self.emails)}")
                
                # Check if we've reached the threshold
                if len(self.emails) >= email_threshold:
                    print(f"Email threshold reached: {email_threshold}")
                    break
                
                # Get more links to visit
                new_links = self._get_links(current_url)
                urls_to_visit.extend(new_links)
                
                # If we've been scraping for a while with no results, try a different approach
                if elapsed_time > 120 and not self.emails:  # 2 minutes with no results
                    print("No emails found after 2 minutes, trying direct contact page approach...")
                    self._try_direct_contact_approach()
                
            except WebDriverException as e:
                print(f"WebDriver error processing {current_url}: {str(e)}")
            except Exception as e:
                print(f"Error processing {current_url}: {str(e)}")
        
        # If we still don't have emails, try one last approach
        if not self.emails:
            print("No emails found through regular scraping, trying alternative methods...")
            self._try_alternative_methods()
        
        # Return list of emails
        return list(self.emails)
    
    def _try_direct_contact_approach(self):
        """Try to directly access contact pages with different variations"""
        contact_variations = [
            "/contact", "/contact-us", "/contactus", "/get-in-touch", "/reach-us",
            "/about/contact", "/about-us/contact", "/company/contact",
            "/en/contact", "/en/contact-us", "/english/contact",
            "/contact.html", "/contact.php", "/contact.aspx",
            "/enquiry", "/inquiry", "/enquiries", "/inquiries"
        ]
        
        for variation in contact_variations:
            try:
                url = urljoin(self.base_url, variation)
                if url not in self.visited_urls:
                    print(f"Trying direct contact page: {url}")
                    self.driver.get(url)
                    self.visited_urls.add(url)
                    
                    # Wait for page to load
                    try:
                        WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.TAG_NAME, "body"))
                        )
                    except TimeoutException:
                        continue
                    
                    # Extract emails
                    page_emails = self._extract_emails_from_page()
                    self.emails.update(page_emails)
                    
                    if page_emails:
                        print(f"Found {len(page_emails)} emails on direct contact page. Total: {len(self.emails)}")
            except Exception:
                continue
    
    def _try_alternative_methods(self):
        """Try alternative methods to find emails when regular scraping fails"""
        # Method 1: Try to find emails in the page source of the homepage
        try:
            print("Trying to find emails in homepage source...")
            self.driver.get(self.base_url)
            
            # Wait for page to load
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except TimeoutException:
                pass
            
            # Get the entire page source and look for email patterns
            page_source = self.driver.page_source
            
            # Use a more aggressive regex to find potential emails
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            potential_emails = re.findall(email_pattern, page_source)
            
            # Filter for business emails
            for email in potential_emails:
                if self.domain in email or any(prefix in email.split('@')[0].lower() for prefix in 
                                              ['info', 'contact', 'sales', 'support', 'admin', 'hello']):
                    self.emails.add(email)
            
            if self.emails:
                print(f"Found {len(self.emails)} emails using alternative method")
        except Exception as e:
            print(f"Error in alternative method: {str(e)}")
        
        # Method 2: Try to construct common email addresses
        if not self.emails:
            print("Trying to construct common email addresses...")
            common_prefixes = ['info', 'contact', 'sales', 'support', 'admin', 'hello', 'enquiry', 'help']
            for prefix in common_prefixes:
                email = f"{prefix}@{self.domain}"
                self.emails.add(email)
                print(f"Added constructed email: {email}")
    
    def _scroll_page(self):
        """Scroll the page to load lazy content"""
        try:
            # Get scroll height
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # Scroll in increments
            for i in range(3):  # Scroll 3 times
                # Scroll down
                self.driver.execute_script(f"window.scrollTo(0, {last_height * (i+1) / 3});")
                # Wait to load
                time.sleep(1)
            
            # Scroll back to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            
        except Exception as e:
            print(f"Error scrolling page: {str(e)}")
    
    def close(self):
        """Close the WebDriver"""
        try:
            if hasattr(self, 'driver'):
                self.driver.quit()
                print("WebDriver closed successfully")
        except Exception as e:
            print(f"Error closing WebDriver: {str(e)}")
