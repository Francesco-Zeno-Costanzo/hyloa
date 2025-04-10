import unittest
import tkinter as tk
from unittest.mock import MagicMock

from Hysteresis.utils.scroll import ScrollableFrame

class TestScrollableFrame(unittest.TestCase):

    def setUp(self):
        '''Set up a basic Tkinter root window.
        '''
        self.root = tk.Tk()
        self.root.withdraw()  # Prevent window from appearing

    def tearDown(self):
        '''Destroy the root window after test.
        '''
        #self.root.update_idletasks()
        self.root.destroy()

    def test_scrollable_frame_creation(self):
        '''Test if ScrollableFrame initializes correctly.
        '''
        frame = ScrollableFrame(self.root)
        frame.pack()

        # Check if canvas and scrollbar exist
        self.assertIsInstance(frame.canvas, tk.Canvas)
        self.assertTrue(hasattr(frame, "scrollable_frame"))
        self.assertIsInstance(frame.scrollable_frame, tk.Frame)

        # Check if window has been added to the canvas
        windows = frame.canvas.find_all()
        self.assertGreater(len(windows), 0, "Canvas should contain at least one window.")

    """def test_scrollregion_updated_on_configure(self):
        '''Test that scrollregion updates when inner frame is resized.
        '''
        frame = ScrollableFrame(self.root)
        frame.pack()

        mock_canvas_configure  = MagicMock()
        frame.canvas.configure = mock_canvas_configure

        # Simulate <Configure> event
        frame.scrollable_frame.event_generate("<Configure>")
        self.root.update_idletasks()

        # Ensure scrollregion was updated
        mock_canvas_configure.assert_called()"""

    def test_mousewheel_binding(self):
        '''Test that mouse wheel binds/unbinds correctly on enter/leave.
        '''
        frame = ScrollableFrame(self.root)
        frame.pack()

        # Bind mock methods
        frame.canvas.bind_all   = MagicMock()
        frame.canvas.unbind_all = MagicMock()

        # Simulate <Enter> and <Leave> events
        frame._bind_mousewheel(event=None)
        frame._unbind_mousewheel(event=None)

        # Check that bindings happened
        frame.canvas.bind_all.assert_any_call("<MouseWheel>", frame._on_mousewheel)
        frame.canvas.unbind_all.assert_any_call("<MouseWheel>")

    def test_mousewheel_scrolls_canvas(self):
        '''Test that mousewheel event scrolls canvas.
        '''
        frame = ScrollableFrame(self.root)
        frame.pack()

        frame.canvas.yview_scroll = MagicMock()

        # Simulate a Windows-style mouse wheel scroll
        event = type("Event", (), {"delta": 120, "num": 0})()
        frame._on_mousewheel(event)
        frame.canvas.yview_scroll.assert_called_with(-1, "units")

        # Simulate a Linux-style scroll down
        event = type("Event", (), {"num": 5})()
        frame._on_mousewheel(event)
        frame.canvas.yview_scroll.assert_called_with(1, "units")

        # Simulate a Linux-style scroll up
        event = type("Event", (), {"num": 4})()
        frame._on_mousewheel(event)
        frame.canvas.yview_scroll.assert_called_with(-1, "units")



