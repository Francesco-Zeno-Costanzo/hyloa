.. Hyloa documentation master file, created by
   sphinx-quickstart on YYYY-MM-DD.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

========================================
HYLOA - Documentation
========================================

Welcome to the official documentation of **HYsteresis LOop Analyzer**, a software for analyzing hysteresis loops.

.. image:: _static/hysteresis_logo.png
   :scale: 30%
   :alt: Logo di hyloa
   :align: center

**Documentation index:**

.. toctree::
   :maxdepth: 2
   :caption: Contents

   installation
   usage
   release_notes
   modules
   hyloa
   hyloa.data
   hyloa.gui
   hyloa.utils

-----------------

**What is HYLOA?**
----------------------------------
`HYLOA` is a Python package designed to analyze hysteresis loops with an intuitive graphical interface.

📌 **Main features**:

- 📊 **Data display**: Loading and displaying hysteresis loops.
- 🔧 **Analysis tools**: Filters, normalization, curve fitting and more.
- 🖥 **User-friendly graphical interface** based on PyQt5.

-----------------

**How to get started?**
--------------------------------
To install the package:

1. Go to:

   https://github.com/Francesco-Zeno-Costanzo/hyloa/releases

2. Download the file:

   ``hyloa-<version>-py3-none-any.whl``

3. Open a terminal in the folder where the wheel was downloaded.

4. Install it with:

   .. code-block:: bash

       python -m pip install hyloa-<version>-py3-none-any.whl

Replace ``<version>`` with the actual release version.

To launch the graphical interface:

.. code-block:: bash

   hyloa

**Windows users - quick launch:**

If you're on Windows and prefer not to use the terminal, simply:

1. Download:

   - ``hyloa-<version>-py3-none-any.whl``
   - ``setup.bat``

2. Double-click ``setup.bat``  to run the installer.

This will automatically install everything you need and create a desktop shortcut to launch the GUI.


**Feedback**
-----------------
If you find a bug or have suggestions, open an issue at [GitHub](https://github.com/Francesco-Zeno-Costanzo/hyloa).

-----------------

**Index and search**
--------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`



