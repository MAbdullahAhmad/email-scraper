import re

def extract_emails(text, domain=None):
    """
    Extract valid email addresses from text.
    
    Args:
        text: Text to search for emails
        domain: Optional domain to filter emails
        
    Returns:
        List of valid email addresses
    """
    # Improved regex pattern that:
    # 1. Avoids matching image files or URLs with @ symbols
    # 2. Focuses on standard email format
    # 3. Requires proper TLDs
    
    # This pattern matches standard email format but excludes file extensions
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+(?!\.[a-zA-Z0-9]{2,4}\b)'
    
    # Find all matches
    emails = re.findall(email_pattern, text)
    
    # Also try to find emails that might be obfuscated with HTML entities
    # Common in anti-scraping techniques
    html_text = text
    try:
        # Replace HTML entities like &#64; with @
        for match in re.finditer(r'&#(\d+);', text):
            char_code = int(match.group(1))
            html_text = html_text.replace(match.group(0), chr(char_code))
            
        # Also try with hex entities like &#x40;
        for match in re.finditer(r'&#[xX]([0-9a-fA-F]+);', text):
            char_code = int(match.group(1), 16)
            html_text = html_text.replace(match.group(0), chr(char_code))
            
        # Look for emails in the decoded text
        if html_text != text:
            emails.extend(re.findall(email_pattern, html_text))
    except Exception:
        # If decoding fails, continue with original emails
        pass
    
    # Also look for common email protection patterns
    # For example: <span class="__cf_email__" data-cfemail="1a7f727b695a7d777b737634797577">
    try:
        for match in re.finditer(r'data-cfemail="([a-f0-9]+)"', text):
            hex_encoded = match.group(1)
            try:
                # Cloudflare email protection decoder
                decoded = decode_cloudflare_email(hex_encoded)
                if '@' in decoded:
                    emails.append(decoded)
            except Exception:
                pass
    except Exception:
        pass
    
    # Filter out non-email matches (like image files)
    filtered_emails = []
    for email in emails:
        # Skip if it looks like a file reference
        if re.search(r'\.(png|jpg|jpeg|gif|svg|webp|pdf|doc|docx)$', email, re.IGNORECASE):
            continue
            
        # If domain is specified, only include emails from that domain
        if domain and domain not in email.split('@')[1]:
            continue
            
        # Only include "main" emails (generic addresses)
        if is_main_email(email):
            filtered_emails.append(email)
    
    return filtered_emails

def decode_cloudflare_email(hex_encoded):
    """
    Decode Cloudflare's email protection encoding
    """
    decoded = ""
    hex_encoded = hex_encoded.strip()
    
    # Convert from hex to bytes
    hex_data = bytes.fromhex(hex_encoded)
    
    # The first byte is the key for XOR decoding
    key = hex_data[0]
    
    # XOR each byte with the key
    for i in range(1, len(hex_data)):
        decoded += chr(hex_data[i] ^ key)
        
    return decoded

def is_main_email(email):
    """
    Check if the email is a "main" email (generic address).
    
    Args:
        email: Email address to check
        
    Returns:
        True if it's a main email, False otherwise
    """
    # List of common generic email prefixes
    generic_prefixes = [
        'info', 'contact', 'sales', 'admin', 'support', 'hello',
        'office', 'mail', 'enquiry', 'enquiries', 'help',
        'service', 'services', 'careers', 'jobs', 'hr',
        'marketing', 'media', 'press', 'general', 'webmaster',
        'no-reply', 'noreply', 'no_reply', 'customerservice',
        'feedback', 'inquiry', 'inquiries', 'team', 'info',
        # Add more domain-specific prefixes
        'gcc', 'dcc', 'uae', 'dubai', 'abudhabi', 'sharjah',
        'projects', 'contracts', 'procurement', 'business',
        'reception', 'frontdesk', 'query', 'queries'
    ]
    
    # Get the username part (before @)
    username = email.split('@')[0].lower()
    
    # Check if the username is a generic prefix or contains only the domain name
    for prefix in generic_prefixes:
        if username == prefix or username.startswith(prefix + '.'):
            return True
            
    # If it contains dots or appears to be a personal name, it's likely not a main email
    if '.' in username and not any(username.startswith(prefix) for prefix in generic_prefixes):
        return False
        
    return True
