import tkinter as tk
from tkinter import ttk

class EnvironmentVerificationDialog:
    def __init__(self, parent, missing_dirs, missing_files, missing_deps):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Environment Verification")
        self.dialog.geometry("600x400")
        self.dialog.resizable(True, True)
        
        # Make dialog modal and always on top
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.attributes('-topmost', True)
        
        # Center the dialog over the parent window
        self.dialog.update_idletasks()
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        
        dialog_width = 600
        dialog_height = 400
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.dialog.geometry(f'{dialog_width}x{dialog_height}+{x}+{y}')
        
        # Create main frame
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title with warning icon
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = ttk.Label(title_frame, 
                              text="⚠️ Environment Verification Required", 
                              font=("Helvetica", 12, "bold"))
        title_label.pack(side=tk.LEFT, padx=5)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create tabs for each type of issue
        if missing_dirs:
            dirs_frame = ttk.Frame(notebook, padding="5")
            notebook.add(dirs_frame, text="Missing Directories")
            self._create_issue_list(dirs_frame, missing_dirs)
            
        if missing_files:
            files_frame = ttk.Frame(notebook, padding="5")
            notebook.add(files_frame, text="Missing Files")
            self._create_issue_list(files_frame, missing_files)
            
        if missing_deps:
            deps_frame = ttk.Frame(notebook, padding="5")
            notebook.add(deps_frame, text="Missing Dependencies")
            self._create_issue_list(deps_frame, missing_deps)
        
        # Instructions
        instructions = ttk.Label(main_frame, 
                               text="Please ensure all required components are in place before continuing.",
                               wraplength=500)
        instructions.pack(pady=10)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Exit", command=self.dialog.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Retry", command=self.retry).pack(side=tk.RIGHT, padx=5)
        
        self.result = False
    
    def _create_issue_list(self, parent, items):
        # Create a frame with scrollbar
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas and scrollbar
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack scrollbar and canvas
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        # Add items to the scrollable frame
        for item in items:
            ttk.Label(scrollable_frame, text=f"• {item}").pack(anchor="w", pady=2)
    
    def retry(self):
        self.result = True
        self.dialog.destroy() 