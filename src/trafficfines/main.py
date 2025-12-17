# main.py
import logging
import tkinter as tk
from trafficfines.gui.app import TrafficFineApp
from trafficfines.utils.logger import setup_logger
from trafficfines.config import LOG_FILE

# Set up root logger for the application
logger = setup_logger('trafficfines', log_file=LOG_FILE, level=logging.INFO)

def main():
    logger.info("Application started")
    try:
        root = tk.Tk()
        app = TrafficFineApp(root)
        root.mainloop()
        logger.info("Application closed")
    except Exception as e:
        logger.critical(f"Critical error during application execution: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()

