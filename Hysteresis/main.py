"""
Code to run to start the analysis.
"""

from tkinter import Tk
from Hysteresis.gui.main_window import MainApp

def main():
    root = Tk()
    MainApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
