# gcal_integration/integration.py
import os
import datetime
import pickle
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError
from trafficfines.config import SCOPES, CREDENTIALS_FILE, TOKEN_FILE
from trafficfines.db.models import FineModel
from trafficfines.utils.logger import get_logger
from trafficfines.utils.error_messages import ErrorMessageMapper

logger = get_logger(__name__)

class CalendarIntegration:
    def __init__(self):
        self.calendar_service = None
        self.fine_model = FineModel()
        # Try to set up calendar service, but don't fail if it doesn't work
        try:
            self.calendar_service = self.setup_google_calendar()
        except Exception as e:
            logger.warning(f"Could not initialize Google Calendar service: {e}")
            logger.info("Calendar features will be disabled. You can re-authenticate later.")
            # Don't raise - allow app to start without calendar
    
    def setup_google_calendar(self, force_reauth: bool = False):
        """
        Set up and authenticate with Google Calendar API.
        
        Args:
            force_reauth: If True, force a new OAuth flow even if valid credentials exist
        
        Returns:
            Google Calendar API service object
        """
        try:
            creds = None
            
            # If forcing re-auth, delete existing token file
            if force_reauth and os.path.exists(TOKEN_FILE):
                logger.info("Forcing re-authentication - removing existing token")
                os.remove(TOKEN_FILE)
            
            if os.path.exists(TOKEN_FILE) and not force_reauth:
                logger.debug(f"Loading existing token from {TOKEN_FILE}")
                with open(TOKEN_FILE, 'rb') as token:
                    creds = pickle.load(token)
                    
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token and not force_reauth:
                    logger.info("Refreshing expired credentials")
                    try:
                        creds.refresh(Request())
                    except Exception as e:
                        logger.warning(f"Failed to refresh credentials: {e}. Starting new OAuth flow.")
                        creds = None
                
                if not creds or not creds.valid or force_reauth:
                    logger.info("Starting OAuth flow for new credentials")
                    if not os.path.exists(CREDENTIALS_FILE):
                        raise FileNotFoundError(f"Credentials file not found: {CREDENTIALS_FILE}")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        CREDENTIALS_FILE, SCOPES)
                    creds = flow.run_local_server(port=0)
                
                logger.info("Saving credentials to token file")
                with open(TOKEN_FILE, 'wb') as token:
                    pickle.dump(creds, token)
                    
            logger.info("Successfully set up Google Calendar API")
            return build('calendar', 'v3', credentials=creds)
        except FileNotFoundError as e:
            logger.error(ErrorMessageMapper.get_log_message(e, {'file': CREDENTIALS_FILE or TOKEN_FILE}), exc_info=True)
            raise
        except Exception as e:
            logger.error(ErrorMessageMapper.get_log_message(e, {'operation': 'setup_google_calendar'}), exc_info=True)
            raise
    
    def reauthenticate(self):
        """
        Force re-authentication with Google Calendar.
        This will open a browser window for the user to authorize the application.
        
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            logger.info("Starting re-authentication process")
            self.calendar_service = self.setup_google_calendar(force_reauth=True)
            logger.info("Re-authentication successful")
            return True
        except Exception as e:
            logger.error(f"Re-authentication failed: {e}", exc_info=True)
            return False
    
    def is_authenticated(self):
        """
        Check if calendar service is authenticated and available.
        
        Returns:
            True if authenticated, False otherwise
        """
        return self.calendar_service is not None
    
    def create_payment_event(self, fine_id, fine_number, due_date, amount):
        """Create Google Calendar event for payment reminder"""
        if self.calendar_service is None:
            logger.warning("Calendar service not available. Please re-authenticate.")
            return False
        
        try:
            logger.debug(f"Creating payment event for fine {fine_number} (ID: {fine_id})")
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
                calendarId='primary',
                timeMin=datetime.datetime.combine(due_date, datetime.time.min).isoformat() + 'Z',
                timeMax=datetime.datetime.combine(due_date, datetime.time.max).isoformat() + 'Z',
                q=fine_number
            ).execute()
            
            if not events_result.get('items', []):
                created_event = self.calendar_service.events().insert(
                    calendarId='primary', body=event).execute()
                
                logger.info(f"Created payment calendar event for fine {fine_number} (event ID: {created_event.get('id')})")
                
                # Update the database
                self.fine_model.mark_payment_event_created(fine_id)
                return True
            else:
                logger.debug(f"Payment event for fine {fine_number} already exists, skipping")
                return False
        except HttpError as e:
            logger.error(ErrorMessageMapper.get_log_message(e, {
                'operation': 'create_payment_event',
                'fine_number': fine_number,
                'fine_id': fine_id
            }), exc_info=True)
            return False
        except Exception as e:
            logger.error(ErrorMessageMapper.get_log_message(e, {
                'operation': 'create_payment_event',
                'fine_number': fine_number,
                'fine_id': fine_id
            }), exc_info=True)
            return False
    
    def create_driver_id_event(self, fine_id, fine_number, driver_id_due_date):
        """Create Google Calendar event for driver ID submission reminder"""
        if self.calendar_service is None:
            logger.warning("Calendar service not available. Please re-authenticate.")
            return False
        
        if not driver_id_due_date:
            logger.debug(f"No driver ID due date for fine {fine_number}, skipping event creation")
            return False
        
        try:
            logger.debug(f"Creating driver ID event for fine {fine_number} (ID: {fine_id})")
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
                calendarId='primary',
                timeMin=datetime.datetime.combine(driver_id_due_date, datetime.time.min).isoformat() + 'Z',
                timeMax=datetime.datetime.combine(driver_id_due_date, datetime.time.max).isoformat() + 'Z',
                q=fine_number
            ).execute()
            
            if not events_result.get('items', []):
                created_event = self.calendar_service.events().insert(
                    calendarId='primary', body=event).execute()
                
                logger.info(f"Created driver ID calendar event for fine {fine_number} (event ID: {created_event.get('id')})")
                
                # Update the database
                self.fine_model.mark_driver_id_event_created(fine_id)
                return True
            else:
                logger.debug(f"Driver ID event for fine {fine_number} already exists, skipping")
                return False
        except HttpError as e:
            logger.error(ErrorMessageMapper.get_log_message(e, {
                'operation': 'create_driver_id_event',
                'fine_number': fine_number,
                'fine_id': fine_id
            }), exc_info=True)
            return False
        except Exception as e:
            logger.error(ErrorMessageMapper.get_log_message(e, {
                'operation': 'create_driver_id_event',
                'fine_number': fine_number,
                'fine_id': fine_id
            }), exc_info=True)
            return False
    
    def create_calendar_events(self):
        """Create Google Calendar events for all pending fines"""
        if self.calendar_service is None:
            raise Exception("Calendar service not available. Please re-authenticate with Google Calendar.")
        
        logger.info("Starting calendar events creation process")
        results = {
            'payment_events': {'created': 0, 'skipped': 0},
            'driver_id_events': {'created': 0, 'skipped': 0}
        }
        
        try:
            # Process payment events
            payment_fines = self.fine_model.get_fines_without_payment_events()
            logger.info(f"Found {len(payment_fines)} fines without payment events")
            for fine_id, fine_number, due_date, amount in payment_fines:
                if self.create_payment_event(fine_id, fine_number, due_date, amount):
                    results['payment_events']['created'] += 1
                else:
                    results['payment_events']['skipped'] += 1
            
            # Process driver ID events
            driver_id_fines = self.fine_model.get_fines_without_driver_id_events()
            logger.info(f"Found {len(driver_id_fines)} fines without driver ID events")
            for fine_id, fine_number, driver_id_due_date in driver_id_fines:
                if self.create_driver_id_event(fine_id, fine_number, driver_id_due_date):
                    results['driver_id_events']['created'] += 1
                else:
                    results['driver_id_events']['skipped'] += 1
            
            logger.info(f"Calendar events creation complete. Payment: {results['payment_events']}, Driver ID: {results['driver_id_events']}")
            return results
        except Exception as e:
            logger.error(ErrorMessageMapper.get_log_message(e, {'operation': 'create_calendar_events'}), exc_info=True)
            raise