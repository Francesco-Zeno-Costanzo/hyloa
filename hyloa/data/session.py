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
Code to save a session (i.e. alla dta loaded all plot crated and so on) in .pkl files
"""
import os
import pickle
import logging

from PyQt5.QtCore import QTimer

from PyQt5.QtWidgets import (
    QMdiSubWindow, QMessageBox, QFileDialog
)

from hyloa.utils.logging_setup import setup_logging

from hyloa.gui.plot_window import PlotSubWindow
from hyloa.gui.plot_window import PlotControlWidget
from hyloa.gui.worksheet import WorksheetWindow

def save_current_session(app_instance, parent_widget=None):
    '''
    Save the current session to a .pkl file.

    Parameters
    ----------
    app_instance : MainApp
        Main application instance containing the session data.
    parent_widget : QWidget or None
        Optional parent for the dialog windows.
    '''
    if app_instance.logger is None:
        QMessageBox.critical(parent_widget, "Error", "Cannot start analysis without starting log.")
        return

    file_path, _ = QFileDialog.getSaveFileName(
        parent_widget,
        "Save session",
        "",
        "Pickle Files (*.pkl)"
    )

    if not file_path:
        QMessageBox.warning(parent_widget, "Warning", "No file selected for saving.")
        return

    try:
        # Build the dictionary for saving data 
        session_data = {
            "dataframes":   app_instance.dataframes,
            "header_lines": app_instance.header_lines,
            "logger_path":  app_instance.logger_path,
            "log_filename": os.path.basename(app_instance.logger_path),
            "fit_results":  app_instance.fit_results,
            "number_plots": app_instance.number_plots,

            "plot_widgets": {
                idx: {
                    "selected_pairs": [
                        (
                            f_combo.currentText(),
                            x_combo.currentText(),
                            y_combo.currentText()
                        )
                        for f_combo, x_combo, y_combo in widget.selected_pairs
                    ],
                    "plot_customizations": widget.plot_customizations.copy()
                }
                for idx, widget in app_instance.plot_widgets.items()
            },
            "plot_names": {
                idx : name for idx, name in app_instance.plot_names.items()
            },
            "control_windows_geometry": {
                idx: {
                    "x": sub.x(),
                    "y": sub.y(),
                    "width":  sub.width(),
                    "height": sub.height(),
                    "minimized": sub.isMinimized()
                }
                for idx, sub in app_instance.plot_subwindows.items()
            },
            "plot_windows_geometry": {
                idx: {
                    "x": fig_sub.x(),
                    "y": fig_sub.y(),
                    "width":  fig_sub.width(),
                    "height": fig_sub.height(),
                    "minimized": fig_sub.isMinimized()
                }
                for idx, fig_sub in app_instance.figure_subwindows.items()
            },
            "worksheets": {
                idx: {
                    "name":    app_instance.worksheet_names.get(idx, f"Worksheet {idx}"),
                    "content": app_instance.worksheet_windows[idx].to_session_data()
                }
                for idx in app_instance.worksheet_windows
            },

        }

        with open(file_path, "wb") as f:
            pickle.dump(session_data, f)

        QMessageBox.information(parent_widget, "Session saved",
                                f"Session saved in file:\n{file_path}")
    except Exception as e:
        QMessageBox.critical(parent_widget, "Error", f"Error while saving:\n{e}")


def load_previous_session(app_instance, parent_widget=None):
    '''
    Load a previously saved session from a .pkl file.

    Parameters
    ----------
    app_instance : MainApp
        Main application instance to load the session into.
    parent_widget : QWidget or None
        Optional parent for the dialog windows.
    '''
    options = QFileDialog.Options()
    file_path, _ = QFileDialog.getOpenFileName(
        parent_widget,
        "Load session",
        "",
        "Pickle Files (*.pkl)",
        options=options
    )

    if not file_path:
        QMessageBox.warning(parent_widget, "Error", "No file selected for session loading.")
        return

    try:
        with open(file_path, "rb") as f:
            session_data = pickle.load(f)

        # Reload attributes of main app instance
        app_instance.dataframes     = session_data.get("dataframes", [])
        app_instance.header_lines   = session_data.get("header_lines", [])
        app_instance.fit_results    = session_data.get("fit_results", {})
        app_instance.number_plots   = session_data.get("number_plots", 0)

        try :
            app_instance.logger_path = session_data.get("logger_path", None)
            # Recreate the logger
            setup_logging(app_instance.logger_path)
        except :

            log_filename = session_data.get("log_filename")
            # To ensure compatibility with different OS
            default_dir              = os.path.dirname(file_path)
            reconstructed_path       = os.path.join(default_dir, log_filename)
            app_instance.logger_path = reconstructed_path
            # Recreate the logger
            setup_logging(app_instance.logger_path)

        
        app_instance.logger = logging.getLogger(__name__)
        app_instance.logger.info("Logger restored from session file.")

        app_instance.open_default_panels()

        # Recreate all plot's control panels
        plot_widgets_data = session_data.get("plot_widgets", {})
        plot_names_data   = session_data.get("plot_names",   {}) 
        
        # Loop only over widget because widgets and names share the same keys
        for idx_str, plot_info in plot_widgets_data.items():
            
            idx       = int(idx_str)
            plot_name = plot_names_data.get(idx, f"Graph {idx}")

            widget = PlotControlWidget(app_instance, idx, plot_name)
            
            for i in reversed(range(widget.pair_layout.count())):
                widget.pair_layout.itemAt(i).widget().setParent(None)
            widget.selected_pairs.clear()

            app_instance.plot_widgets[idx] = widget
            app_instance.plot_names[idx]   = plot_name

            # Retrieve selected pairs ...
            for file_str, x_str, y_str in plot_info.get("selected_pairs", []):
                widget.add_pair(file_text=file_str, x_col=x_str, y_col=y_str)

            # ... and customization
            widget.plot_customizations = plot_info.get("plot_customizations", {})

            # Create sub window for panel
            sub = PlotSubWindow(app_instance, widget, idx)
            app_instance.mdi_area.addSubWindow(sub)
            sub.show()

            # Restore size and position for control panels...
            ctrl_geom = session_data.get("control_windows_geometry", {}).get(idx)
            if ctrl_geom:
                sub.setGeometry(ctrl_geom["x"], ctrl_geom["y"], ctrl_geom["width"], ctrl_geom["height"])
                if ctrl_geom.get("minimized"):
                    sub.showMinimized()
            
            app_instance.plot_subwindows[idx] = sub

            widget.plot() # Force the plot
            # ... and for plot windows
            fig_geom = session_data.get("plot_windows_geometry", {}).get(idx)
            fig_sub  = app_instance.figure_subwindows.get(idx)
            if fig_geom and fig_sub:
                fig_sub.setGeometry(fig_geom["x"], fig_geom["y"], fig_geom["width"], fig_geom["height"])
                if fig_geom.get("minimized"):
                    fig_sub.showMinimized()

        # --- restore worksheets  ---
        worksheet_data = session_data.get("worksheets", {})
        for idx_key, ws_info in worksheet_data.items():
            try:
                idx = int(idx_key)
            except:
                idx = idx_key

            ws_name = ws_info.get("name", f"Worksheet {idx}")

            # create worksheet instance with name
            ws = WorksheetWindow(app_instance.mdi_area, name=ws_name)

            # add to mdi area BEFORE restoring content (important!)
            app_instance.mdi_area.addSubWindow(ws)

            # restore content & plots; from_session_data will set geometry and schedule show
            ws.from_session_data(ws_info.get("content", {}))

            # save references in app_instance
            app_instance.worksheet_windows[idx]    = ws
            app_instance.worksheet_names[idx]      = ws_name
            app_instance.worksheet_subwindows[idx] = ws

            # ensure it's visible (from_session_data schedules showNormal/showMinimized)
            QTimer.singleShot(0, lambda w=ws: w.show())


        # Rename main window to reflect the loaded session
        base_name = os.path.basename(file_path)
        name, _   = os.path.splitext(base_name)
        app_instance.setWindowTitle(f"HYLOA - {name}")
            
        QMessageBox.information(parent_widget, "Session Loaded",
                                f"Session loaded from file:\n{file_path}")

    except Exception as e:
        QMessageBox.critical(parent_widget, "Error",
                             f"Error while loading session:\n{e}")