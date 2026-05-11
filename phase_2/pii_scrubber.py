import re

def scrub_pii(text: str) -> str:
    """
    Scrubs common PII from text using regular expressions.
    - Email addresses
    - Phone numbers (various formats)
    - Potential account numbers (long digit sequences)
    """
    # Email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
    
    # Phone numbers (e.g., +91-9999999999, 9999999999, 09999999999)
    # This regex is broad to catch common Indian and international formats
    text = re.sub(r'\b(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', '[PHONE]', text)
    text = re.sub(r'\b\d{10}\b', '[PHONE]', text)
    
    # Long sequences of digits (potential account/card numbers)
    text = re.sub(r'\b\d{12,16}\b', '[ACCOUNT_NO]', text)
    
    return text
