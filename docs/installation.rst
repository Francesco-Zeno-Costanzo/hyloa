==============================
Installing the package
==============================

At the moment **HYLOA is distributed only as a wheel (.whl)** through GitHub Releases.  
Because of this, the recommended installation method is to download and install the wheel file directly.



**Installing from GitHub Release Linux**
--------------------------------------------
This is currently the official way to install HYLOA.

1. Go to:

   https://github.com/Francesco-Zeno-Costanzo/hyloa/releases

2. Download the file:

   ``hyloa-<version>-py3-none-any.whl``

3. Open a terminal in the folder where the wheel was downloaded.

4. Install it with:

   .. code-block:: bash

       python -m pip install hyloa-<version>-py3-none-any.whl

Replace ``<version>`` with the actual release version.

This method does **not** require cloning or downloading the entire repository.

**Windows installation using setup.bat**
-------------------------------------------
For Windows users who prefer a simple one-click installation, each release include a
``setup.bat`` installer script.

This script typically runs:

.. code-block:: none

    @echo off
    python -m pip install hyloa-<version>-py3-none-any.whl
    REM: create desktop shortcuts, copy icons, ...

Typical usage:

1. Download:

   - ``hyloa-<version>-py3-none-any.whl``
   - ``setup.bat``

2. Double-click ``setup.bat``  to run the installer.

3. The script installs HYLOA and create a desktop icon.

This will automatically install everything you need and create a desktop shortcut to launch the GUI.

**Updating HYLOA**
---------------------
To update HYLOA to the latest version, simply download the latest wheel file from the GitHub Releases page and install it using pip as shown above.
This will overwrite the previous installation with the new version.

**Installing from source (developer mode)**
-----------------------------------------------
If you want to modify the code or contribute:

.. code-block:: bash

    git clone https://github.com/Francesco-Zeno-Costanzo/hyloa.git
    cd hyloa
    python -m pip install -e .

This installs HYLOA in *editable mode*, ideal for development.


**Final Notes**
-----------------
Distributing HYLOA as a wheel in GitHub Releases allows users to download only the necessary installation files without downloading the whole repository.
This makes installation fast, clean, and platform-independent.