"""
Code to run to start the analysis.
"""

import sys
from PyQt5.QtWidgets import QApplication

from hyloa.gui.main_window import MainApp


def main():
    ''' Function that starts the gui for analysis
    '''   
    app = QApplication(sys.argv)
    window = MainApp()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
