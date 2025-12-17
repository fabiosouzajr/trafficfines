# Configuration Guide

The Traffic Fine Manager application supports flexible configuration through environment variables and optional configuration files.

## Configuration Sources (Priority Order)

Configuration is loaded in the following order (later sources override earlier ones):

1. **Default values** (hardcoded in `config.py`)
2. **JSON configuration file** (`config.json` in project root, or path specified by `TRAFFICFINES_CONFIG_FILE`)
3. **Environment variables** (highest priority)

## Environment Variables

You can override any configuration setting using environment variables:

### Database Configuration
- `TRAFFICFINES_DB_PATH` - Path to the SQLite database file

### Google Calendar Configuration
- `TRAFFICFINES_CREDENTIALS_FILE` - Path to Google Calendar credentials JSON file
- `TRAFFICFINES_TOKEN_FILE` - Path to store OAuth token

### PDF Folder Configuration
- `TRAFFICFINES_PDF_FOLDER` - Default folder for scanning PDF files

### Logging Configuration
- `TRAFFICFINES_LOG_FILE` - Path to the log file

### Localization Configuration
- `TRAFFICFINES_TIMEZONE` - Timezone (e.g., 'America/Sao_Paulo')
- `TRAFFICFINES_LANGUAGE` - Language code (e.g., 'pt_BR')
- `TRAFFICFINES_CURRENCY` - Currency code (e.g., 'BRL')
- `TRAFFICFINES_CURRENCY_SYMBOL` - Currency symbol (e.g., 'R$')
- `TRAFFICFINES_DATE_FORMAT` - Date format string (e.g., '%d/%m/%Y')
- `TRAFFICFINES_DATETIME_FORMAT` - DateTime format string (e.g., '%d/%m/%Y %H:%M:%S')

### Config File Location
- `TRAFFICFINES_CONFIG_FILE` - Path to JSON configuration file (overrides default `config.json`)

## JSON Configuration File

Create a `config.json` file in the project root (or specify path via `TRAFFICFINES_CONFIG_FILE`) with the following structure:

```json
{
  "database_path": "traffic_fines.db",
  "credentials_file": "credentials.json",
  "token_file": "token.pickle",
  "default_pdf_folder": "~/Documents/multas",
  "log_file": "app.log",
  "locale": {
    "language": "pt_BR",
    "currency": "BRL",
    "currency_symbol": "R$",
    "timezone": "America/Sao_Paulo",
    "date_format": "%d/%m/%Y",
    "datetime_format": "%d/%m/%Y %H:%M:%S"
  },
  "scopes": [
    "https://www.googleapis.com/auth/calendar"
  ]
}
```

**Note**: Paths in the JSON file are relative to the project root, or you can use absolute paths. The `~` symbol is expanded to the user's home directory.

## Configuration Validation

The application validates configuration at startup. If validation fails, the application will:

1. Log all errors and warnings
2. Display errors to stderr
3. Exit with error code 1

### Validation Checks

- **Database path**: Parent directory exists and is writable
- **Log file path**: Parent directory exists and is writable
- **PDF folder**: Exists and is readable (warning if missing, as it may be created later)
- **Credentials file**: Exists (warning if missing, as calendar features won't work)
- **Locale settings**: All required locale fields are set and valid
- **Date formats**: Date format strings are valid
- **Scopes**: Google Calendar scopes are properly configured

## Examples

### Using Environment Variables (Windows)
```cmd
set TRAFFICFINES_DB_PATH=C:\Data\traffic_fines.db
set TRAFFICFINES_TIMEZONE=America/New_York
python run.py
```

### Using Environment Variables (Linux/Mac)
```bash
export TRAFFICFINES_DB_PATH=/var/data/traffic_fines.db
export TRAFFICFINES_TIMEZONE=America/New_York
python run.py
```

### Using JSON Configuration File
1. Copy `config.json.example` to `config.json` in the project root
2. Edit `config.json` with your settings
3. Run the application normally: `python run.py`

## Programmatic Access

You can also access configuration programmatically:

```python
from trafficfines.config import get_config, validate_config

# Get configuration instance
config = get_config()

# Validate configuration
try:
    validate_config()
    print("Configuration is valid")
except ConfigurationError as e:
    print(f"Configuration error: {e}")

# Access configuration values
print(config.DATABASE_PATH)
print(config.LOCALE['timezone'])
```

## Backward Compatibility

All existing imports continue to work:

```python
from trafficfines.config import DATABASE_PATH, LOCALE, SCOPES
```

These module-level variables are automatically populated from the Config instance.

