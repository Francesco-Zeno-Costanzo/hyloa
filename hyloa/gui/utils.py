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
Simple collapsible section widget for PyQt5, 
used in the settings dialog to group related settings together.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QToolButton
from PyQt5.QtCore import Qt


class CollapsibleSection(QWidget):
    ''' A collapsible section widget for PyQt5.
    '''
    def __init__(self, title="", parent=None):
        '''
        Initialize the collapsible section.
        
        Parameters
        ----------
            title (str): The title of the section.
            parent (QWidget): The parent widget.
        '''
        super().__init__(parent)

        self.toggle_button = QToolButton()
        self.toggle_button.setText(title)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(False)
        self.toggle_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toggle_button.setArrowType(Qt.RightArrow)
        self.toggle_button.clicked.connect(self.toggle)

        self.toggle_button.setStyleSheet("""
            QToolButton {
                border: none;
                text-align: left;
                padding: 6px;
                font-weight: bold;
            }
            QToolButton:hover {
                background-color: #eeeeee;
            }
            """
        )

        self.content_area = QWidget()
        self.content_area.setVisible(False)

        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(10, 5, 10, 10)
        self.content_area.setLayout(self.content_layout)

        self.content_area.setStyleSheet("""
            QWidget {
                border-left: 2px solid #dddddd;
            }
            """
        )

        layout = QVBoxLayout(self)
        layout.addWidget(self.toggle_button)
        layout.addWidget(self.content_area)

    def toggle(self):
        '''
        Toggle the visibility of the content area and update the arrow icon.
        '''
        is_open = self.toggle_button.isChecked()
        self.content_area.setVisible(is_open)
        self.toggle_button.setArrowType(
            Qt.DownArrow if is_open else Qt.RightArrow
        )

    def addWidget(self, widget):
        '''
        Add a widget to the content area.
        
        Parameters
        ----------
            widget (QWidget): The widget to add.
        '''
        self.content_layout.addWidget(widget)

    def addLayout(self, layout):
        '''
        Add a layout to the content area.

        Parameters
        ----------
            layout (QLayout): The layout to add.
        '''
        self.content_layout.addLayout(layout)