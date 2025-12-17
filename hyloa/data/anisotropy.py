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

import numpy as np
from scipy.interpolate import splrep, BSpline
from scipy.interpolate import InterpolatedUnivariateSpline

from PyQt5.QtWidgets import QMessageBox

from hyloa.utils.err_format import format_value_error


def compute_b_spline(file_combo, x_up_combo, y_up_combo, x_down_combo, y_down_combo,
                     smooth_up_edit, smooth_dw_edit,
                     plot_state, logger, window, draw_plot):
    
    '''
    Compute cubic B-spline interpolations for the corrected hysteresis loop branches.

    This function applies a cubic B-spline interpolation separately to the
    corrected up and down branches of a hysteresis loop. The spline is computed
    using the corrected data stored in plot_state and is intended as a smooth
    representation of the loop after tilt/drift correction.

    The spline can only be computed after the correction step has been performed,
    since it operates on the corrected arrays (x_up_corr, y_up_corr,
    x_dw_corr, y_dw_corr). The resulting splines are stored in plot_state
    and immediately visualized via the provided plotting callback.

    For numerical stability and consistency with SciPy requirements, the data
    are internally sorted to ensure a strictly monotonic x-axis. Duplicate x
    values are explicitly checked and rejected, as they would invalidate the
    spline computation.

    Parameters
    ----------
    file_combo : QComboBox
        Combo box used to select the source data file (used for logging purposes).
    x_up_combo, y_up_combo : QComboBox
        Combo boxes selecting the x and y columns corresponding to the up branch.
    x_down_combo, y_down_combo : QComboBox
        Combo boxes selecting the x and y columns corresponding to the down branch.
    smooth_up_edit : QLineEdit
        Input field specifying the smoothing parameter s for the up branch spline.
        Must be a non-negative float.
    smooth_dw_edit : QLineEdit
        Input field specifying the smoothing parameter s for the down branch spline.
        Must be a non-negative float.
    plot_state : dict
        Dictionary storing the current plotting state.
    logger : logging.Logger
        Logger instance used to record spline computation details.
    window : QWidget
        Parent widget used to display error message boxes.
    draw_plot : callable
        Callback function responsible for redrawing the plot after the spline
        computation.

    Notes
    -----
    - The spline is computed using scipy.interpolate.splrep and evaluated
      on a dense, uniformly spaced grid spanning the corrected x-range.
    - The spline represents the full corrected curve.
    '''
    
    try :

        idx_src  = file_combo.currentIndex()
        x_up_col = x_up_combo.currentText()
        y_up_col = y_up_combo.currentText()
        x_dw_col = x_down_combo.currentText()
        y_dw_col = y_down_combo.currentText()
    
        s_up = float(smooth_up_edit.text())
        s_dw = float(smooth_dw_edit.text())

        if s_up < 0 or s_dw < 0:
            QMessageBox.critical(window, "Error", "Smoothing parameter must be non-negative.")
            return

        x_up = plot_state["x_up_corr"]
        y_up = plot_state["y_up_corr"]
        x_dw = plot_state["x_dw_corr"]
        y_dw = plot_state["y_dw_corr"]
        e_up = plot_state["e_up"]
        e_dw = plot_state["e_dw"]

        if x_up is None:
            QMessageBox.critical(window, "Error", "Spline must be applied on corrected data.")
            return
        
        #=========================================================#
        # Up branch spline                                        #
        #=========================================================#

        # Ensure monotonic x
        idx = np.argsort(x_up)
        x_up, y_up = x_up[idx], y_up[idx]

        # Check duplicates
        if np.any(np.diff(x_up) == 0):
            QMessageBox.critical(window, "Error", "Duplicate x values detected in up branch.")
            return

        # Compute spline
        try:
            tck_up = splrep(x_up, y_up, s=s_up)
        except Exception as e:
            QMessageBox.critical(window, "Error", f"Spline fit up branch failed: {e}.")
            return
        
        try :
            x_dense_up = np.linspace(x_up.min(), x_up.max(), 5000)
            y_dense_up = BSpline(*tck_up)(x_dense_up)
        except Exception as e:
            QMessageBox.critical(window, "Error", f"Error in spline conputation for up branch: {e}.")
            return
        
        #=========================================================#
        # Dw branch spline                                        #
        #=========================================================#

        # Ensure monotonic x
        idx = np.argsort(x_dw)
        x_dw, y_dw = x_dw[idx], y_dw[idx]

        # Check duplicates
        if np.any(np.diff(x_dw) == 0):
            QMessageBox.critical(window, "Error", "Duplicate x values detected in dw branch.")
            return

        # Compute spline
        try:
            tck_dw = splrep(x_dw, y_dw, s=s_dw)
        except Exception as e:
            QMessageBox.critical(window, "Error", f"Spline fit dw branch failed: {e}.")
            return
        
        try :
            x_dense_dw = np.linspace(x_dw.min(), x_dw.max(), 5000)
            y_dense_dw = BSpline(*tck_dw)(x_dense_dw)
        except Exception as e:
            QMessageBox.critical(window, "Error", f"Error in spline conputation for dw branch: {e}.")
            return 

        plot_state.update({
            "fit_hc_p"  : None,
            "fit_hc_n"  : None,
            "done_spl3" : True,
            "spline_up" : (x_dense_up, y_dense_up),
            "spline_dw" : (x_dense_dw, y_dense_dw)
        })
        draw_plot()

        log_lines = []
        log_lines.append(f"Computed Bspline for data in file {idx_src + 1}, columns {x_up_col}/{y_up_col} and {x_dw_col}/{y_dw_col}.")
        log_lines.append(f"With smoting parameter {s_up} for up branch and {s_dw} for down branch.\n")
        logger.info(f"Bspline results" + "\n".join(log_lines))
    
    except Exception as e:
        QMessageBox.critical(window, "Error", f"Error during spline interpolation:\n{e}")
        return



