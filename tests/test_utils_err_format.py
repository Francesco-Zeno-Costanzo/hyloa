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
test error print format
"""
import pytest
from hyloa.utils.err_format import format_value_error 


@pytest.mark.parametrize("val, err, expected", [
    
    (1.234598,   0.01631,    "1.23(2)"),
    (1234.523,   12.0,       "1235(12)"),
    (2.0,        0.3,        "2.0(3)"),
    (2.0,        0.05,       "2.00(5)"),
    (12300000.0, 340000.0,   "1.23(3)e7"),
    (5.6e-05,    1.2e-06,    "5.6(1)e-5"),
    (0.001234,   5.6e-05,    "1.23(6)e-3"),
    (2000,       150,        "2000(150)"),
    (2000,       3,          "2000(3)"),
    (0.983493,   0.00021341, "9.835(2)e-1"),
    (1e-8,       3e-9,       "1.0(3)e-8"),
    (9.876e7,    2.3e6,      "9.9(2)e7"),
    (2,          7423,       "2(7423)e0")
])

def test_format_value_error(val, err, expected):
    result = format_value_error(val, err)
    assert result == expected, f"Expected {expected}, got {result}"
