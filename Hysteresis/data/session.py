import pickle
import logging
import matplotlib.pyplot as plt
from tkinter import messagebox, filedialog
from Hysteresis.utils.logging_setup import setup_logging

def save_current_session(app_instance):

    if app_instance.logger is None:
        messagebox.showerror("Errore", "Impossibile iniziare l'analisi senza avviare il log")
        return
    
    # Open the dialog box to choose the file path
    save_file = filedialog.asksaveasfilename(
        defaultextension=".pkl",
        filetypes=[("pickle Files", "*.pkl")],
    )


    sessione = {
        "dataframes":          app_instance.dataframes,
        "count_plot":          app_instance.count_plot,
        "header_lines":        app_instance.header_lines,
        "plot_customizations": app_instance.plot_customizations,
        "logger_path":         app_instance.logger_path,
        "fit_results":         app_instance.fit_results,
        "figures"    :         app_instance.list_figures,
    }
    
    if save_file:
        with open(save_file, "wb") as f:
            pickle.dump(sessione, f)

        messagebox.showinfo("Sessione Salvata", f"Sessione salvata nel file: {save_file}")
        plt.close("all")
    
    else :
        messagebox.showerror("Errore", "Per favore seleziona un file valido per il salvataggio della sessione.")
        


def load_previous_session(app_instance):
    
    load_file = filedialog.askopenfilename(
        defaultextension=".pkl",
        filetypes=[("pickle Files", "*.pkl")],
    )

    if not load_file:
        messagebox.showerror("Errore", "Nessun file selezionato per il caricamento della sessione.")
        return

    try:
        with open(load_file, "rb") as f:
            sessione = pickle.load(f)

        
        app_instance.dataframes          = sessione.get("dataframes", [])
        app_instance.count_plot          = sessione.get("count_plot", 0)
        app_instance.header_lines        = sessione.get("header_lines", 0)
        app_instance.plot_customizations = sessione.get("plot_customizations", {})
        app_instance.logger_path         = sessione.get("logger_path", None)
        app_instance.fit_results         = sessione.get("fit_results", {})
        F = sessione.get("figures", [])

        messagebox.showinfo("Sessione Caricata", f"Sessione caricata dal file: {load_file}")

        # Reconfigure logging if a logger path is provided        
        setup_logging(app_instance.logger_path)
        app_instance.logger = logging.getLogger(__name__)
        app_instance.logger.info("Logger ripristinato da file di sessione.")

        if F: plt.show()


    except Exception as e:
        messagebox.showerror("Errore", f"Errore durante il caricamento della sessione:\n{e}")
