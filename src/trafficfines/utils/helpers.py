import datetime
import re
from trafficfines.config import LOCALE

def parse_date(date_str):
    """Convert string date to datetime object using configured date format"""
    if not date_str:
        return None
    try:
        return datetime.datetime.strptime(date_str, LOCALE['date_format']).date()
    except ValueError:
        return None

def format_currency(amount):
    """Format amount as currency string using configured locale settings"""
    if amount is None:
        return f"{LOCALE['currency_symbol']}0,00"
    
    amount_float = float(amount)
    
    # Brazilian Real formatting: R$ 1.234,56
    if LOCALE['currency'] == 'BRL':
        # Format with thousands separator (.) and decimal comma (,)
        formatted = f"{amount_float:,.2f}"
        # Replace comma with placeholder, then dot with comma, then placeholder with dot
        formatted = formatted.replace(',', 'X').replace('.', ',').replace('X', '.')
        return f"{LOCALE['currency_symbol']} {formatted}"
    
    # Default USD formatting: $1,234.56
    return f"${amount_float:,.2f}"

def format_date(date_obj):
    """Format date object as string using configured date format"""
    if date_obj is None:
        return ""
    if isinstance(date_obj, datetime.date):
        return date_obj.strftime(LOCALE['date_format'])
    return str(date_obj)

def format_datetime(datetime_obj):
    """Format datetime object as string using configured datetime format"""
    if datetime_obj is None:
        return ""
    if isinstance(datetime_obj, (datetime.datetime, datetime.date)):
        return datetime_obj.strftime(LOCALE['datetime_format'])
    return str(datetime_obj)

def extract_with_regex(text, pattern, group=1):
    """Extract text using regex pattern"""
    match = re.search(pattern, text)
    if match:
        return match.group(group)
    return None
