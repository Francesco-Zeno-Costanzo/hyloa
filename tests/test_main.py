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
Test entry point
"""
import time
import pytest
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

from hyloa.main import *


def test_splash_creation(qtbot):
    pixmap = QPixmap(100, 100)
    splash = Splash(pixmap)

    qtbot.addWidget(splash)

    assert splash.windowFlags() & Qt.FramelessWindowHint
    assert splash.progress.value() == 0


def test_progress_update(qtbot):
    pixmap = QPixmap(100, 100)
    splash = Splash(pixmap)

    qtbot.addWidget(splash)

    splash.set_progress(50)
    assert splash.progress.value() == 50

    splash.set_progress(100)
    assert splash.progress.value() == 100


def test_progress_format(qtbot):
    pixmap = QPixmap(100, 100)
    splash = Splash(pixmap)

    qtbot.addWidget(splash)

    assert splash.progress.isTextVisible()
    assert splash.progress.format() == "%p%"



def test_remaining_time_positive():
    start = time.monotonic()
    time.sleep(0.1)

    remaining = compute_remaining_time(start, 1.0)

    assert remaining > 0
    assert remaining <= 1000


def test_remaining_time_zero_when_expired():
    start = time.monotonic()
    time.sleep(0.2)

    remaining = compute_remaining_time(start, 0.1)

    assert remaining == 0
