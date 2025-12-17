# Traffic Fine Manager - Application Documentation

## Overview

The Traffic Fine Manager is a desktop application built with Python and Tkinter that helps users manage traffic fines by:
- Parsing traffic fine information from PDF documents
- Storing fine data in a local SQLite database
- Creating Google Calendar events for payment deadlines and driver identification submissions
- Providing a user-friendly GUI for viewing, filtering, and managing fines

## Architecture

### Technology Stack
- **GUI Framework**: Tkinter (Python's built-in GUI library)
- **Database**: SQLite3
- **PDF Processing**: PyMuPDF (fitz)
- **Calendar Integration**: Google Calendar API (via google-api-python-client)
- **Authentication**: OAuth 2.0 for Google Calendar

### Project Structure

```
trafficfines/
├── main.py                 # Application entry point
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── gui/                   # GUI components
│   ├── app.py            # Main application window
│   ├── import_tab.py     # PDF import functionality
│   ├── fines_tab.py      # Fines viewing and management
│   └── calendar_tab.py   # Calendar integration UI
├── db/                    # Database layer
│   ├── database.py       # Database connection and schema
│   └── models.py         # Data models and CRUD operations
├── pdf/                   # PDF processing
│   ├── parser.py         # PDF parsing logic
│   └── read_pdf.py       # PDF reading utilities
├── gcal_integration/      # Google Calendar integration
│   └── integration.py    # Calendar API wrapper
├── utils/                 # Utility functions
│   └── helpers.py        # Helper functions (date parsing, currency formatting)
└── docs/                  # Documentation
```

## Core Components

### 1. Main Application (`main.py`)
- Initializes logging to both file (`app.log`) and console
- Creates the Tkinter root window
- Instantiates and runs the `TrafficFineApp`

### 2. GUI Application (`gui/app.py`)
The main application window contains:
- **Tabbed Interface**: Three tabs for different functionalities
- **Menu Bar**: File and Help menus
- **Tab Communication**: Callbacks between tabs for data synchronization

#### Tabs:
1. **Import Tab** (`gui/import_tab.py`): Handles PDF import workflow
2. **Fines Tab** (`gui/fines_tab.py`): Displays and manages stored fines
3. **Calendar Tab** (`gui/calendar_tab.py`): Manages Google Calendar integration

### 3. Database Layer (`db/`)

#### Database Schema (`db/database.py`)
The `fines` table stores:
- **Identification**: `fine_number` (unique), `id` (primary key)
- **Dates**: `notification_date`, `defense_due_date`, `driver_id_due_date`, `violation_date`
- **Vehicle Info**: `license_plate`, `vehicle_model`, `owner_name`, `owner_document`
- **Violation Details**: `violation_location`, `violation_time`, `violation_code`, `description`
- **Speed Data**: `measured_speed`, `considered_speed`, `speed_limit`
- **Financial**: `amount`
- **Metadata**: `pdf_path`, `payment_event_created`, `driver_id_event_created`

#### Data Model (`db/models.py`)
The `FineModel` class provides:
- `save_fine()`: Insert or update fine records (uses `INSERT OR REPLACE`)
- `get_all_fines()`: Retrieve all fines ordered by violation date
- `get_fines_without_payment_events()`: Get fines needing payment reminders
- `get_fines_without_driver_id_events()`: Get fines needing driver ID reminders
- `mark_payment_event_created()`: Mark payment event as created
- `mark_driver_id_event_created()`: Mark driver ID event as created
- `get_fine_by_number()`: Retrieve a specific fine by number

### 4. PDF Processing (`pdf/parser.py`)

#### PDFParser Class
The parser extracts data from Brazilian traffic fine PDFs using:
- **Field Mapping**: Maps Portuguese field names to canonical keys
- **Text Extraction**: Uses PyMuPDF to extract text from all pages
- **Line-by-Line Parsing**: Identifies field headers and extracts following values
- **Data Transformation**: 
  - Converts date strings (dd/mm/yyyy) to date objects
  - Parses currency values (R$ format) to float
  - Handles missing or invalid data gracefully

#### Supported Fields
- Auto de Infração (Fine Number)
- Notification and due dates
- License plate and vehicle information
- Violation details (location, date, time, code, description)
- Speed-related data (measured, considered, limit)
- Owner information (name, CPF/CNPJ)
- Fine amount

### 5. Google Calendar Integration (`gcal_integration/integration.py`)

#### CalendarIntegration Class
- **Authentication**: OAuth 2.0 flow with token caching
- **Event Creation**: Creates two types of events:
  1. **Payment Events**: Reminders for payment deadlines (`defense_due_date`)
  2. **Driver ID Events**: Reminders for driver identification deadlines (`driver_id_due_date`)
- **Duplicate Prevention**: Checks for existing events before creating new ones
- **Database Sync**: Updates database flags when events are created

#### Event Details
- **Summary**: Includes fine number
- **Description**: Contains fine details and amount
- **Reminders**: Email and popup reminders 24 hours before deadline
- **Time Zone**: Currently hardcoded to 'America/Los_Angeles' (should be configurable)

### 6. Utility Functions (`utils/helpers.py`)
- `parse_date()`: Converts dd/mm/yyyy strings to date objects
- `format_currency()`: Formats numeric amounts as currency strings ($X.XX)
- `extract_with_regex()`: Generic regex extraction helper

## User Workflow

### Importing Fines
1. User selects a folder containing PDF files
2. Clicks "Verificar Pasta" (Verify Folder) to scan for PDFs
3. Application parses each PDF and validates required fields:
   - `fine_number`
   - `license_plate`
   - `amount`
4. Compatible files are displayed in a table with extracted information
5. User reviews the list and clicks "Processar Arquivos" (Process Files)
6. Valid fines are saved to the database
7. Fines tab is automatically refreshed

### Viewing Fines
1. Fines are displayed in a sortable table
2. **Filtering**: By status (All, Pending Payment, Pending Driver ID, Complete)
3. **Searching**: By fine number, date, or license plate
4. **Details**: Double-click or "View Details" button shows full fine information

### Creating Calendar Events
1. User navigates to Calendar Events tab
2. Clicks "Create Calendar Events"
3. Application:
   - Authenticates with Google Calendar (if needed)
   - Finds fines without payment events
   - Finds fines without driver ID events
   - Creates events for each pending fine
   - Updates database flags
4. Status display shows number of events created/skipped
5. Fines tab is refreshed to show updated status

## Configuration

### Configuration File (`config.py`)
- **Database Path**: `traffic_fines.db` (SQLite database file)
- **Google Calendar**:
  - `SCOPES`: Calendar API permissions
  - `CREDENTIALS_FILE`: OAuth credentials JSON file
  - `TOKEN_FILE`: Cached authentication token
- **PDF Folder**: Default folder path for PDF scanning

## Data Flow

```
PDF Files → PDFParser → Fine Data Dictionary → FineModel → SQLite Database
                                                              ↓
                                                    CalendarIntegration
                                                              ↓
                                                    Google Calendar API
```

## Error Handling

- **PDF Parsing**: Returns `None` if parsing fails, logged with exception details
- **Database Operations**: Returns `False` on failure, errors logged
- **Calendar API**: Exceptions caught and displayed to user via message boxes
- **GUI Operations**: User-friendly error messages via `messagebox`

## Logging

- **Log File**: `app.log` in application root
- **Log Level**: INFO (configurable in `main.py`)
- **Log Format**: Timestamp, level, message
- **Handlers**: Both file and console output

## Dependencies

- `PyMuPDF`: PDF text extraction
- `requests`: HTTP requests (for Google API)
- `google-api-python-client`: Google Calendar API client
- `google-auth-httplib2`: HTTP transport for authentication
- `google-auth-oauthlib`: OAuth 2.0 flow

## Known Limitations

1. **Hardcoded Timezone**: Calendar events use 'America/Los_Angeles' timezone
2. **Currency Format**: Currently displays as USD ($) instead of Brazilian Real (R$)
3. **PDF Format Dependency**: Parser assumes specific PDF structure and Portuguese field names
4. **No Payment Tracking**: Application doesn't track actual payment status, only calendar event creation
5. **Single Database**: No support for multiple users or database selection
6. **No Export Functionality**: Cannot export fine data to other formats
7. **Limited Validation**: Only validates three required fields during import

## Future Enhancements (from TODO)

- Function to verify if payment information has been submitted for each fine
- Table with payment information
- Function to handle payment PDF files

