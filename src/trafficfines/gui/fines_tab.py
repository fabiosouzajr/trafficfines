# gui/fines_tab.py

import tkinter as tk
from tkinter import ttk
import datetime
from trafficfines.db.models import FineModel
from trafficfines.utils.helpers import format_currency, format_date, format_datetime

class FinesTab(ttk.Frame):
    def __init__(self, parent, calendar_integration=None):
        super().__init__(parent, padding="10")
        self.fine_model = FineModel()
        self.calendar_integration = calendar_integration
        self.create_widgets()
        self.refresh_fines_list()
    
    def create_widgets(self):
        # Create filter frame
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.filter_var = tk.StringVar(value="All")
        filter_combo = ttk.Combobox(filter_frame, textvariable=self.filter_var, 
                                    values=["All", "Pending Payment", "Pending Driver ID", "Complete"])
        filter_combo.pack(side=tk.LEFT, padx=(0, 10))
        filter_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_fines_list())
        
        # Search frame
        search_frame = ttk.Frame(filter_frame)
        search_frame.pack(side=tk.RIGHT)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT)
        search_entry.bind("<KeyRelease>", lambda e: self.refresh_fines_list())
        
        # Create treeview with scrollbars
        treeview_frame = ttk.Frame(self)
        treeview_frame.pack(fill=tk.BOTH, expand=True)
        
        # Define columns
        columns = ("Fine Number", "Issue Date", "Driver ID Due Date", "Amount", "License Plate", "Payment Event", "Driver ID Event")
        self.tree = ttk.Treeview(treeview_frame, columns=columns, show="headings")
        
        # Define headings
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        
        # Add scrollbars
        vsb = ttk.Scrollbar(treeview_frame, orient=tk.VERTICAL, command=self.tree.yview)
        hsb = ttk.Scrollbar(treeview_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))
        hsb.grid(row=1, column=0, sticky=(tk.E, tk.W))
        
        treeview_frame.columnconfigure(0, weight=1)
        treeview_frame.rowconfigure(0, weight=1)
        
        # Add buttons at the bottom
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, pady=10)
        
        refresh_btn = ttk.Button(button_frame, text="Refresh", command=self.refresh_fines_list)
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        view_details_btn = ttk.Button(button_frame, text="View Details", command=self.view_fine_details)
        view_details_btn.pack(side=tk.LEFT, padx=5)
        
        # Double-click event
        self.tree.bind("<Double-1>", lambda e: self.view_fine_details())
    
    def refresh_fines_list(self):
        """Refresh the fines list with optional filtering and searching"""
        # Clear current items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Load fines from database
        fines = self.fine_model.get_all_fines()
        
        # Apply filter
        filter_value = self.filter_var.get()
        search_text = self.search_var.get().lower()
        
        for fine in fines:
            fine_number = fine['fine_number']
            notification_date = format_date(fine['notification_date']) if fine['notification_date'] else ""
            driver_id_due_date = format_date(fine['driver_id_due_date']) if fine['driver_id_due_date'] else ""
            amount = format_currency(fine['amount'])
            license_plate = fine['license_plate'] if fine['license_plate'] else ""
            payment_status = "Created" if fine['payment_event_created'] else "Pending"
            driver_id_status = "Created" if fine['driver_id_event_created'] else "Pending"
            
            # Apply filter
            if filter_value == "Pending Payment" and fine['payment_event_created']:
                continue
            elif filter_value == "Pending Driver ID" and fine['driver_id_event_created']:
                continue
            elif filter_value == "Complete" and (not fine['payment_event_created'] or not fine['driver_id_event_created']):
                continue
            
            # Apply search
            if search_text:
                search_fields = [
                    str(fine_number).lower(),
                    str(notification_date).lower(),
                    str(driver_id_due_date).lower(),
                    str(license_plate).lower()
                ]
                if not any(search_text in field for field in search_fields):
                    continue
            
            self.tree.insert("", tk.END, values=(
                fine_number, notification_date, driver_id_due_date, amount, 
                license_plate, payment_status, driver_id_status
            ))
    
    def view_fine_details(self):
        """Show details of selected fine in a popup window"""
        selected = self.tree.selection()
        if not selected:
            return
        
        fine_number = self.tree.item(selected[0], 'values')[0]
        fine = self.fine_model.get_fine_by_number(fine_number)
        
        if fine:
            details_window = tk.Toplevel(self)
            details_window.title(f"Fine Details: {fine_number}")
            details_window.geometry("500x400")
            
            # Create frame for details
            details_frame = ttk.Frame(details_window, padding="20")
            details_frame.pack(fill=tk.BOTH, expand=True)
            
            row = 0
            for field in fine.keys():
                if field != 'id':  # Skip ID field
                    ttk.Label(details_frame, text=f"{field.replace('_', ' ').title()}:").grid(
                        row=row, column=0, sticky=tk.W, padx=5, pady=2)
                    
                    value = fine[field]
                    if field == 'amount':
                        value = format_currency(value)
                    elif value is None:
                        value = "N/A"
                    elif field.endswith('_created'):
                        value = "Yes" if value else "No"
                    elif isinstance(value, (datetime.date, datetime.datetime)):
                        # Format date/datetime fields using locale config
                        value = format_date(value) if isinstance(value, datetime.date) else format_datetime(value)
                        
                    ttk.Label(details_frame, text=str(value)).grid(
                        row=row, column=1, sticky=tk.W, padx=5, pady=2)
                    
                    row += 1
            
            # Add close button
            ttk.Button(details_window, text="Close", command=details_window.destroy).pack(pady=10)