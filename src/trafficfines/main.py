# main.py
import logging
import sys
import tkinter as tk
from trafficfines.gui.app import TrafficFineApp
from trafficfines.utils.logger import setup_logger
from trafficfines.config import LOG_FILE, validate_config, ConfigurationError

# Set up root logger for the application
logger = setup_logger('trafficfines', log_file=LOG_FILE, level=logging.INFO)

def main():
    logger.info("Application started")
    try:
        # Validate configuration before starting application
        try:
            validate_config()
            logger.info("Configuration validation passed")
        except ConfigurationError as e:
            logger.critical(f"Configuration error: {e}")
            print(f"Configuration Error: {e}", file=sys.stderr)
            print("\nPlease fix the configuration issues and try again.", file=sys.stderr)
            sys.exit(1)
        
        root = tk.Tk()
        app = TrafficFineApp(root)
        root.mainloop()
        logger.info("Application closed")
    except Exception as e:
        logger.critical(f"Critical error during application execution: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()

