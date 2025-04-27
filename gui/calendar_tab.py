import tkinter as tk
from tkinter import ttk, messagebox
from gcal_integration.integration import CalendarIntegration


class CalendarTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding="10")
        
        self.calendar_integration = CalendarIntegration()
        self.on_events_created = None  # Callback to notify when events are created
        
        self.create_widgets()
    
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