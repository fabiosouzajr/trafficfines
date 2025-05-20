# gcal_calendar/integration.py
import os
import datetime
import pickle
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from config import SCOPES, CREDENTIALS_FILE, TOKEN_FILE
from db.models import FineModel

class CalendarIntegration:
    def __init__(self):
        self.calendar_service = self.setup_google_calendar()
        self.fine_model = FineModel()
        self._selected_calendar_id = 'primary'  # Default to primary calendar
        self._calendars = []  # Cache for calendar list
        self._initialize_calendars()
    
    def _initialize_calendars(self):
        """Initialize the calendar list and set default calendar"""
        try:
            if not self.calendar_service:
                print("Calendar service not available")
                self._calendars = []
                self._selected_calendar_id = 'primary'
                return

            print("Fetching available calendars...")
            self._calendars = self.list_calendars()
            
            if not self._calendars:
                print("No calendars found or no access to calendars")
                self._selected_calendar_id = 'primary'
                return

            print(f"Found {len(self._calendars)} calendars")
            # Try to find primary calendar first
            primary = next((cal for cal in self._calendars if cal.get('primary', False)), None)
            if primary:
                print(f"Using primary calendar: {primary['summary']}")
                self._selected_calendar_id = primary['id']
            else:
                # If no primary calendar found, use the first one
                print(f"Using first available calendar: {self._calendars[0]['summary']}")
                self._selected_calendar_id = self._calendars[0]['id']

            # Verify access to the selected calendar
            if not self.verify_calendar_access(self._selected_calendar_id):
                print("Selected calendar is not accessible, trying to find an accessible calendar...")
                for cal in self._calendars:
                    if self.verify_calendar_access(cal['id']):
                        print(f"Found accessible calendar: {cal['summary']}")
                        self._selected_calendar_id = cal['id']
                        return
                print("No accessible calendars found, using primary calendar")
                self._selected_calendar_id = 'primary'

        except Exception as e:
            print(f"Error initializing calendars: {str(e)}")
            self._calendars = []
            self._selected_calendar_id = 'primary'
    
    def setup_google_calendar(self):
        """Set up and authenticate with Google Calendar API"""
        try:
            print("Setting up Google Calendar service...")
            creds = None
            
            # First try to load existing token
            if os.path.exists(TOKEN_FILE):
                print("Loading existing token...")
                try:
                    with open(TOKEN_FILE, 'rb') as token:
                        creds = pickle.load(token)
                    print("Token loaded successfully")
                except Exception as e:
                    print(f"Error loading token: {str(e)}")
                    # If token is corrupted, remove it
                    try:
                        os.remove(TOKEN_FILE)
                        print("Removed corrupted token file")
                    except:
                        pass
            
            # If no valid token, check for credentials file
            if not creds or not creds.valid:
                if not os.path.exists(CREDENTIALS_FILE):
                    print(f"Error: Credentials file not found at {CREDENTIALS_FILE}")
                    return None
                    
                print("Starting new authentication flow...")
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        CREDENTIALS_FILE, SCOPES)
                    creds = flow.run_local_server(port=0)
                    
                    # Save the token for future use
                    print("Saving new token...")
                    with open(TOKEN_FILE, 'wb') as token:
                        pickle.dump(creds, token)
                    print("Token saved successfully")
                except Exception as e:
                    print(f"Error in authentication flow: {str(e)}")
                    return None
            
            print("Building calendar service...")
            service = build('calendar', 'v3', credentials=creds)
            
            # Test the service
            try:
                print("Testing calendar service...")
                service.calendarList().list().execute()
                print("Calendar service initialized successfully")
                return service
            except Exception as e:
                print(f"Error testing calendar service: {str(e)}")
                return None
                
        except Exception as e:
            print(f"Error setting up Google Calendar: {str(e)}")
            return None
    
    def verify_calendar_access(self, calendar_id):
        """Verify if we have access to a specific calendar"""
        try:
            if not self.calendar_service:
                return False
            # Try to get calendar details
            calendar = self.calendar_service.calendars().get(calendarId=calendar_id).execute()
            print(f"Successfully verified access to calendar: {calendar.get('summary', calendar_id)}")
            return True
        except Exception as e:
            print(f"No access to calendar {calendar_id}: {str(e)}")
            # Try to refresh the token if it's an authentication error
            if 'unauthorized' in str(e).lower() or 'invalid' in str(e).lower():
                print("Attempting to refresh authentication...")
                try:
                    # Remove the token file to force re-authentication
                    if os.path.exists(TOKEN_FILE):
                        os.remove(TOKEN_FILE)
                        print("Removed old token file")
                    # Re-initialize the calendar service
                    self.calendar_service = self.setup_google_calendar()
                    if self.calendar_service:
                        print("Successfully refreshed authentication")
                        return self.verify_calendar_access(calendar_id)
                except Exception as refresh_error:
                    print(f"Failed to refresh authentication: {str(refresh_error)}")
            return False

    def verify_calendar_events(self):
        """Verify existing calendar events and update database accordingly"""
        try:
            # Verify we have a valid calendar service
            if not self.calendar_service:
                print("Calendar service not properly initialized")
                return None

            # Verify we have access to the selected calendar
            if not self.verify_calendar_access(self._selected_calendar_id):
                print(f"No access to selected calendar: {self._selected_calendar_id}")
                # Try to reinitialize calendars
                print("Attempting to reinitialize calendars...")
                self._initialize_calendars()
                if not self.verify_calendar_access(self._selected_calendar_id):
                    print("Still unable to access calendar after reinitialization")
                    return None
                
            print(f"Verifying events in calendar: {self.get_calendar_name(self._selected_calendar_id)}")
            # Get all fines
            fines = self.fine_model.get_all_fines()
            results = {
                'payment_events': {'found': 0, 'missing': 0},
                'driver_id_events': {'found': 0, 'missing': 0}
            }
            
            for fine in fines:
                fine_id = fine['id']
                fine_number = fine['fine_number']
                due_date = fine['notification_date']
                driver_id_due_date = fine['driver_id_due_date']
                
                # Check payment event
                if due_date:
                    try:
                        events_result = self.calendar_service.events().list(
                            calendarId=self._selected_calendar_id,
                            timeMin=datetime.datetime.combine(due_date, datetime.time.min).isoformat() + 'Z',
                            timeMax=datetime.datetime.combine(due_date, datetime.time.max).isoformat() + 'Z',
                            q=fine_number
                        ).execute()
                        
                        events = events_result.get('items', [])
                        has_payment_event = any(
                            'Traffic Fine Payment Due' in event.get('summary', '')
                            for event in events
                        )
                        
                        if has_payment_event and not fine['payment_event_created']:
                            self.fine_model.mark_payment_event_created(fine_id)
                            results['payment_events']['found'] += 1
                        elif not has_payment_event and fine['payment_event_created']:
                            self.fine_model.mark_payment_event_not_created(fine_id)
                            results['payment_events']['missing'] += 1
                    except Exception as e:
                        print(f"Error checking payment event for fine {fine_number}: {e}")
                        continue
                
                # Check driver ID event
                if driver_id_due_date:
                    try:
                        events_result = self.calendar_service.events().list(
                            calendarId=self._selected_calendar_id,
                            timeMin=datetime.datetime.combine(driver_id_due_date, datetime.time.min).isoformat() + 'Z',
                            timeMax=datetime.datetime.combine(driver_id_due_date, datetime.time.max).isoformat() + 'Z',
                            q=fine_number
                        ).execute()
                        
                        events = events_result.get('items', [])
                        has_driver_id_event = any(
                            'Driver ID Submission Due' in event.get('summary', '')
                            for event in events
                        )
                        
                        if has_driver_id_event and not fine['driver_id_event_created']:
                            self.fine_model.mark_driver_id_event_created(fine_id)
                            results['driver_id_events']['found'] += 1
                        elif not has_driver_id_event and fine['driver_id_event_created']:
                            self.fine_model.mark_driver_id_event_not_created(fine_id)
                            results['driver_id_events']['missing'] += 1
                    except Exception as e:
                        print(f"Error checking driver ID event for fine {fine_number}: {e}")
                        continue
            
            return results
            
        except Exception as e:
            print(f"Error verifying calendar events: {e}")
            return None
    
    def create_payment_event(self, fine_id, fine_number, due_date, amount):
        """Create Google Calendar event for payment reminder"""
        event = {
            'summary': f'Traffic Fine Payment Due: {fine_number}',
            'description': f'Pay traffic fine #{fine_number} - Amount: ${amount}',
            'start': {
                'date': due_date.isoformat(),
                'timeZone': 'America/Los_Angeles',
            },
            'end': {
                'date': due_date.isoformat(),
                'timeZone': 'America/Los_Angeles',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 24 * 60},
                ],
            },
        }
        
        # Check for duplicates
        events_result = self.calendar_service.events().list(
            calendarId=self._selected_calendar_id,
            timeMin=datetime.datetime.combine(due_date, datetime.time.min).isoformat() + 'Z',
            timeMax=datetime.datetime.combine(due_date, datetime.time.max).isoformat() + 'Z',
            q=fine_number
        ).execute()
        
        if not events_result.get('items', []):
            event = self.calendar_service.events().insert(
                calendarId=self._selected_calendar_id, body=event).execute()
            
            # Update the database
            self.fine_model.mark_payment_event_created(fine_id)
            return True
        
        return False
    
    def create_driver_id_event(self, fine_id, fine_number, driver_id_due_date):
        """Create Google Calendar event for driver ID submission reminder"""
        if not driver_id_due_date:
            return False
            
        event = {
            'summary': f'Driver ID Submission Due: {fine_number}',
            'description': f'Submit driver identification for fine #{fine_number}',
            'start': {
                'date': driver_id_due_date.isoformat(),
                'timeZone': 'America/Los_Angeles',
            },
            'end': {
                'date': driver_id_due_date.isoformat(),
                'timeZone': 'America/Los_Angeles',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 24 * 60},
                ],
            },
        }
        
        # Check for duplicates
        events_result = self.calendar_service.events().list(
            calendarId=self._selected_calendar_id,
            timeMin=datetime.datetime.combine(driver_id_due_date, datetime.time.min).isoformat() + 'Z',
            timeMax=datetime.datetime.combine(driver_id_due_date, datetime.time.max).isoformat() + 'Z',
            q=fine_number
        ).execute()
        
        if not events_result.get('items', []):
            event = self.calendar_service.events().insert(
                calendarId=self._selected_calendar_id, body=event).execute()
            
            # Update the database
            self.fine_model.mark_driver_id_event_created(fine_id)
            return True
        
        return False
    
    def create_calendar_events(self):
        """Create Google Calendar events for all pending fines"""
        results = {
            'payment_events': {'created': 0, 'skipped': 0},
            'driver_id_events': {'created': 0, 'skipped': 0}
        }
        
        # Process payment events
        payment_fines = self.fine_model.get_fines_without_payment_events()
        for fine_id, fine_number, due_date, amount in payment_fines:
            if self.create_payment_event(fine_id, fine_number, due_date, amount):
                results['payment_events']['created'] += 1
            else:
                results['payment_events']['skipped'] += 1
        
        # Process driver ID events
        driver_id_fines = self.fine_model.get_fines_without_driver_id_events()
        for fine_id, fine_number, driver_id_due_date in driver_id_fines:
            if self.create_driver_id_event(fine_id, fine_number, driver_id_due_date):
                results['driver_id_events']['created'] += 1
            else:
                results['driver_id_events']['skipped'] += 1
        
        return results

    def get_account_name(self):
        """Return the email address of the authenticated Google account."""
        try:
            user_info = self.calendar_service.calendarList().get(calendarId='primary').execute()
            return user_info.get('summary', 'Unknown')
        except Exception as e:
            print(f"Error getting account name: {e}")
            return 'Unknown'

    def list_calendars(self):
        """Return a list of all calendars for the user."""
        try:
            calendars_result = self.calendar_service.calendarList().list().execute()
            return calendars_result.get('items', [])
        except Exception as e:
            print(f"Error listing calendars: {e}")
            return []

    def get_selected_calendar(self):
        """Return the currently selected calendar ID."""
        return self._selected_calendar_id

    def set_selected_calendar(self, calendar_id):
        """Set the currently selected calendar ID."""
        try:
            # First verify we have access to the calendar
            if not self.verify_calendar_access(calendar_id):
                print(f"Warning: No access to calendar ID {calendar_id}")
                # Try to find an accessible calendar
                for cal in self._calendars:
                    if self.verify_calendar_access(cal['id']):
                        self._selected_calendar_id = cal['id']
                        print(f"Switched to accessible calendar: {cal['summary']}")
                        return
                # If no accessible calendar found, use primary
                self._selected_calendar_id = 'primary'
                print("No accessible calendars found, using primary calendar")
                return

            # If we have access, set the calendar
            self._selected_calendar_id = calendar_id
            print(f"Successfully set calendar to: {self.get_calendar_name(calendar_id)}")
        except Exception as e:
            print(f"Error setting calendar: {e}")
            self._selected_calendar_id = 'primary'

    def get_calendar_name(self, calendar_id):
        """Get the name of a calendar by its ID"""
        try:
            calendar = next((cal for cal in self._calendars if cal['id'] == calendar_id), None)
            return calendar['summary'] if calendar else 'Primary Calendar'
        except Exception as e:
            print(f"Error getting calendar name: {e}")
            return 'Primary Calendar'

    def create_calendar(self, summary):
        """Create a new calendar with the given summary/name."""
        try:
            calendar = {
                'summary': summary,
                'timeZone': 'America/Los_Angeles',
            }
            created_calendar = self.calendar_service.calendars().insert(body=calendar).execute()
            return created_calendar
        except Exception as e:
            print(f"Error creating calendar: {e}")
            return None