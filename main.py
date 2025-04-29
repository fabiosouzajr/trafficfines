# main.py
import logging
import tkinter as tk
from gui.app import TrafficFineApp

# Set up logging
logging.basicConfig(
    level=logging.INFO,  # You can change to DEBUG for more verbosity
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

def main():
    logging.info("Application started")
    root = tk.Tk()
    app = TrafficFineApp(root)
    root.mainloop()
    logging.info("Application closed")

if __name__ == "__main__":
    main()
