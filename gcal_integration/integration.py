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
    
    def setup_google_calendar(self):
        """Set up and authenticate with Google Calendar API"""
        creds = None
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)
                
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)
                
        return build('calendar', 'v3', credentials=creds)
    
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
            calendarId='primary',
            timeMin=datetime.datetime.combine(due_date, datetime.time.min).isoformat() + 'Z',
            timeMax=datetime.datetime.combine(due_date, datetime.time.max).isoformat() + 'Z',
            q=fine_number
        ).execute()
        
        if not events_result.get('items', []):
            event = self.calendar_service.events().insert(
                calendarId='primary', body=event).execute()
            
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
            calendarId='primary',
            timeMin=datetime.datetime.combine(driver_id_due_date, datetime.time.min).isoformat() + 'Z',
            timeMax=datetime.datetime.combine(driver_id_due_date, datetime.time.max).isoformat() + 'Z',
            q=fine_number
        ).execute()
        
        if not events_result.get('items', []):
            event = self.calendar_service.events().insert(
                calendarId='primary', body=event).execute()
            
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