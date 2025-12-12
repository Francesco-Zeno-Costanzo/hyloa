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
Code with basic routines to correct some loop distortions
"""

import numpy as np
from scipy.optimize import curve_fit
from PyQt5.QtWidgets import QMessageBox

from hyloa.utils.err_format import format_value_error

#================================================#
# Function to chek simmetry by flipping a branch #
#================================================#

def change_ps(plot_state, window, draw_plot):
    '''
    Function to change the plot status deleting the corrected data

    Parameters
    ----------
    plot_state : dict
        dictionary of the plotted data
    window : QWidget
        The main window widget.
    draw_plot : callable
        Function to update the preview
    '''

    try:
        plot_state.update({
            "done_corr": False,
            "x_up_corr": None,
            "y_up_corr": None,
            "e_up"     : None,
            "x_dw_corr": None,
            "y_dw_corr": None,
            "e_dw"     : None,
            "fit_hc_p" : None,
            "fit_hc_n" : None
        })
        draw_plot()

    except Exception as e:
        QMessageBox.critical(window, "Error", f"Error during flip:\n{e}")

#================================================#
# Function to chek simmetry by flipping a branch #
#================================================#

def flip(plot_state, window, draw_plot):
    '''
    Function to flip a brach to ensure simmetricity of the loop.

    Parameters
    ----------
    plot_state : dict
        dictionary of the plotted data
    window : QWidget
        The main window widget.
    draw_plot : callable
        Function to update the preview
    '''
    try:
        plot_state["flipped"] = not plot_state["flipped"]
        draw_plot()

    except Exception as e:
        QMessageBox.critical(window, "Error", f"Error during flip:\n{e}")

#================================================#
# Function to correct field                      #
#================================================#

def apply_shift(field_shift_pc_edit, plot_state, window, fit_data, args=()):
    '''
    Function add a field shift after the corrections

    Parameters
    ----------
    field_shift_pc_edit : QLineEdit
        Value for field shifting
    window : QWidget
        The main window widget.
    plot_state : dict
        dictionary of the plotted data
    fit_data : callable
        Function for fitting data
    args : tuple
        Argumets to pass to fit_data
    '''
    try:

        field_shift = float(field_shift_pc_edit.text())
        plot_state["x_up_corr"] -= field_shift
        plot_state["x_dw_corr"] -= field_shift

        fit_data(*args)

    except Exception as e:
        QMessageBox.critical(window, "Error", f"Error applying shift:\n{e}")


#================================================#
# MAIN CORRECTION FUNCTION                       #
#================================================#

def perform_correction(file_combo, save_file_combo,
                       x_up_combo, y_up_combo, x_down_combo, y_down_combo,
                       field_shift_edit, field_scale_edit,
                       x_start_n_edit, x_end_n_edit, x_start_p_edit, x_end_p_edit,
                       tail_params_edit, tail_function_edit,
                       x_up_dest, y_up_dest, x_dw_dest, y_dw_dest,
                       dataframes, logger, plot_state, draw_plot,
                       window):
    ''' 
    Perform the loop correction using the parameters from the UI.
    The correction involves fitting the saturation parts (tails) of the hystersis loop
    to remove drifts.

    Parameters
    ----------
    file_combo : QComboBox
        Combo box to select source data file.
    save_file_combo : QComboBox
        Combo box to select destination data file.
    x_up_combo : QComboBox
        Combo box to select X column for Up branch.
    y_up_combo : QComboBox
        Combo box to select Y column for Up branch.
    x_down_combo : QComboBox
        Combo box to select X column for Down branch.
    y_down_combo : QComboBox
        Combo box to select Y column for Down branch.
    field_shift_edit : QLineEdit
        Line edit for field shift value.
    field_scale_edit : QLineEdit
        Line edit for field scale value.
    x_start_n_edit : QLineEdit
        Line edit for negative tail start limit.
    x_end_n_edit : QLineEdit
        Line edit for negative tail end limit.
    x_start_p_edit : QLineEdit
        Line edit for positive tail start limit.
    x_end_p_edit : QLineEdit
        Line edit for positive tail end limit.
    tail_params_edit : QLineEdit
        Line edit for tail fit parameter names.
    tail_function_edit : QLineEdit
        Line edit for tail fit function.
    x_up_dest : QComboBox
        Combo box to select X column in which to store the correct up branch.
    y_up_dest : QComboBox
        Combo box to select Y column in which to store the correct up branch.
    x_dw_dest : QComboBox
        Combo box to select X column in which to store the correct down branch.
    y_dw_dest : QComboBox
        Combo box to select Y column in which to store the correct down branch.
    dataframes : list of pd.DataFrame
        List of dataframes containing loaded data.
    logger : Logger
        Logger of the application.
    plot_state : dict
        dictionary of the plotted data
    draw_plot : callable
        Function to update the preview
    output_box : QTextEdit
        Text edit for displaying output results.
    window : QWidget
        The main window widget.
    '''
    try:
        idx_src      = file_combo.currentIndex()
        df_src       = dataframes[idx_src].copy()      # working copy
        save_choice  = save_file_combo.currentIndex()  # 0 = No save, >0 => file index adjust
        
        if save_choice == 0:
            save_idx = None
        else:
            # save_file_combo items: ["No save", "File 1", "File 2"...]
            save_idx = save_choice - 1

        # Read field shift/scale
        field_shift = float(field_shift_edit.text())
        field_scale = float(field_scale_edit.text())

        # Read x/y column names
        x_up_col = x_up_combo.currentText()
        y_up_col = y_up_combo.currentText()
        x_dw_col = x_down_combo.currentText()
        y_dw_col = y_down_combo.currentText()
        
        # Prepare arrays: apply shift and scale
        x_up = np.copy(df_src[x_up_col].astype(float).values) - field_shift
        x_up = x_up * field_scale
        y_up = np.copy(df_src[y_up_col].astype(float).values)
        x_dw = np.copy(df_src[x_dw_col].astype(float).values) - field_shift
        x_dw = x_dw * field_scale
        y_dw = np.copy(df_src[y_dw_col].astype(float).values)

        # Read tail ranges
        try:
            x_n_start = float(x_start_n_edit.text()) * field_scale # For up negative region
            x_n_end   = float(x_end_n_edit.text()) * field_scale
        except Exception:
            # fallback
            x_n_start, x_n_end = -4000,  -1000

        try:
            x_p_start = float(x_start_p_edit.text()) * field_scale # For up positive region
            x_p_end   = float(x_end_p_edit.text()) * field_scale 
        except Exception:
            x_p_start, x_p_end = 1000, 4000

        # Masks for up/down tails split by sign
        mask_n_up = (x_up >= x_n_start) & (x_up <= x_n_end)
        mask_p_up = (x_up >= x_p_start) & (x_up <= x_p_end)
        mask_n_dw = (x_dw >= x_n_start) & (x_dw <= x_n_end)
        mask_p_dw = (x_dw >= x_p_start) & (x_dw <= x_p_end)
        
        #=========================================#
        # Auxiliary functions for fitting         #
        #=========================================#

        try:
            tail_param_names = [p.strip() for p in tail_params_edit.text().split(",") if p.strip() != ""]
            func_code_tail   = f"lambda x, {', '.join(tail_param_names)}: {tail_function_edit.text()}"
            f_func           = eval(func_code_tail, {"np": np, "__builtins__": {}})
        
        except Exception as e:
            QMessageBox.critical(window, "Error", f"Invalid function for tail fit:\n{e}")
            return
        
        s2 = lambda x, y, f, popt: sum((y-f(x, *popt))**2)/(len(x)-len(popt))

        def poly_error(x, params, dparams):
            '''
            params: [a0, a1, a2, ...]
            dparams: relative uncertainties
            '''
            total = 0.0
            # Skip i=0 because a0 is the constant term
            for i in range(1, len(params)):
                total += ( (x**i) * dparams[i] )**2
            return np.sqrt(total)

        #=========================================#

        # Fit linear tails (four fits)
        p_up_1, c_up_1 = curve_fit(f_func, x_up[mask_n_up], y_up[mask_n_up])
        p_up_2, c_up_2 = curve_fit(f_func, x_up[mask_p_up], y_up[mask_p_up])
        p_dw_1, c_dw_1 = curve_fit(f_func, x_dw[mask_n_dw], y_dw[mask_n_dw])
        p_dw_2, c_dw_2 = curve_fit(f_func, x_dw[mask_p_dw], y_dw[mask_p_dw])

        # Parameter errors
        dp_up_1 = np.sqrt(np.diag(c_up_1))
        dp_up_2 = np.sqrt(np.diag(c_up_2))
        dp_dw_1 = np.sqrt(np.diag(c_dw_1))
        dp_dw_2 = np.sqrt(np.diag(c_dw_2))

        # Model dispersion error
        e_up_1 = s2(x_up[mask_n_up], y_up[mask_n_up], f_func, p_up_1)
        e_up_2 = s2(x_up[mask_p_up], y_up[mask_p_up], f_func, p_up_2)
        e_dw_1 = s2(x_dw[mask_n_dw], y_dw[mask_n_dw], f_func, p_dw_1)
        e_dw_2 = s2(x_dw[mask_p_dw], y_dw[mask_p_dw], f_func, p_dw_2)

        e_up = (e_up_1 + e_up_2) * 0.5
        e_dw = (e_dw_1 + e_dw_2) * 0.5

        # Corrections
        corr_up = np.where(
            x_up < 0,
            f_func(x_up, *p_up_1) - p_up_1[0],
            f_func(x_up, *p_up_2) - p_up_2[0]
        )

        corr_dw = np.where(
            x_dw < 0,
            f_func(x_dw, *p_dw_1) - p_dw_1[0],
            f_func(x_dw, *p_dw_2) - p_dw_2[0]
        )
        
        d_corr_up = np.where(
            x_up < 0,
            poly_error(x_up, p_up_1, dp_up_1),
            poly_error(x_up, p_up_2, dp_up_2)
        )

        d_corr_dw = np.where(
            x_dw < 0,
            poly_error(x_dw, p_dw_1, dp_dw_1),
            poly_error(x_dw, p_dw_2, dp_dw_2)
        )

        # Total error = dispersion + abs(d_corr)
        e_up = e_up + np.abs(d_corr_up)
        e_dw = e_dw + np.abs(d_corr_dw)

        # Apply correction to data
        y_up_corr = y_up - corr_up
        y_dw_corr = y_dw - corr_dw

        def close_fun(up_arr, q1, q2):
            ''' Close the loop using intercepts q1 and q2
            '''
            up_c  = np.copy(up_arr) - q1
            up_c *= 2/(abs(q2)+abs(q1))
            up_c  = up_c + q1/abs(q1) #- 1 if q1 < 0 else + 1
            return up_c

        # Apply close operation using intercepts q = intercept of negative and positive tail fits
        y_up_closed = close_fun(y_up_corr, p_up_1[0], p_up_2[0])
        y_dw_closed = close_fun(y_dw_corr, p_dw_1[0], p_dw_2[0])

        plot_state.update({
            "done_corr": True,
            "x_up_corr": x_up,
            "y_up_corr": y_up_closed,
            "e_up"     : e_up,
            "x_dw_corr": x_dw,
            "y_dw_corr": y_dw_closed,
            "e_dw"     : e_dw,
        })
        draw_plot()

        # Summary of results
        log_results_lines = []
        log_results_lines.append(f"Summary of correction for data in file {idx_src + 1}, columns {x_up_col}/{y_up_col} and {x_dw_col}/{y_dw_col}:")
        log_results_lines.append(f"Corrected data with field shift = {field_shift} and scale = {field_scale}")
        log_results_lines.append(f"Using tail fit function: {tail_function_edit.text()}")
        log_results_lines.append(f"Using range limits (neg): {x_n_start/field_scale} to {x_n_end/field_scale}")
        log_results_lines.append(f"Using range limits (pos): {x_p_start/field_scale} to {x_p_end/field_scale}\n")
        logger.info("Loop correction completed. Summary:\n" + "\n".join(log_results_lines))

        # Save corrected columns if requested
        if save_idx is not None:
            df_dest = dataframes[save_idx]

            df_dest[x_up_dest.currentText()] = x_up
            df_dest[y_up_dest.currentText()] = y_up_closed

            df_dest[x_dw_dest.currentText()] = x_dw
            df_dest[y_dw_dest.currentText()] = y_dw_closed

            logger.info("Corrected columns saved to destination file.")

    except Exception as e:
        QMessageBox.critical(window, "Error", f"Error running fits: {e}")
        logger.exception("Unhandled error in perform_all_fits: %s", e) 
    

#===================================================================#
# Function to fit for physiscal quantities                          #
#===================================================================#       

def fit_data(file_combo,
             x_up_combo, y_up_combo, x_down_combo, y_down_combo,
             x_start_up_hc_edit, x_end_up_hc_edit, x_start_dw_hc_edit, x_end_dw_hc_edit,
             hc_params_edit, hc_function_edit, logger, plot_state, draw_plot,
             output_box, window):
    '''
    Parameters
    ----------
    file_combo : QComboBox
        Combo box to select source data file.
    x_up_combo : QComboBox
        Combo box to select X column for Up branch.
    y_up_combo : QComboBox
        Combo box to select Y column for Up branch.
    x_down_combo : QComboBox
        Combo box to select X column for Down branch.
    y_down_combo : QComboBox
        Combo box to select Y column for Down branch.
    x_start_up_hc_edit : QLineEdit
        Line edit for Up branch coercive fit start limit.
    x_end_up_hc_edit : QLineEdit
        Line edit for Up branch coercive fit end limit.
    x_start_dw_hc_edit : QLineEdit
        Line edit for Down branch coercive fit start limit.
    x_end_dw_hc_edit : QLineEdit
        Line edit for Down branch coercive fit end limit.
    hc_params_edit : QLineEdit
        Line edit for coercive fit parameter names.
    hc_function_edit : QLineEdit
        Line edit for coercive fit function.
    logger : Logger
        Logger of the application.
    plot_state : dict
        dictionary of the plotted data
    draw_plot : callable
        Function to update the preview
    output_box : QTextEdit
        Text edit for displaying output results.
    window : QWidget
        The main window widget.
    '''
    try : 
        idx_src = file_combo.currentIndex()
    
        # Read x/y column names
        x_up_col = x_up_combo.currentText()
        y_up_col = y_up_combo.currentText()
        x_dw_col = x_down_combo.currentText()
        y_dw_col = y_down_combo.currentText()

        #Read data
        x_up = plot_state["x_up_corr"]
        y_up = plot_state["y_up_corr"]
        x_dw = plot_state["x_dw_corr"]
        y_dw = plot_state["y_dw_corr"]
        e_up = plot_state["e_up"]
        e_dw = plot_state["e_dw"]
        
        if e_up is None:
            QMessageBox.critical(window, "Error", f"You need to correct data first")
            return

        
        results_text_lines =  []
        try:
            hc_param_names = [p.strip() for p in hc_params_edit.text().split(",") if p.strip() != ""]
            func_code_hc   = f"lambda x, {', '.join(hc_param_names)}: {hc_function_edit.text()}"
            g_func         = eval(func_code_hc, {"np": np, "__builtins__": {}})
        
        except Exception as e:
            QMessageBox.critical(window, "Error", f"Invalid function for coercive fit:\n{e}")
            return
        
        # Fit coercivity
        try:
            x_n_start_hc = float(x_start_dw_hc_edit.text())
            x_n_end_hc   = float(x_end_dw_hc_edit.text())
            x_p_start_hc = float(x_start_up_hc_edit.text())
            x_p_end_hc   = float(x_end_up_hc_edit.text())
        except Exception as e:
            QMessageBox.critical(window, "Error", f"Invalid value for Hc range:\n{e}")
            return
        
        mask_n = (x_dw >= x_n_start_hc) & (x_dw <= x_n_end_hc)
        mask_p = (x_up >= x_p_start_hc) & (x_up <= x_p_end_hc)

        if mask_n.sum() < 2 or mask_p.sum() < 2:
            QMessageBox.critical(window, "Error", "Not enough points in coercive fit ranges.")
            return
        else :
            # Perform weighted fits
            popt_n, covm_n = curve_fit(g_func, x_dw[mask_n], y_dw[mask_n], sigma=e_dw[mask_n])
            popt_p, covm_p = curve_fit(g_func, x_up[mask_p], y_up[mask_p], sigma=e_up[mask_p])

        
        t1 = np.linspace(x_n_start_hc, x_n_end_hc, 400)
        t2 = np.linspace(x_p_start_hc, x_p_end_hc, 400)

        plot_state.update({
            "fit_hc_p" : (t1, g_func(t1, *popt_n)),
            "fit_hc_n" : (t2, g_func(t2, *popt_p))
        })
        draw_plot()

        # Store numerical results
        results_text_lines.append("Coercive fit results:")
        for p, val, err in zip(hc_param_names, popt_n, np.sqrt(np.diag(covm_n))):
            results_text_lines.append(f"{p} = {format_value_error(val, err)}")    
            
        for i , pi in zip(range(len(popt_n)), hc_param_names):
            for j , pj in zip(range(i+1, len(popt_n)), hc_param_names[i+1:]):
                corr_ij = covm_n[i, j]/np.sqrt(covm_n[i, i]*covm_n[j, j])
                results_text_lines.append(f"corr({pi}, {pj}) = {corr_ij:.3f}")
        
        for p, val, err in zip(hc_param_names, popt_p, np.sqrt(np.diag(covm_p))):
            results_text_lines.append(f"{p} = {format_value_error(val, err)}")    
            
        for i , pi in zip(range(len(popt_p)), hc_param_names):
            for j , pj in zip(range(i+1, len(popt_p)), hc_param_names[i+1:]):
                corr_ij = covm_n[i, j]/np.sqrt(covm_p[i, i]*covm_p[j, j])
                results_text_lines.append(f"corr({pi}, {pj}) = {corr_ij:.3f}")

        # Show textual results
        output_box.setPlainText("\n".join(results_text_lines))

        # Summary of results
        log_results_lines = []
        log_results_lines.append(f"Summary of fit for data in file {idx_src + 1}, columns {x_up_col}/{y_up_col} and {x_dw_col}/{y_dw_col}:")
        log_results_lines.append(f"Using fit function: {hc_function_edit.text()}")
        log_results_lines.append(f"Using fit ranges (down): {x_n_start_hc} to {x_n_end_hc}")
        log_results_lines.append(f"Using fit ranges (up): {x_p_start_hc} to {x_p_end_hc}\n")
        logger.info("Fit completed. Summary:\n" + "\n".join(log_results_lines) +"\n".join(results_text_lines))
    
    except Exception as e:
        QMessageBox.critical(window, "Error", f"Error during fitting:\n{e}")
        return

