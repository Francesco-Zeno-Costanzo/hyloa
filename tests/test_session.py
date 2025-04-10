import unittest
from unittest.mock import MagicMock, patch, mock_open
from Hysteresis.data.session import save_current_session, load_previous_session

class TestSessionFunctions(unittest.TestCase):

    def setUp(self):
        self.mock_app = MagicMock()
        self.mock_app.dataframes = ["data"]
        self.mock_app.count_plot = 1
        self.mock_app.header_lines = 2
        self.mock_app.plot_customizations = {"title": "grafico"}
        self.mock_app.logger_path = "log.txt"
        self.mock_app.fit_results = {"fit": "ok"}
        self.mock_app.logger = MagicMock()
        self.mock_app.list_figures = ["figure1", "figure2"]

    @patch("Hysteresis.data.session.filedialog.asksaveasfilename")
    @patch("Hysteresis.data.session.pickle.dump")
    @patch("Hysteresis.data.session.open", new_callable=mock_open)
    @patch("Hysteresis.data.session.messagebox.showinfo")
    def test_save_current_session_success(self, mock_info, mock_open_file, mock_pickle_dump, mock_save_dialog):
        mock_save_dialog.return_value = "session.pkl"
        
        save_current_session(self.mock_app)

        mock_open_file.assert_called_once_with("session.pkl", "wb")
        mock_pickle_dump.assert_called_once()
        mock_info.assert_called_once_with("Sessione Salvata", "Sessione salvata nel file: session.pkl")

    @patch("Hysteresis.data.session.messagebox.showerror")
    def test_save_current_session_no_logger(self, mock_error):
        self.mock_app.logger = None
        save_current_session(self.mock_app)
        mock_error.assert_called_once_with("Errore", "Impossibile iniziare l'analisi senza avviare il log")

    @patch("Hysteresis.data.session.filedialog.asksaveasfilename")
    @patch("Hysteresis.data.session.messagebox.showerror")
    def test_save_current_session_no_file(self, mock_error, mock_save_dialog):
        mock_save_dialog.return_value = ""
        save_current_session(self.mock_app)
        mock_error.assert_called_once_with("Errore", "Per favore seleziona un file valido per il salvataggio della sessione.")

    @patch("Hysteresis.data.session.filedialog.askopenfilename")
    @patch("Hysteresis.data.session.pickle.load")
    @patch("Hysteresis.data.session.open", new_callable=mock_open)
    @patch("Hysteresis.data.session.setup_logging")
    @patch("Hysteresis.data.session.logging.getLogger")
    @patch("Hysteresis.data.session.messagebox.showinfo")
    def test_load_previous_session_success(self, mock_info, mock_get_logger, mock_setup_logging, mock_open_file, mock_pickle_load, mock_open_dialog):
        mock_open_dialog.return_value = "session.pkl"
        mock_pickle_load.return_value = {
            "dataframes": ["data"],
            "count_plot": 1,
            "header_lines": 2,
            "plot_customizations": {"title": "grafico"},
            "logger_path": "log.txt",
            "fit_results": {"fit": "ok"},
            "figures": ["figure1", "figure2"]
        }
        mock_get_logger.return_value = MagicMock()

        load_previous_session(self.mock_app)

        self.assertEqual(self.mock_app.dataframes, ["data"])
        self.assertEqual(self.mock_app.count_plot, 1)
        self.assertEqual(self.mock_app.plot_customizations["title"], "grafico")
        mock_setup_logging.assert_called_once_with("log.txt")
        mock_info.assert_called_once_with("Sessione Caricata", "Sessione caricata dal file: session.pkl")

    @patch("Hysteresis.data.session.filedialog.askopenfilename")
    @patch("Hysteresis.data.session.messagebox.showerror")
    def test_load_previous_session_no_file(self, mock_error, mock_open_dialog):
        mock_open_dialog.return_value = ""
        load_previous_session(self.mock_app)
        mock_error.assert_called_once_with("Errore", "Nessun file selezionato per il caricamento della sessione.")

    @patch("Hysteresis.data.session.filedialog.askopenfilename")
    @patch("Hysteresis.data.session.open", side_effect=Exception("Errore fittizio"))
    @patch("Hysteresis.data.session.messagebox.showerror")
    def test_load_previous_session_exception(self, mock_error, mock_open_dialog, mock_open_file):
        mock_open_dialog.return_value = "session.pkl"
        load_previous_session(self.mock_app)
        mock_error.assert_called_once()
        self.assertIn("Errore durante il caricamento della sessione", mock_error.call_args[0][1])

if __name__ == "__main__":
    unittest.main()
