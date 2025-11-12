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
Code to ensure correct print format for error
"""
import numpy as np


def format_value_error(val, err):
    '''
    A function that returns the formatting of the measurement
    with error in the form: value(error). Therefore, the error
    refers to the last digit of the value.
    Only one significant digit for the error is displayed.
    If the error is smalle than 1e-3 or bigger 1e3 the scientific
    notation will be used.
    
    Parameters
    ----------
    val : float
        central values
    err : float
        error associated to val
    
    Return
    ------
    string

    Examples
    --------
    >>> print(format_value_error(1.234598, 0.01631)
    1.23(2)
    >>> print(format_value_error(1234.523, 12.0)
    1235(12)
    >>> print(format_value_error(12300000.0 ± 340000.0)
    1.23(3)e7
    >>> print(format_value_error(5.6e-05, 1.2e-06)
    5.6(1)e-5
    '''
    
    # Division between mantissa and exponent for error
    exp  = int(np.log10(err))
    mant = err / 10**exp

    # Scientific notation for error bigger than 1e3 and smoller than 1e-3
    if abs(exp) >= 3:
        # Division between mantissa and exponent for central value
        exp_val  = int(np.log10(abs(val)) if val != 0 else 0)
        scale    = 10**exp_val
        mant_val = val / scale

        # Ensures correct formatting
        if mant_val < 1:
            exp_val  -= 1
            scale    /= 10
            mant_val *= 10   

        elif mant_val >= 10:
            exp_val  += 1
            scale    *= 10
            mant_val /= 10

        # Sacle the error
        err_scaled = err / scale
        exp_err    = int(np.log10(err_scaled))
        mant_err   = err_scaled / 10**(exp_err)

        # Ensures correct formatting
        if mant_err < 1:
            exp_err  -= 1
            # Update mantissa will be correct but not necessary
        elif mant_err >= 10:
            exp_err  += 1

        # Number of significant digits to display
        sig_dig  = 1
        # Dacimal for rounding to sig_dig digits
        decimals = max(0, -exp_err -1 + sig_dig)

        err_int  = int(round(err_scaled * 10**decimals))
        mant_val = round(mant_val, decimals)
        val_str  = f"{mant_val:.{decimals}f}"

        return f"{val_str}({err_int})e{exp_val}"

    # Ensures correct formatting
    if mant < 1.0:
        exp  -= 1 
        # Update mantissa will be correct but not necessary
    elif mant >= 10.0:
        exp  += 1

    # Number of significant digits to display
    sig_dig = 1
    # Dacimal for rounding to sig_dig digits
    decimals = max(0, -exp - 1 + sig_dig)

    err_rounded = round(err, decimals)
    val_rounded = round(val, decimals)

    err_int = int(round(err_rounded * 10**decimals))
    val_str = f"{val_rounded:.{decimals}f}"

    return f"{val_str}({err_int})"