def compute_Hk(file_combo, x_up_combo, y_up_combo, x_down_combo, y_down_combo,
               hk_thr_edit, plot_state, logger, window, output_box):
    
    '''
    Compute the anisotropy field Hk.

    This function estimates the anisotropy field using the cubic spline
    representations of the up and down branches previously computed.
    The method is based on the relative difference between the two branches:
    regions where the difference falls below a given threshold are used
    to identify the negative and positive anisotropy fields.

    The final anisotropy field is computed as the mean value between the
    negative and positive branches, with an associated uncertainty.

    Parameters
    ----------
    file_combo : QComboBox
        Combo box used to select the source data file.
    x_up_combo : QComboBox
        Combo box selecting the X column for the up branch.
    y_up_combo : QComboBox
        Combo box selecting the Y column for the up branch.
    x_down_combo : QComboBox
        Combo box selecting the X column for the down branch.
    y_down_combo : QComboBox
        Combo box selecting the Y column for the down branch.
    hk_thr_edit : QComboBox or QLineEdit
        Widget containing the threshold value used to select the region
        where the relative difference between up and down branches is below
        the chosen limit.
    plot_state : dict
        Dictionary storing the current plot state.
    logger : logging.Logger
        Logger instance used to record the computation results.
    window : QWidget
        Parent widget used to display error message boxes.
    output_box : QTextEdit
        Text box where the computed anisotropy field and related information
        are displayed.

    Notes
    -----
    This function requires that the cubic splines for both branches have
    already been computed. If the spline data are not available, the
    computation will fail.
    '''
    
    try :
        idx_src  = file_combo.currentIndex()
        x_up_col = x_up_combo.currentText()
        y_up_col = y_up_combo.currentText()
        x_dw_col = x_down_combo.currentText()
        y_dw_col = y_down_combo.currentText()

        x_up, y_up = plot_state["spline_up"]
        x_dw, y_dw = plot_state["spline_dw"] 
        
    
        diff  = abs( (y_up - y_dw)/y_up )
        field = x_up
        thr_y = np.where(diff == np.max(diff))[0][0]

        thr = float(hk_thr_edit.text())

        pts     = np.where(diff < thr)[0]
        field_a = field[pts] 

        field_n = field_a[field_a < field[thr_y]]
        field_p = field_a[field_a > field[thr_y]]

        field_p = np.sort(field_p)
        field_n = np.sort(field_n)

        Hk_1 = field_n.max()
        Hk_2 = field_p.min()
        
        Hk = 0.5*(-Hk_1 + Hk_2)
        dH = abs(0.5*( Hk_1 + Hk_2))

        results_text_lines = []
        results_text_lines.append(f"Negative anisotropy field: {Hk_1}")
        results_text_lines.append(f"Positive anisotropy field: {Hk_2}")
        results_text_lines.append(f"Mean: {format_value_error(Hk, dH)}")
        
        output_box.setPlainText("\n".join(results_text_lines))
        
        log_lines = []
        log_lines.append(f"Computed anisotropy field for data in file {idx_src + 1}, columns {x_up_col}/{y_up_col} and {x_dw_col}/{y_dw_col}.")
        
        logger.info("\n".join(log_lines) +"\n".join(results_text_lines))
      
    
    except Exception as e:
        QMessageBox.critical(window, "Error", f"Error during anisotropy field calculation:\n{e}")

