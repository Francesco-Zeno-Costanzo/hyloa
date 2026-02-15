==============================
Installing the package
==============================

HYLOA is distributed both with **pip** and with **a wheel (.whl)** through GitHub Releases.
The recommended installation method is different between Linux and Windows, but in both cases it is possible
to use either method. The wheel installation allows you to choose the version, and is recommended for Windows users,
because it includes a simple installer script which is the **setup.bat** file;
while the pip installation allows you to get the latest version directly from PyPI.


**Linux Installation**
========================

It is recommended to do this in a **virtual environment** to avoid conflicts with other packages:

.. code-block:: bash

    python -m venv .venv
    source .venv/bin/activate

**Recommended method: pip installation**
----------------------------------------

1. Open a terminal and run:

.. code-block:: bash

    pip install hyloa

This will install the latest version of HYLOA from PyPI.


**Alternative method: wheel installation**
--------------------------------------------

1. Go to the release page:

   https://github.com/Francesco-Zeno-Costanzo/hyloa/releases

2. Download the file:

   ``hyloa-<version>-py3-none-any.whl``

3. Open a terminal in the folder where the wheel was downloaded.

4. Install HYLOA with:

.. code-block:: bash

    python -m pip install hyloa-<version>-py3-none-any.whl

Replace ``<version>`` with the actual release version.

**Windows installation using setup.bat**
==========================================
To make the installation process easier for Windows users,
each release includes a simple installer script: ``setup.bat``.
You can use it to install HYLOA and create a desktop shortcut to launch the GUI.

You only need to do the following:

1. Download from the release page:

   - ``hyloa-<version>-py3-none-any.whl``
   - ``setup.bat``

2. Double-click **setup.bat**

The script will:

- install HYLOA,
- create a desktop shortcut to launch the GUI.

This will automatically install everything you need and create a desktop shortcut to launch the GUI.

.. note::

   On Windows, make sure that Python is installed **with the “Add python.exe to PATH” option enabled** during the installer setup.  
   If you forgot to check that box, you can add Python to your PATH manually:

   **Add Python to PATH (user level):**

   1. Open the Start Menu and search for **“Environment Variables”**, then open **“Edit the system environment variables”**.
   2. Click **“Environment Variables…”**.
   3. Under **“User variables”**, select **Path** and click **“Edit…”**.
   4. Click **“New”** and paste the folder path containing ``python.exe``  
      (e.g. ``C:\Users\you\AppData\Local\Programs\Python\Python311``).
   5. Optionally, also add the ``Scripts`` subfolder.
   6. Click **OK** to close all dialogs.

   After doing this, close and reopen your terminal and run:

   ``python --version``

   to verify that Python is correctly available in your PATH.


**Updating HYLOA**
---------------------
To update HYLOA to the latest version, is possible to use pip:
.. code-block:: bash

    pip install --upgrade hyloa

Alternatively, you can simply download the latest wheel file from the GitHub Releases
page and install it as shown above.
This will overwrite the previous installation with the new version.

**Installing from source (developer mode)**
-----------------------------------------------
If you want to modify the code or contribute:

.. code-block:: bash

    git clone https://github.com/Francesco-Zeno-Costanzo/hyloa.git
    cd hyloa
    python -m pip install -e .

This installs HYLOA in *editable mode*, ideal for development.
Via ``pip install -e .`` the package is linked to the source code, so any changes you make will be reflected immediately without needing to reinstall.


**Final Notes**
-----------------
Distributing HYLOA as a wheel in GitHub Releases or with pipallows users to download
only the necessary installation files without downloading the whole repository.
This makes installation fast, clean, and platform-independent.
The differences in installation methods between Linux and Windows are mainly due to the convenience of providing a simple installer script for Windows users,
which allows the creation of a desktop shortcut and a more straightforward installation process without needing to use the command line.