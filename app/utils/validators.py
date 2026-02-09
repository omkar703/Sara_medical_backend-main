import phonenumbers
from phonenumbers import NumberParseException

def validate_phone_e164(cls, v):
    """
    Validates and formats a phone number to E.164 standard.
    Example: (555) 123-4567 -> +15551234567
    """
    if not v:
        return v
    
    try:
        # Allow parsing with or without '+' if we assume a default region, 
        # but for strict E.164, we usually expect the '+' or handle it gracefully.
        # Here we attempt to parse. If it fails, we raise an error.
        n = phonenumbers.parse(v, None) # None implies strictly international format with '+'
    except NumberParseException:
        # Optional: Try parsing with a default region (e.g., 'US' or 'IN') if '+' is missing
        # n = phonenumbers.parse(v, "US") 
        raise ValueError('Invalid phone number format. Please use international format (e.g., +14155552671)')

    if not phonenumbers.is_valid_number(n):
        raise ValueError('Invalid phone number.')

    return phonenumbers.format_number(n, phonenumbers.PhoneNumberFormat.E164)