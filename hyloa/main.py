# This file is part of HYLOA - HYsteresis LOop Analyzer.
# Copyright (C) 2024 Francesco Zeno Costanzo

# HYLOA is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# HYLOA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with HYLOA. If not, see <https://www.gnu.org/licenses/>.


"""
Entry point for HYLOA application.
"""

import sys
import time 
from importlib import resources
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer


# Duration to show the splash screen at minimum
MIN_SPLASH_TIME = 3.0  # Seconds


class Splash(QWidget):
    '''
    Splash screen with a logo and a progress bar.
    '''
    def __init__(self, pixmap):
        '''
        Initialize the splash screen with a logo and a progress bar.

        Parameters
        ----------
        pixmap : QPixmap
            The logo to display on the splash screen.
        '''
        super().__init__(
            flags=Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )

        self.setAttribute(Qt.WA_TranslucentBackground)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Logo
        self.logo = QLabel()
        self.logo.setPixmap(pixmap)
        self.logo.setAlignment(Qt.AlignCenter)

        # Progress Bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setFormat("%p%")

        layout.addWidget(self.logo)
        layout.addWidget(self.progress)

        self.adjustSize()
        self.move(
            self.screen().geometry().center() - self.rect().center()
        )

    def set_progress(self, value):
        '''
        Update the progress bar value.
        
        Parameters
        ----------
        value : int
            The new value for the progress bar (0-100).
        '''
        self.progress.setValue(value)


def compute_remaining_time(start_time, min_splash_time):
    '''
    Compute the remaining time to show the splash screen

    Parameters
    ----------
    start_time : float
        The time when the splash screen was shown (monotonic).
    min_splash_time : float
        The minimum duration to show the splash screen (seconds).
    Returns
    -------
    int
        Remaining time in milliseconds to show the splash screen.
    '''
    elapsed = time.monotonic() - start_time
    return max(0, int((min_splash_time - elapsed) * 1000))


def main():
    '''
    Main entry point for the HYLOA application.
    '''
    start_time = time.monotonic()
    app = QApplication(sys.argv)

    # Load splash screen resources
    with resources.path("hyloa.resources", "icon-6.png") as p:
        pixmap = QPixmap(str(p))

    splash = Splash(pixmap)
    splash.show()
    splash.set_progress(20)
    app.processEvents()

    # Import main window (heavy part of the loading)
    from hyloa.gui.main_window import MainApp
    splash.set_progress(60)
    app.processEvents()
    window = MainApp()
   
    remaining = compute_remaining_time(start_time, MIN_SPLASH_TIME)

    def finish():
        splash.set_progress(100)
        app.processEvents()
        window.show()
        splash.close()

    QTimer.singleShot(remaining, finish)
    

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
