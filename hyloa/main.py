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
