import re

def extract_emails(text, domain=None):
    """
    Extract valid email addresses from text
    
    Args:
        text: Text to search for emails
        domain: If provided, only return emails from this domain
        
    Returns:
        List of email addresses
    """
    # Improved regex pattern to match only valid email addresses
    # This pattern avoids matching file extensions like .png, .jpg, etc.
    email_pattern = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
    
    # Find all matches
    emails = re.findall(email_pattern, text)
    
    # Filter out non-generic emails (personal emails)
    generic_emails = []
    for email in emails:
        # Extract username part (before @)
        username = email.split('@')[0].lower()
        
        # Check if it's a generic email (not personal)
        if any(generic in username for generic in ['info', 'sales', 'admin', 'contact', 'support', 
                                                 'hello', 'help', 'office', 'mail', 'enquiry', 
                                                 'enquiries', 'general', 'hr', 'jobs', 'careers']):
            # If domain is specified, only include emails from that domain
            if domain:
                if domain in email.split('@')[1]:
                    generic_emails.append(email)
            else:
                generic_emails.append(email)
    
    return generic_emails
