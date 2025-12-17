import tkinter as tk
from tkinter import ttk, messagebox
import threading
from trafficfines.gcal_integration.integration import CalendarIntegration
from trafficfines.utils.logger import get_logger
from trafficfines.utils.error_messages import ErrorMessageMapper
from trafficfines.utils.helpers import format_datetime

logger = get_logger(__name__)


class CalendarTab(ttk.Frame):
    def __init__(self, parent, calendar_integration=None):
        super().__init__(parent, padding="10")
        self.calendar_integration = calendar_integration or CalendarIntegration()
        self.on_events_created = None  # Callback to notify when events are created
        # Get root window reference
        self.root = self._get_root()
        self.create_widgets()
    
    def _get_root(self):
        """Get the root Tk window"""
        widget = self
        while widget.master:
            widget = widget.master
        return widget
    
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_label = ttk.Label(
            main_frame, 
            text="Google Calendar Integration", 
            font=("Arial", 14, "bold")
        )
        header_label.pack(pady=(20, 10))
        
        info_label = ttk.Label(
            main_frame,
            text="Create calendar events for payment deadlines and driver identification submissions.",
            wraplength=500,
            justify=tk.CENTER
        )
        info_label.pack(pady=(0, 10))
        
        # Authentication status frame
        auth_frame = ttk.LabelFrame(main_frame, text="Authentication Status")
        auth_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Authentication status label
        self.auth_status_var = tk.StringVar()
        self.update_auth_status()
        auth_status_label = ttk.Label(
            auth_frame,
            textvariable=self.auth_status_var,
            font=("Arial", 10)
        )
        auth_status_label.pack(pady=10, padx=10)
        
        # Re-authenticate button
        self.reauth_btn = ttk.Button(
            auth_frame,
            text="Re-authenticate with Google Calendar",
            command=self.reauthenticate,
            padding=(10, 5)
        )
        self.reauth_btn.pack(pady=5)
        
        # Create events button
        self.create_events_btn = ttk.Button(
            main_frame, 
            text="Create Calendar Events", 
            command=self.create_events,
            padding=(20, 10),
            state=tk.NORMAL if self.calendar_integration.is_authenticated() else tk.DISABLED
        )
        self.create_events_btn.pack(pady=10)
        
        # Progress indicator for event creation (initially hidden)
        self.progress_frame = ttk.Frame(main_frame)
        self.progress_frame.pack(pady=10, fill=tk.X, padx=20)
        
        self.progress_label = ttk.Label(self.progress_frame, text="")
        self.progress_label.pack(pady=5)
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='indeterminate', length=400)
        self.progress_bar.pack(pady=5, fill=tk.X, expand=True)
        
        self.progress_frame.pack_forget()  # Hide initially
        
        # Update button state based on auth status (after all widgets are created)
        self.update_auth_button_state()
        
        # Status display area
        self.status_frame = ttk.LabelFrame(main_frame, text="Calendar Sync Status")
        self.status_frame.pack(fill=tk.BOTH, expand=True, pady=20, padx=10)
        
        # Status indicators
        self.payment_status = self.create_status_indicator(self.status_frame, "Payment Events", 0)
        self.driver_id_status = self.create_status_indicator(self.status_frame, "Driver ID Events", 1)
        
        # Last sync time
        self.last_sync_var = tk.StringVar(value="Last sync: Never")
        ttk.Label(main_frame, textvariable=self.last_sync_var).pack(pady=10, side=tk.BOTTOM)
    
    def create_status_indicator(self, parent, label_text, row):
        """Create a status indicator with progress bar"""
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=0, sticky=tk.W+tk.E, padx=20, pady=10)
        parent.columnconfigure(0, weight=1)
    
        ttk.Label(frame, text=label_text).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        stats_frame = ttk.Frame(frame)
        stats_frame.grid(row=1, column=0, sticky=tk.W+tk.E)    
        created_var = tk.StringVar(value="0 created")
        skipped_var = tk.StringVar(value="0 skipped")
        
        ttk.Label(stats_frame, textvariable=created_var).pack(side=tk.LEFT, padx=(0, 20))
        ttk.Label(stats_frame, textvariable=skipped_var).pack(side=tk.LEFT)
        
        return {
            'created_var': created_var,
            'skipped_var': skipped_var
        }
    
    def create_events(self):
        """Create calendar events for all pending fines"""
        # Disable button during processing
        self.create_events_btn.config(state=tk.DISABLED)
        
        # Show progress indicator
        self.progress_frame.pack(pady=10, fill=tk.X, padx=20)
        self.progress_label.config(text="Creating calendar events...")
        self.progress_bar.start()
        self.update_status("Processing...", "Processing...")
        self.update_idletasks()
        
        # Run event creation in separate thread to prevent UI freezing
        def create_events_thread():
            try:
                # Create events
                results = self.calendar_integration.create_calendar_events()
                
                # Update UI on main thread
                self.root.after(0, lambda: self._finish_event_creation(results))
                
            except Exception as e:
                logger.error(f"Failed to create calendar events: {e}", exc_info=True)
                user_message = ErrorMessageMapper.format_error_for_user(e, {'operation': 'create_calendar_events'})
                self.root.after(0, lambda: messagebox.showerror("Erro", user_message))
                self.root.after(0, lambda: self._finish_event_creation(None, error=True))
        
        thread = threading.Thread(target=create_events_thread, daemon=True)
        thread.start()
    
    def _finish_event_creation(self, results, error=False):
        """Finish event creation and update UI"""
        # Stop and hide progress indicator
        self.progress_bar.stop()
        self.progress_frame.pack_forget()
        
        # Re-enable button
        self.create_events_btn.config(state=tk.NORMAL if self.calendar_integration.is_authenticated() else tk.DISABLED)
        
        if not error and results:
            # Update status indicators
            self.update_status(
                f"{results['payment_events']['created']} created",
                f"{results['payment_events']['skipped']} skipped",
                is_payment=True
            )
            
            self.update_status(
                f"{results['driver_id_events']['created']} created",
                f"{results['driver_id_events']['skipped']} skipped",
                is_payment=False
            )
            
            # Update last sync time
            from datetime import datetime
            self.last_sync_var.set(f"Last sync: {format_datetime(datetime.now())}")
            
            # Show summary message
            total_created = results['payment_events']['created'] + results['driver_id_events']['created']
            if total_created > 0:
                messagebox.showinfo("Success", f"Created {total_created} calendar events successfully")
            else:
                messagebox.showinfo("Information", "No new calendar events needed to be created")
            
            # Notify listeners
            if self.on_events_created:
                self.on_events_created()
    
    def update_status(self, created_text, skipped_text, is_payment=True):
        """Update status indicators"""
        status = self.payment_status if is_payment else self.driver_id_status
        status['created_var'].set(created_text)
        status['skipped_var'].set(skipped_text)
    
    def update_auth_status(self):
        """Update authentication status display"""
        if self.calendar_integration.is_authenticated():
            self.auth_status_var.set("✓ Authenticated - Calendar features are available")
        else:
            self.auth_status_var.set("✗ Not authenticated - Please re-authenticate to use calendar features")
    
    def update_auth_button_state(self):
        """Update the state of authentication-related buttons"""
        is_authenticated = self.calendar_integration.is_authenticated()
        if is_authenticated:
            self.create_events_btn.config(state=tk.NORMAL)
        else:
            self.create_events_btn.config(state=tk.DISABLED)
    
    def reauthenticate(self):
        """Handle re-authentication with Google Calendar"""
        try:
            # Disable button during authentication
            self.reauth_btn.config(state=tk.DISABLED, text="Authenticating...")
            self.update_idletasks()
            
            # Show info message
            messagebox.showinfo(
                "Re-authentication",
                "A browser window will open for you to authorize the application.\n\n"
                "Please complete the authorization in your browser."
            )
            
            # Perform re-authentication
            success = self.calendar_integration.reauthenticate()
            
            if success:
                messagebox.showinfo(
                    "Success",
                    "Successfully authenticated with Google Calendar!\n\n"
                    "You can now create calendar events."
                )
                # Update UI
                self.update_auth_status()
                self.update_auth_button_state()
            else:
                messagebox.showerror(
                    "Authentication Failed",
                    "Failed to authenticate with Google Calendar.\n\n"
                    "Please check:\n"
                    "- Your internet connection\n"
                    "- That credentials.json file exists\n"
                    "- Check the log file for more details"
                )
                self.update_auth_status()
                self.update_auth_button_state()
        
        except FileNotFoundError as e:
            messagebox.showerror(
                "Credentials File Missing",
                f"Credentials file not found: {e}\n\n"
                "Please ensure credentials.json is in the project root directory."
            )
            logger.error(f"Credentials file not found: {e}")
        except Exception as e:
            logger.error(f"Re-authentication error: {e}", exc_info=True)
            user_message = ErrorMessageMapper.format_error_for_user(e, {'operation': 'reauthenticate'})
            messagebox.showerror("Erro", user_message)
        finally:
            # Re-enable button
            self.reauth_btn.config(state=tk.NORMAL, text="Re-authenticate with Google Calendar")