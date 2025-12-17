# config.py
"""
Configuration management with environment variable support and validation.

Supports:
- Environment variable overrides
- JSON configuration file loading
- Configuration validation at startup
"""
import os
import json
from pathlib import Path
from typing import Dict, Optional, List, Tuple, Any


class ConfigurationError(Exception):
    """Raised when configuration validation fails."""
    pass


class Config:
    """
    Configuration class that loads settings from environment variables
    and optional JSON config file.
    """
    
    def __init__(self):
        """Initialize configuration with defaults and load from environment/config file."""
        # Get project root directory (parent of src/)
        self.PROJECT_ROOT = Path(__file__).parent.parent.parent
        
        # Load configuration
        self._load_defaults()
        self._load_from_file()
        self._load_from_environment()
        
        # Convert paths to strings for backward compatibility
        self._convert_paths_to_strings()
    
    def _load_defaults(self):
        """Load default configuration values."""
        # Database configuration
        self.DATABASE_PATH = self.PROJECT_ROOT / 'traffic_fines.db'
        
        # Google Calendar API configuration
        self.SCOPES = ['https://www.googleapis.com/auth/calendar']
        self.CREDENTIALS_FILE = self.PROJECT_ROOT / 'credentials.json'
        self.TOKEN_FILE = self.PROJECT_ROOT / 'token.pickle'
        
        # PDF scanning configuration
        self.DEFAULT_PDF_FOLDER = self.PROJECT_ROOT / 'multas'
        
        # Logging configuration
        self.LOG_FILE = self.PROJECT_ROOT / 'app.log'
        
        # Localization configuration
        self.LOCALE = {
            'language': 'pt_BR',
            'currency': 'BRL',
            'currency_symbol': 'R$',
            'timezone': 'America/Sao_Paulo',
            'date_format': '%d/%m/%Y',
            'datetime_format': '%d/%m/%Y %H:%M:%S'
        }
    
    def _load_from_file(self):
        """Load configuration from JSON file if it exists."""
        config_file_path = os.getenv('TRAFFICFINES_CONFIG_FILE')
        if not config_file_path:
            # Check for default config file in project root
            default_config = self.PROJECT_ROOT / 'config.json'
            if default_config.exists():
                config_file_path = str(default_config)
        
        if config_file_path and os.path.exists(config_file_path):
            try:
                with open(config_file_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # Update configuration from file
                if 'database_path' in config_data:
                    self.DATABASE_PATH = Path(config_data['database_path'])
                
                if 'credentials_file' in config_data:
                    self.CREDENTIALS_FILE = Path(config_data['credentials_file'])
                
                if 'token_file' in config_data:
                    self.TOKEN_FILE = Path(config_data['token_file'])
                
                if 'default_pdf_folder' in config_data:
                    self.DEFAULT_PDF_FOLDER = Path(config_data['default_pdf_folder'])
                
                if 'log_file' in config_data:
                    self.LOG_FILE = Path(config_data['log_file'])
                
                if 'locale' in config_data:
                    self.LOCALE.update(config_data['locale'])
                
                if 'scopes' in config_data:
                    self.SCOPES = config_data['scopes']
                
            except json.JSONDecodeError as e:
                raise ConfigurationError(f"Invalid JSON in config file '{config_file_path}': {e}")
            except Exception as e:
                raise ConfigurationError(f"Error loading config file '{config_file_path}': {e}")
    
    def _load_from_environment(self):
        """Load configuration from environment variables."""
        # Database configuration
        if os.getenv('TRAFFICFINES_DB_PATH'):
            self.DATABASE_PATH = Path(os.getenv('TRAFFICFINES_DB_PATH'))
        
        # Google Calendar API configuration
        if os.getenv('TRAFFICFINES_CREDENTIALS_FILE'):
            self.CREDENTIALS_FILE = Path(os.getenv('TRAFFICFINES_CREDENTIALS_FILE'))
        
        if os.getenv('TRAFFICFINES_TOKEN_FILE'):
            self.TOKEN_FILE = Path(os.getenv('TRAFFICFINES_TOKEN_FILE'))
        
        # PDF scanning configuration
        if os.getenv('TRAFFICFINES_PDF_FOLDER'):
            self.DEFAULT_PDF_FOLDER = Path(os.getenv('TRAFFICFINES_PDF_FOLDER'))
        
        # Logging configuration
        if os.getenv('TRAFFICFINES_LOG_FILE'):
            self.LOG_FILE = Path(os.getenv('TRAFFICFINES_LOG_FILE'))
        
        # Localization - timezone
        if os.getenv('TRAFFICFINES_TIMEZONE'):
            self.LOCALE['timezone'] = os.getenv('TRAFFICFINES_TIMEZONE')
        
        # Localization - language
        if os.getenv('TRAFFICFINES_LANGUAGE'):
            self.LOCALE['language'] = os.getenv('TRAFFICFINES_LANGUAGE')
        
        # Localization - currency
        if os.getenv('TRAFFICFINES_CURRENCY'):
            self.LOCALE['currency'] = os.getenv('TRAFFICFINES_CURRENCY')
        
        if os.getenv('TRAFFICFINES_CURRENCY_SYMBOL'):
            self.LOCALE['currency_symbol'] = os.getenv('TRAFFICFINES_CURRENCY_SYMBOL')
        
        # Localization - date format
        if os.getenv('TRAFFICFINES_DATE_FORMAT'):
            self.LOCALE['date_format'] = os.getenv('TRAFFICFINES_DATE_FORMAT')
        
        if os.getenv('TRAFFICFINES_DATETIME_FORMAT'):
            self.LOCALE['datetime_format'] = os.getenv('TRAFFICFINES_DATETIME_FORMAT')
    
    def _convert_paths_to_strings(self):
        """Convert Path objects to strings for backward compatibility."""
        self.DATABASE_PATH = str(self.DATABASE_PATH)
        self.CREDENTIALS_FILE = str(self.CREDENTIALS_FILE)
        self.TOKEN_FILE = str(self.TOKEN_FILE)
        self.DEFAULT_PDF_FOLDER = str(self.DEFAULT_PDF_FOLDER)
        self.LOG_FILE = str(self.LOG_FILE)
    
    def validate(self) -> Tuple[bool, List[str], List[str]]:
        """
        Validate configuration settings.
        
        Returns:
            Tuple of (is_valid, list_of_errors, list_of_warnings)
        """
        errors = []
        warnings = []
        
        # Validate database path - parent directory must be writable
        db_path = Path(str(self.DATABASE_PATH))
        db_parent = db_path.parent
        if not db_parent.exists():
            try:
                db_parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create database directory '{db_parent}': {e}")
        elif not os.access(db_parent, os.W_OK):
            errors.append(f"Database directory '{db_parent}' is not writable")
        
        # Validate log file path - parent directory must be writable
        log_path = Path(str(self.LOG_FILE))
        log_parent = log_path.parent
        if not log_parent.exists():
            try:
                log_parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create log directory '{log_parent}': {e}")
        elif not os.access(log_parent, os.W_OK):
            errors.append(f"Log directory '{log_parent}' is not writable")
        
        # Validate credentials file - should exist if Google Calendar is to be used
        # (Not an error, just a warning - app can work without it)
        creds_path = Path(str(self.CREDENTIALS_FILE))
        if not creds_path.exists():
            warnings.append(f"Google Calendar credentials file '{self.CREDENTIALS_FILE}' not found. Calendar features will be unavailable.")
        
        # Validate PDF folder - should exist and be readable
        pdf_folder = Path(str(self.DEFAULT_PDF_FOLDER))
        if not pdf_folder.exists():
            warnings.append(f"Default PDF folder '{self.DEFAULT_PDF_FOLDER}' does not exist. It will be used when creating the folder.")
        elif not os.access(pdf_folder, os.R_OK):
            errors.append(f"Default PDF folder '{self.DEFAULT_PDF_FOLDER}' is not readable")
        
        # Validate locale settings
        if not self.LOCALE.get('timezone'):
            errors.append("Locale timezone is not set")
        
        if not self.LOCALE.get('currency'):
            errors.append("Locale currency is not set")
        
        if not self.LOCALE.get('currency_symbol'):
            errors.append("Locale currency_symbol is not set")
        
        if not self.LOCALE.get('date_format'):
            errors.append("Locale date_format is not set")
        
        if not self.LOCALE.get('datetime_format'):
            errors.append("Locale datetime_format is not set")
        
        # Validate date format strings
        try:
            from datetime import datetime
            test_date = datetime(2024, 12, 25, 10, 30, 0)
            test_date.strftime(self.LOCALE['date_format'])
            test_date.strftime(self.LOCALE['datetime_format'])
        except ValueError as e:
            errors.append(f"Invalid date format string in locale configuration: {e}")
        
        # Validate SCOPES
        if not isinstance(self.SCOPES, list):
            errors.append("SCOPES must be a list")
        elif not self.SCOPES:
            errors.append("SCOPES cannot be empty")
        
        return len(errors) == 0, errors, warnings
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration values."""
        return {
            'database_path': self.DATABASE_PATH,
            'credentials_file': self.CREDENTIALS_FILE,
            'token_file': self.TOKEN_FILE,
            'default_pdf_folder': self.DEFAULT_PDF_FOLDER,
            'log_file': self.LOG_FILE,
            'locale': self.LOCALE.copy(),
            'scopes': self.SCOPES.copy()
        }


# Create global config instance
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


def validate_config() -> None:
    """
    Validate configuration and raise ConfigurationError if invalid.
    
    Raises:
        ConfigurationError: If configuration is invalid
    """
    config = get_config()
    is_valid, errors, warnings = config.validate()
    
    if warnings:
        from trafficfines.utils.logger import get_logger
        logger = get_logger(__name__)
        for warning in warnings:
            logger.warning(f"Configuration warning: {warning}")
    
    if not is_valid:
        error_message = "Configuration validation failed:\n" + "\n".join(f"  - {error}" for error in errors)
        raise ConfigurationError(error_message)


# Initialize config instance
_config = get_config()

# Export configuration values as module-level variables for backward compatibility
DATABASE_PATH = _config.DATABASE_PATH
CREDENTIALS_FILE = _config.CREDENTIALS_FILE
TOKEN_FILE = _config.TOKEN_FILE
DEFAULT_PDF_FOLDER = _config.DEFAULT_PDF_FOLDER
LOG_FILE = _config.LOG_FILE
LOCALE = _config.LOCALE
SCOPES = _config.SCOPES
