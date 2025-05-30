# gui/app.py
import tkinter as tk
import tkinter.ttk as ttk
from gui.import_tab import ImportTab
from gui.fines_tab import FinesTab
from gui.calendar_tab import CalendarTab

class TrafficFineApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Traffic Fine Manager")
        self.root.geometry("800x600")
        self.root.minsize(700, 500)
        
        # Create shared calendar integration instance
        from gcal_integration.integration import CalendarIntegration
        self.calendar_integration = CalendarIntegration()
        
        # Ensure the window is properly configured
        self.root.update_idletasks()
        
        # Create the UI
        self.create_ui()
        
        # Ensure the window is ready to be shown
        self.root.update()
    
    def create_ui(self):
        # Create main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(expand=True, fill="both", padx=5, pady=5)
        
        # Create tabs
        self.tab_control = ttk.Notebook(main_frame)
        self.tab_control.pack(expand=1, fill="both")
        
        # Create each tab with shared calendar integration
        self.import_tab = ImportTab(self.tab_control)
        self.fines_tab = FinesTab(self.tab_control, self.calendar_integration)
        self.calendar_tab = CalendarTab(self.tab_control, self.calendar_integration)
        
        # Add tabs to notebook
        self.tab_control.add(self.import_tab, text="Import Fines")
        self.tab_control.add(self.fines_tab, text="View Fines")
        self.tab_control.add(self.calendar_tab, text="Calendar Events")
        
        # Add menu
        self.create_menu()
        
        # Set up callbacks between tabs
        self.import_tab.on_fines_updated = self.fines_tab.refresh_fines_list
        self.calendar_tab.on_events_created = self.fines_tab.refresh_fines_list
        self.calendar_tab.on_calendar_changed = self.fines_tab.refresh_fines_list
    
    def create_menu(self):
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def show_about(self):
        about_window = tk.Toplevel(self.root)
        about_window.title("About Traffic Fine Manager")
        about_window.geometry("300x200")
        
        ttk.Label(about_window, 
                  text="Traffic Fine Manager\nVersion 1.0\n\nManage traffic fines and Google Calendar events.",
                  justify=tk.CENTER).pack(expand=True)
        
        ttk.Button(about_window, text="Close", command=about_window.destroy).pack(pady=10)
