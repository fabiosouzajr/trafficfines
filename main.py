# main.py
import tkinter as tk
from gui.app import TrafficFineApp

def main():
    root = tk.Tk()
    app = TrafficFineApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
