# main.py
import logging
import tkinter as tk
import os
import sys
import pkg_resources
from gui.app import TrafficFineApp
from gui.verification_dialog import EnvironmentVerificationDialog

# Set up logging
logging.basicConfig(
    level=logging.INFO,  # You can change to DEBUG for more verbosity
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

def check_required_directories():
    required_dirs = ['gui', 'utils', 'pdf', 'db', 'multas', 'gcal_integration']
    missing_dirs = []
    
    for dir_name in required_dirs:
        if not os.path.isdir(dir_name):
            missing_dirs.append(dir_name)
    
    return missing_dirs

def check_required_files():
    required_files = ['config.py', 'requirements.txt', 'traffic_fines.db']
    missing_files = []
    
    for file_name in required_files:
        if not os.path.isfile(file_name):
            missing_files.append(file_name)
    
    return missing_files

def check_dependencies():
    try:
        with open('requirements.txt', 'r') as f:
            required = {line.strip() for line in f if line.strip() and not line.startswith('#')}
        
        # Get installed packages with their versions
        installed = {pkg.key: pkg.version for pkg in pkg_resources.working_set}
        missing = set()
        
        for package in required:
            # Split package name and version if specified
            if '==' in package:
                name, version = package.split('==')
                name = name.lower()  # Convert to lowercase for comparison
                if name not in installed:
                    missing.add(package)
            else:
                # If no version specified, just check if package is installed
                name = package.lower()  # Convert to lowercase for comparison
                if name not in installed:
                    missing.add(package)
        
        return missing
    except Exception as e:
        logging.error(f"Error checking dependencies: {str(e)}")
        return set()  # Return empty set on error to prevent false positives

def verify_environment(root):
    missing_dirs = check_required_directories()
    missing_files = check_required_files()
    missing_deps = check_dependencies()
    
    if missing_dirs or missing_files or missing_deps:
        dialog = EnvironmentVerificationDialog(root, missing_dirs, missing_files, missing_deps)
        root.wait_window(dialog.dialog)
        return dialog.result
    
    return True

def main():
    logging.info("Application started")
    
    # Create the root window
    root = tk.Tk()
    
    # Create the main application first
    app = TrafficFineApp(root)
    
    # Verify environment after creating the main window
    if not verify_environment(root):
        logging.error("Application initialization failed due to missing components")
        root.destroy()
        sys.exit(1)
    
    # Start the main loop
    root.mainloop()
    logging.info("Application closed")

if __name__ == "__main__":
    main()
