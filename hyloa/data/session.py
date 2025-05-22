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
import pickle
import logging

from PyQt5.QtWidgets import (
    QMdiSubWindow, QMessageBox, QFileDialog
)

from hyloa.utils.logging_setup import setup_logging

from hyloa.gui.plot_window import PlotSubWindow
from hyloa.gui.plot_window import PlotControlWidget

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
        QMessageBox.critical(parent_widget, "Errore", "Impossibile iniziare l'analisi senza avviare il log.")
        return

    file_path, _ = QFileDialog.getSaveFileName(
        parent_widget,
        "Salva sessione",
        "",
        "Pickle Files (*.pkl)"
    )

    if not file_path:
        QMessageBox.warning(parent_widget, "Attenzione", "Nessun file selezionato per il salvataggio.")
        return

    try:
        # Build the dictionary for saving data 
        session_data = {
            "dataframes": app_instance.dataframes,
            "header_lines": app_instance.header_lines,
            "logger_path": app_instance.logger_path,
            "fit_results": app_instance.fit_results,
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
            }
        }

        with open(file_path, "wb") as f:
            pickle.dump(session_data, f)

        QMessageBox.information(parent_widget, "Sessione Salvata",
                                f"Sessione salvata nel file:\n{file_path}")
    except Exception as e:
        QMessageBox.critical(parent_widget, "Errore", f"Errore durante il salvataggio:\n{e}")


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
        "Carica sessione",
        "",
        "Pickle Files (*.pkl)",
        options=options
    )

    if not file_path:
        QMessageBox.warning(parent_widget, "Errore", "Nessun file selezionato per il caricamento della sessione.")
        return

    try:
        with open(file_path, "rb") as f:
            session_data = pickle.load(f)

        # Reload attributes of main app instance
        app_instance.dataframes     = session_data.get("dataframes", [])
        app_instance.header_lines   = session_data.get("header_lines", [])
        app_instance.logger_path    = session_data.get("logger_path", None)
        app_instance.fit_results    = session_data.get("fit_results", {})
        app_instance.number_plots   = session_data.get("number_plots", 0)

        # Recreate the logger
        setup_logging(app_instance.logger_path)
        app_instance.logger = logging.getLogger(__name__)
        app_instance.logger.info("Logger ripristinato da file di sessione.")

        app_instance.open_default_panels()

        # Recreate all plot's control panels
        plot_widgets_data = session_data.get("plot_widgets", {})
        plot_names_data   = session_data.get("plot_names",   {}) 
        
        # Loop only over widget because widgets and names share the same keys
        for idx_str, plot_info in plot_widgets_data.items():
            
            idx       = int(idx_str)
            plot_name = plot_names_data.get(idx, f"Grafico {idx}")

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

            # Force the plot
            widget.plot()

        QMessageBox.information(parent_widget, "Sessione Caricata",
                                f"Sessione caricata dal file:\n{file_path}")

    except Exception as e:
        QMessageBox.critical(parent_widget, "Errore",
                             f"Errore durante il caricamento della sessione:\n{e}")