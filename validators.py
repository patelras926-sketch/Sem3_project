# FarmIntel – Form validation (email, mobile, name, password, numbers)
import re
from decimal import Decimal, InvalidOperation

# Email: standard format
EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

# Mobile: 10 digits (India), optional leading +91 or 0
MOBILE_RE = re.compile(r'^(\+91|0)?[6-9]\d{9}$')

# Name: 2–150 chars, letters/spaces/hyphens/apostrophe (no digits for full name)
NAME_RE = re.compile(r'^[\w\s.\'-]{2,150}$', re.UNICODE)

# Password: min 6 chars, at least one letter and one digit
PASSWORD_MIN_LEN = 6
PASSWORD_RE = re.compile(r'^(?=.*[A-Za-z])(?=.*\d).{6,}$')

def validate_email(value):
    """Returns (True, None) if valid else (False, error_message)."""
    if not value or not value.strip():
        return False, 'Email is required.'
    v = value.strip()
    if len(v) > 120:
        return False, 'Email is too long.'
    if not EMAIL_RE.match(v):
        return False, 'Enter a valid email address.'
    return True, None

def validate_mobile(value, required=True):
    """Indian mobile: 10 digits, optionally with +91 or 0 prefix."""
    if not value or not str(value).strip():
        if required:
            return False, 'Mobile number is required.'
        return True, None
    v = re.sub(r'\s', '', str(value).strip())
    if not MOBILE_RE.match(v):
        return False, 'Enter a valid 10-digit mobile number (e.g. 9876543210).'
    return True, None

def normalize_mobile(value):
    """Return 10-digit Indian mobile (strip +91 or leading 0). Returns None if invalid/empty."""
    if not value or not str(value).strip():
        return None
    v = re.sub(r'\s', '', str(value).strip())
    if not MOBILE_RE.match(v):
        return None
    v = re.sub(r'^(\+91|0)', '', v)
    return v[-10:] if len(v) >= 10 else v

def validate_name(value, field_name='Name', required=True, min_len=2, max_len=150):
    """Full name: letters, spaces, hyphens, apostrophe."""
    if not value or not value.strip():
        if required:
            return False, f'{field_name} is required.'
        return True, None
    v = value.strip()
    if len(v) < min_len:
        return False, f'{field_name} must be at least {min_len} characters.'
    if len(v) > max_len:
        return False, f'{field_name} must be at most {max_len} characters.'
    if not NAME_RE.match(v):
        return False, f'{field_name} can only contain letters, spaces, hyphens and apostrophe.'
    return True, None

def validate_password(value, min_length=PASSWORD_MIN_LEN):
    """Min length and at least one letter and one digit."""
    if not value:
        return False, 'Password is required.'
    if len(value) < min_length:
        return False, f'Password must be at least {min_length} characters.'
    if not PASSWORD_RE.match(value):
        return False, 'Password must contain at least one letter and one number.'
    return True, None

def validate_confirm_password(password, confirm):
    if not confirm:
        return False, 'Please confirm your password.'
    if password != confirm:
        return False, 'Passwords do not match.'
    return True, None

def validate_land_area(value, required=False):
    """Non-negative number, optional."""
    if value is None or value == '' or (isinstance(value, str) and not value.strip()):
        if required:
            return False, 'Land area is required.'
        return True, None
    try:
        n = Decimal(str(value).strip())
        if n < 0:
            return False, 'Land area cannot be negative.'
        if n > 99999:
            return False, 'Land area is too large.'
        return True, None
    except (InvalidOperation, ValueError):
        return False, 'Enter a valid number for land area.'

def validate_positive_number(value, field_name='Field', required=False, allow_zero=True):
    """Numeric field: non-negative (or positive if allow_zero=False)."""
    if value is None or value == '' or (isinstance(value, str) and not value.strip()):
        if required:
            return False, f'{field_name} is required.'
        return True, None
    try:
        n = Decimal(str(value).strip())
        if allow_zero and n < 0:
            return False, f'{field_name} cannot be negative.'
        if not allow_zero and n <= 0:
            return False, f'{field_name} must be greater than zero.'
        return True, None
    except (InvalidOperation, ValueError):
        return False, f'Enter a valid number for {field_name}.'

def validate_int_range(value, field_name='Field', min_val=0, max_val=None, required=False):
    """Integer in range."""
    if value is None or value == '' or (isinstance(value, str) and not value.strip()):
        if required:
            return False, f'{field_name} is required.'
        return True, None
    try:
        n = int(float(value))
        if n < min_val:
            return False, f'{field_name} must be at least {min_val}.'
        if max_val is not None and n > max_val:
            return False, f'{field_name} must be at most {max_val}.'
        return True, None
    except (TypeError, ValueError):
        return False, f'Enter a valid number for {field_name}.'

def validate_decimal_range(value, field_name='Field', min_val=0, max_val=None, required=False):
    """Decimal in range (e.g. discount 0–100)."""
    if value is None or value == '' or (isinstance(value, str) and not value.strip()):
        if required:
            return False, f'{field_name} is required.'
        return True, None
    try:
        n = Decimal(str(value).strip())
        if n < min_val:
            return False, f'{field_name} cannot be less than {min_val}.'
        if max_val is not None and n > max_val:
            return False, f'{field_name} cannot be more than {max_val}.'
        return True, None
    except (InvalidOperation, ValueError):
        return False, f'Enter a valid number for {field_name}.'

def validate_crop_name(value):
    """Crop or crop name: 1–150 chars."""
    if not value or not value.strip():
        return False, 'Crop name is required.'
    v = value.strip()
    if len(v) > 150:
        return False, 'Crop name is too long.'
    return True, None

def validate_identifier(value, kind='identifier'):
    """Login identifier: non-empty."""
    if not value or not value.strip():
        return False, f'Please enter {kind}.'
    return True, None

def validate_required_string(value, field_name='Field', min_len=1, max_len=200):
    """Non-empty string within length limits."""
    if not value or not str(value).strip():
        return False, f'{field_name} is required.'
    v = str(value).strip()
    if len(v) < min_len:
        return False, f'{field_name} must be at least {min_len} character(s).'
    if len(v) > max_len:
        return False, f'{field_name} must be at most {max_len} characters.'
    return True, None
