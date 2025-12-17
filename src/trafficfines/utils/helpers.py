import datetime
import re

import datetime
import re

def parse_date(date_str):
    """Convert string date to datetime object, expects dd/mm/yyyy"""
    if not date_str:
        return None
    try:
        return datetime.datetime.strptime(date_str, '%d/%m/%Y').date()
    except ValueError:
        return None

def format_currency(amount):
    """Format amount as currency string"""
    if amount is None:
        return "$0.00"
    return f"${float(amount):.2f}"

def extract_with_regex(text, pattern, group=1):
    """Extract text using regex pattern"""
    match = re.search(pattern, text)
    if match:
        return match.group(group)
    return None
