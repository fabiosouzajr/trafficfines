import tkinter as tk
from tkinter import ttk, messagebox
from gcal_integration.integration import CalendarIntegration


class CalendarTab(ttk.Frame):
    def __init__(self, parent, calendar_integration=None):
        super().__init__(parent, padding="10")
        self.calendar_integration = calendar_integration or CalendarIntegration()
        self.on_events_created = None  # Callback to notify when events are created
        self.on_calendar_changed = None  # Callback to notify when calendar selection changes
        self.create_widgets()
    
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # --- Calendar selection section ---
        selection_frame = ttk.LabelFrame(main_frame, text="Calendar Selection")
        selection_frame.pack(fill=tk.X, pady=(0, 15), padx=5)

        # Check if calendar service is available
        if not self.calendar_integration.calendar_service:
            self.show_credentials_error(selection_frame)
            return

        # Account name
        account_name = self.calendar_integration.get_account_name()
        ttk.Label(selection_frame, text=f"Google Account: {account_name}").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)

        # Calendar list
        ttk.Label(selection_frame, text="Select Calendar:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.calendars = self.calendar_integration.list_calendars()
        self.calendar_names = [cal['summary'] for cal in self.calendars]
        self.calendar_ids = [cal['id'] for cal in self.calendars]
        self.selected_calendar_var = tk.StringVar()
        # Set default selection
        default_id = self.calendar_integration.get_selected_calendar()
        default_name = next((cal['summary'] for cal in self.calendars if cal['id'] == default_id), self.calendar_names[0] if self.calendar_names else '')
        self.selected_calendar_var.set(default_name)
        
        # Calendar selection frame
        calendar_select_frame = ttk.Frame(selection_frame)
        calendar_select_frame.grid(row=1, column=1, padx=5, pady=5)
        
        self.calendar_combo = ttk.Combobox(calendar_select_frame, values=self.calendar_names, 
                                          textvariable=self.selected_calendar_var, state="readonly", width=30)
        self.calendar_combo.pack(side=tk.LEFT, padx=(0, 5))
        
        change_btn = ttk.Button(calendar_select_frame, text="Change", command=self.confirm_calendar_change)
        change_btn.pack(side=tk.LEFT)

        # Show current selection
        self.current_calendar_label = ttk.Label(selection_frame, text=f"Current: {default_name}")
        self.current_calendar_label.grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=5, pady=(0,5))

        # Create new calendar
        ttk.Label(selection_frame, text="Create New Calendar:").grid(row=3, column=0, sticky=tk.W, padx=5)
        self.new_calendar_var = tk.StringVar()
        new_calendar_entry = ttk.Entry(selection_frame, textvariable=self.new_calendar_var, width=20)
        new_calendar_entry.grid(row=3, column=1, padx=5, pady=5)
        create_btn = ttk.Button(selection_frame, text="Create", command=self.create_new_calendar)
        create_btn.grid(row=3, column=2, padx=5, pady=5)

        # --- End calendar selection section ---
        
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
        info_label.pack(pady=(0, 20))
        
        # Create events button
        create_events_btn = ttk.Button(
            main_frame, 
            text="Create Calendar Events", 
            command=self.create_events,
            padding=(20, 10)
        )
        create_events_btn.pack(pady=10)
        
        # Status display area
        self.status_frame = ttk.LabelFrame(main_frame, text="Calendar Sync Status")
        self.status_frame.pack(fill=tk.BOTH, expand=True, pady=20, padx=10)
        
        # Status indicators
        self.payment_status = self.create_status_indicator(self.status_frame, "Payment Events", 0)
        self.driver_id_status = self.create_status_indicator(self.status_frame, "Driver ID Events", 1)
        
        # Last sync time
        self.last_sync_var = tk.StringVar(value="Last sync: Never")
        ttk.Label(main_frame, textvariable=self.last_sync_var).pack(pady=10, side=tk.BOTTOM)
    
    def show_credentials_error(self, parent):
        """Show error message when credentials are missing"""
        error_frame = ttk.Frame(parent)
        error_frame.pack(fill=tk.X, padx=5, pady=5)
        
        error_label = ttk.Label(
            error_frame,
            text="Google Calendar credentials not found",
            font=("Arial", 10, "bold"),
            foreground="red"
        )
        error_label.pack(pady=(0, 5))
        
        instructions = (
            "To use Google Calendar integration:\n\n"
            "1. Go to Google Cloud Console (https://console.cloud.google.com)\n"
            "2. Create a project and enable the Google Calendar API\n"
            "3. Create OAuth 2.0 credentials\n"
            "4. Download the credentials and save as 'credentials.json' in the application directory"
        )
        
        instructions_label = ttk.Label(
            error_frame,
            text=instructions,
            wraplength=400,
            justify=tk.LEFT
        )
        instructions_label.pack(pady=5)
        
        # Disable all calendar-related buttons
        for widget in parent.winfo_children():
            if isinstance(widget, (ttk.Button, ttk.Combobox, ttk.Entry)):
                widget.configure(state="disabled")
    
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
        if not self.calendar_integration.calendar_service:
            messagebox.showerror("Error", "Google Calendar integration is not available. Please check your credentials.")
            return
            
        try:
            # Show processing indicator
            self.update_status("Processing...", "Processing...")
            self.update_idletasks()
            
            # Create events
            results = self.calendar_integration.create_calendar_events()
            
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
            self.last_sync_var.set(f"Last sync: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Show summary message
            total_created = results['payment_events']['created'] + results['driver_id_events']['created']
            if total_created > 0:
                messagebox.showinfo("Success", f"Created {total_created} calendar events successfully")
            else:
                messagebox.showinfo("Information", "No new calendar events needed to be created")
            
            # Notify listeners
            if self.on_events_created:
                self.on_events_created()
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create calendar events: {e}")
    
    def update_status(self, created_text, skipped_text, is_payment=True):
        """Update status indicators"""
        status = self.payment_status if is_payment else self.driver_id_status
        status['created_var'].set(created_text)
        status['skipped_var'].set(skipped_text)

    def confirm_calendar_change(self):
        """Show confirmation dialog for calendar change"""
        if not self.calendar_integration.calendar_service:
            messagebox.showerror("Error", "Google Calendar integration is not available. Please check your credentials.")
            return
            
        selected_name = self.selected_calendar_var.get()
        current_name = self.current_calendar_label.cget("text").replace("Current: ", "")
        
        if selected_name == current_name:
            messagebox.showinfo("No Change", "The selected calendar is already the current calendar.")
            return
            
        response = messagebox.askyesno(
            "Confirm Calendar Change",
            f"Are you sure you want to change the calendar from:\n\n"
            f"Current: {current_name}\n"
            f"To: {selected_name}\n\n"
            "This will affect all calendar operations."
        )
        
        if response:
            self.on_calendar_selected()

    def on_calendar_selected(self, event=None):
        selected_name = self.selected_calendar_var.get()
        selected_id = next((cal['id'] for cal in self.calendars if cal['summary'] == selected_name), 'primary')
        self.calendar_integration.set_selected_calendar(selected_id)
        self.current_calendar_label.config(text=f"Current: {selected_name}")
        
        # Notify listeners about calendar change
        if self.on_calendar_changed:
            self.on_calendar_changed()

    def create_new_calendar(self):
        """Create a new calendar"""
        if not self.calendar_integration.calendar_service:
            messagebox.showerror("Error", "Google Calendar integration is not available. Please check your credentials.")
            return
            
        name = self.new_calendar_var.get().strip()
        if not name:
            messagebox.showwarning("Input Required", "Please enter a name for the new calendar.")
            return
        created = self.calendar_integration.create_calendar(name)
        if created:
            messagebox.showinfo("Success", f"Calendar '{name}' created.")
            # Refresh calendar list
            self.calendars = self.calendar_integration.list_calendars()
            self.calendar_names = [cal['summary'] for cal in self.calendars]
            self.calendar_ids = [cal['id'] for cal in self.calendars]
            self.calendar_combo['values'] = self.calendar_names
            self.selected_calendar_var.set(name)
            self.on_calendar_selected()
        else:
            messagebox.showerror("Error", "Failed to create calendar.")