def symmetrize(file_combo, save_file_combo,
               x_up_combo, y_up_combo, x_down_combo, y_down_combo,
               x_up_dest,  y_up_dest,  x_dw_dest,    y_dw_dest,
               dataframes, logger, plot_state, draw_plot,
               window):
    '''
    Symmetrize a hysteresis loop using spline-interpolated up and down branches.

    This function performs a symmetrization of the hysteresis loop starting
    from the cubic spline representations of the corrected up and down
    branches. The symmetrized loop is constructed by averaging the field
    values and antisymmetrizing the magnetization, enforcing physical
    symmetry conditions.

    A linear spline is built from the averaged data and evaluated on the
    original corrected field arrays. A small random noise, estimated from
    the data, is added to mimic experimental uncertainty.

    Optionally, the symmetrized data can be saved into a user-selected
    destination data file.

    Parameters
    ----------
    file_combo : QComboBox
        Combo box used to select the source data file.
    save_file_combo : QComboBox
        Combo box used to select the destination file for saving the
        symmetrized data. If set to "No save", the data are not written.
    x_up_combo : QComboBox
        Combo box selecting the X column for the up branch.
    y_up_combo : QComboBox
        Combo box selecting the Y column for the up branch.
    x_down_combo : QComboBox
        Combo box selecting the X column for the down branch.
    y_down_combo : QComboBox
        Combo box selecting the Y column for the down branch.
    x_up_dest : QComboBox
        Combo box selecting the destination X column for the symmetrized
        up branch.
    y_up_dest : QComboBox
        Combo box selecting the destination Y column for the symmetrized
        up branch.
    x_dw_dest : QComboBox
        Combo box selecting the destination X column for the symmetrized
        down branch.
    y_dw_dest : QComboBox
        Combo box selecting the destination Y column for the symmetrized
        down branch.
    dataframes : list of pandas.DataFrame
        List of dataframes loaded in the application.
    logger : logging.Logger
        Logger instance used to record spline computation details.
    plot_state : dict
        Dictionary storing the current plotting state.
    draw_plot : callable
        Callback function responsible for redrawing the plot.
    window : QWidget
        Parent widget used to display error message boxes.

    Notes
    -----
    This function requires that both the drift correction and spline
    interpolation steps have already been completed.
    '''
    try :
        idx_src  = file_combo.currentIndex()
        x_up_col = x_up_combo.currentText()
        y_up_col = y_up_combo.currentText()
        x_dw_col = x_down_combo.currentText()
        y_dw_col = y_down_combo.currentText()

        save_choice  = save_file_combo.currentIndex()  # 0 = No save, >0 => file index adjust
        
        if save_choice == 0:
            save_idx = None
        else:
            # save_file_combo items: ["No save", "File 1", "File 2"...]
            save_idx = save_choice - 1

        x_up, y_up = plot_state["spline_up"]
        x_dw, y_dw = plot_state["spline_dw"] 
        
        x_data_up = plot_state["x_up_corr"]
        x_data_dw = plot_state["x_dw_corr"]

        dy_data_err = np.std(plot_state["y_dw_corr"][0:25])

        x_mean = (x_up + x_dw)/2
        y_mean = (y_up - y_dw[::-1])/2

        spl = InterpolatedUnivariateSpline(x_mean, y_mean, k=1)

        dy_err = (2*np.random.random(x_data_up.size) - 1) * dy_data_err

        x_new_up, x_new_dw = x_data_up, -x_data_dw 
        y_new_up, y_new_dw = spl(x_data_up) + dy_err, -spl(x_data_dw) + dy_err

        plot_state.update({
            "s_data_up" : (x_new_up, y_new_up),
            "s_data_dw" : (x_new_dw, y_new_dw)
        })
        draw_plot()


        log_lines = []
        log_lines.append(f"Symmetrizied loop in file {idx_src + 1}, columns {x_up_col}/{y_up_col} and {x_dw_col}/{y_dw_col}.")
        
        logger.info("\n".join(log_lines))

        # Save corrected columns if requested
        if save_idx is not None:
            df_dest = dataframes[save_idx]

            df_dest[x_up_dest.currentText()] = x_new_up
            df_dest[y_up_dest.currentText()] = y_new_up
            
            df_dest[x_dw_dest.currentText()] = x_new_dw
            df_dest[y_dw_dest.currentText()] = y_new_dw

            logger.info("Corrected columns saved to destination file.")
      
    
    except Exception as e:
        QMessageBox.critical(window, "Error", f"Error symmetrization:\n{e}")
