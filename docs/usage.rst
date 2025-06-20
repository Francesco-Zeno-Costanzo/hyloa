===========================
Using the package
===========================

Linux launch
============
To start the hyloa graphical interface, use the command:

.. code-block:: bash
    
    cd path/to/your/files
    hyloa

This will open the graphical interface, where you can load the data, view it and analyze it.

Windows launch
==============
Click on the desktop shortcut created during the installation

Getting Started
===============

To begin using the application, a **log file** must be initialized. This is used to track all operations and comments.  
- When you load a **previous session**, the corresponding log file is automatically reused.  
- Log files and session files **must be stored in the same directory**.  
- If the log file is missing, a new one will be created using the previous path and filename.

File Management
===============

- Use the **"Load File"** button to import one or more data files.
- Upon loading, you’ll be prompted to select which columns to load and optionally rename them.
- All loaded data is stored as **Pandas DataFrames**, and their structure can be reviewed with the **"Show Files"** button.
- The **"Save File"** button allows you to export modified files, keeping the original header.
- You can also **duplicate a file** using the **"Duplicate File"** button. This is useful for testing operations on copies while preserving the original data.

Analysis Tools
==============

- Use **"Create Plot"** to open a control panel for configuring and displaying graphs.  
  Each panel allows you to:
  - Add/remove cycles
  - Customize style
  - Normalize data
  - Perform curve fitting
  - Invert axes or branches
  - Close loops

- The **"Script"** button opens a scripting editor where you can:
  - Write and run custom Python code
  - Load or save `.py` files
  - See script output directly in the application shell

- The **"Annotation"** button opens a simple notepad where you can write text that will be saved directly into the current log file.

Session Management
==================

- The **"Save Session"** button allows you to save the entire state of your analysis to a `.pkl` file. This includes:
  - Loaded data
  - Graphs and their layout
  - Custom styles
  - Curve fits
  - Open window states and positions

- The **"Load Session"** button restores a previously saved session with full fidelity.

- The **"List of Windows"** button provides a previewable list of all currently open windows, useful when:
  - Many plots are open at once
  - Some windows are minimized and need to be brought back to the front

Additional Features
===================

- A built-in **Python shell** is included at the bottom of the interface.
  - All column data loaded from files is automatically available as NumPy arrays in the shell.
  - Results from curve fitting and other operations are also added to the shell's variable space.
  - Shell and script execution can modify DataFrames in-place.

- **Log View Panel**: displays real-time logs of all operations, including system messages, annotations, and errors.

- The entire GUI is built using a **multi-document interface (MDI)**. Each graph and its control panel are separate, dockable, resizable subwindows.

- All actions are recorded in the log, ensuring traceability and reproducibility.

------------------

**Happy analysis**
