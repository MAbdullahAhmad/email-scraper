import re

def extract_emails(text, domain=None):
    """
    Extract email addresses from text with improved regex
    
    Args:
        text: Text to extract emails from
        domain: Domain to filter emails by (optional)
        
    Returns:
        Set of email addresses
    """
    # Improved regex pattern for email addresses
    # This pattern is more specific to avoid matching non-email strings like image filenames
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    
    # Find all matches
    emails = re.findall(email_pattern, text)
    
    # Filter out non-generic emails (if domain is provided)
    if domain:
        # Keep only emails from the specified domain
        domain_emails = [email for email in emails if email.lower().endswith('@' + domain.lower())]
        
        # Filter for generic emails (info@, sales@, admin@, etc.)
        generic_prefixes = ['info', 'sales', 'admin', 'contact', 'support', 'hello', 'help',
                           'office', 'media', 'press', 'careers', 'jobs', 'hr', 'marketing',
                           'webmaster', 'service', 'enquiry', 'enquiries', 'general', 'mail',
                           'business', 'customerservice', 'feedback', 'inquiry', 'inquiries']
        
        generic_emails = []
        for email in domain_emails:
            prefix = email.split('@')[0].lower()
            # Check if the prefix is generic or contains generic terms
            if prefix in generic_prefixes or any(term in prefix for term in generic_prefixes):
                generic_emails.append(email)
        
        # If we found generic emails, return them
        if generic_emails:
            return set(generic_emails)
        
        # If no generic emails found but we have domain emails, return those
        if domain_emails:
            return set(domain_emails)
        
        # If no domain emails found, return empty set
        return set()
    
    # If no domain specified, return all emails
    return set(emails)
