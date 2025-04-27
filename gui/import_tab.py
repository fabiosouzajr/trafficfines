# gui/import_tab.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os

from config import DEFAULT_PDF_FOLDER
from pdf.parser import PDFParser

class ImportTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding="10")
        
        self.pdf_parser = PDFParser()
        self.on_fines_updated = None  # Callback to notify when fines are updated
        
        self.create_widgets()
    
    def create_widgets(self):
        ttk.Label(self, text="Select folder containing traffic fine PDFs:").grid(row=0, column=0, sticky=tk.W, pady=10)
        
        # Folder selection
        self.folder_path = tk.StringVar(value=DEFAULT_PDF_FOLDER)
        entry = ttk.Entry(self, textvariable=self.folder_path, width=50)
        entry.grid(row=1, column=0, padx=5, pady=5)
        
        browse_btn = ttk.Button(self, text="Browse", command=self.browse_folder)
        browse_btn.grid(row=1, column=1, padx=5, pady=5)
        
        # Action buttons
        scan_btn = ttk.Button(self, text="Scan Folder", command=self.scan_folder)
        scan_btn.grid(row=2, column=0, columnspan=2, pady=20)
        
        # Results area
        self.result_label = ttk.Label(self, text="")
        self.result_label.grid(row=3, column=0, columnspan=2, pady=10)
        
        # Results list
        self.result_frame = ttk.LabelFrame(self, text="Processing Results")
        self.result_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        # Make the frame expandable
        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)
        
        # Scrollable results text
        self.results_text = tk.Text(self.result_frame, height=10, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(self.result_frame, command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=scrollbar.set)
        
        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Make the results text read-only
        self.results_text.config(state=tk.DISABLED)
    
    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder_path.set(folder_selected)
    
    def scan_folder(self):
        folder = self.folder_path.get()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Error", "Please select a valid folder")
            return
        
        try:
            # Clear previous results
            self.results_text.config(state=tk.NORMAL)
            self.results_text.delete(1.0, tk.END)
            
            # Process PDFs
            results = self.pdf_parser.scan_folder_for_pdfs(folder)
            
            # Update result summary
            self.result_label.config(
                text=f"Processed {len(results['processed'])} PDF files successfully. {len(results['errors'])} errors."
            )
            
            # Show detailed results
            if results['processed']:
                self.results_text.insert(tk.END, "Successfully processed:\n")
                for file in results['processed']:
                    self.results_text.insert(tk.END, f"✓ {file}\n")
                
            if results['errors']:
                self.results_text.insert(tk.END, "\nErrors:\n")
                for error in results['errors']:
                    self.results_text.insert(tk.END, f"✗ {error}\n")
            
            # Make the results text read-only again
            self.results_text.config(state=tk.DISABLED)
            
            # Notify other components that fines have been updated
            if self.on_fines_updated:
                self.on_fines_updated()
                
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")