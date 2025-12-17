# Code Refactoring - src/ Layout

## Summary

The codebase has been refactored to follow Python best practices by organizing all modules inside a `src/` directory structure.

## New Structure

```
trafficfines/
├── src/
│   └── trafficfines/          # Main package
│       ├── __init__.py
│       ├── main.py            # Application entry point
│       ├── config.py          # Configuration settings
│       ├── db/                # Database layer
│       │   ├── __init__.py
│       │   ├── database.py
│       │   └── models.py
│       ├── gui/               # GUI components
│       │   ├── __init__.py
│       │   ├── app.py
│       │   ├── import_tab.py
│       │   ├── fines_tab.py
│       │   └── calendar_tab.py
│       ├── pdf/               # PDF processing
│       │   ├── __init__.py
│       │   ├── parser.py
│       │   ├── validator.py
│       │   ├── field_config.py
│       │   ├── parsing_strategies.py
│       │   ├── field_mappings.json
│       │   └── read_pdf.py
│       ├── utils/             # Utility functions
│       │   ├── __init__.py
│       │   ├── logger.py
│       │   ├── error_messages.py
│       │   └── helpers.py
│       └── gcal_integration/  # Google Calendar integration
│           ├── __init__.py
│           └── integration.py
├── docs/                      # Documentation
├── multas/                    # Sample PDFs (not in package)
├── setup.py                   # Package installation script
├── run.py                     # Entry point script
├── requirements.txt
├── README
└── LICENSE
```

## Changes Made

### 1. Package Structure
- All Python modules moved to `src/trafficfines/`
- Created proper `__init__.py` files
- Package name is now `trafficfines`

### 2. Import Statements
All imports updated to use absolute imports with package prefix:
- `from gui.app import ...` → `from trafficfines.gui.app import ...`
- `from db.models import ...` → `from trafficfines.db.models import ...`
- `from utils.logger import ...` → `from trafficfines.utils.logger import ...`
- etc.

### 3. Configuration
- `config.py` updated to use `Path` objects for better path handling
- All paths are relative to project root (calculated from package location)
- Database, log files, and credentials are stored in project root

### 4. Entry Points
- **`run.py`**: Simple script to run the app from project root (adds src to path)
- **`setup.py`**: Proper package installation with entry point `trafficfines`
- **`src/trafficfines/main.py`**: Main application entry point

### 5. Error Handling
- Calendar integration now gracefully handles authentication failures
- App can start even if Google Calendar authentication fails
- Better error messages for users

## Running the Application

### Option 1: Using run.py (Development)
```bash
python run.py
```

### Option 2: After Installation
```bash
pip install -e .
trafficfines
```

### Option 3: Direct Python
```bash
python -m trafficfines.main
```

## Installation

To install the package in development mode:
```bash
pip install -e .
```

This installs the package in editable mode, so changes to source code are immediately available.

## Benefits

1. **Better Organization**: Clear separation between source code and other files
2. **Standard Structure**: Follows Python packaging best practices
3. **Easier Distribution**: Can be packaged and distributed as a proper Python package
4. **Better Imports**: Absolute imports prevent import issues
5. **IDE Support**: Better autocomplete and navigation in IDEs
6. **Testing**: Easier to set up tests in a separate `tests/` directory

## Migration Notes

- Old import statements in the root directory no longer work
- All imports must use the `trafficfines.` prefix
- Configuration files (database, logs, credentials) remain in project root
- The old `main.py` in root is replaced by `run.py` and `src/trafficfines/main.py`

## Next Steps

Consider:
1. Moving tests to a `tests/` directory
2. Adding `pyproject.toml` for modern Python packaging
3. Creating a proper `README.md` with installation instructions
4. Adding type stubs for better IDE support

