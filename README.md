# **HYLOA**

<p align="center">
  <img src="https://raw.githubusercontent.com/Francesco-Zeno-Costanzo/Hysteresis/main/docs/_static/hysteresis_logo.png" alt="Hysteresis Logo" width="250">
</p>

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Documentation Status](https://readthedocs.org/projects/hysteresisanalysis/badge/?version=latest)](https://hysteresisanalysis.readthedocs.io/en/latest/?badge=latest)
[![Python Tests](https://github.com/Francesco-Zeno-Costanzo/hyloa/actions/workflows/test.yml/badge.svg)](https://github.com/Francesco-Zeno-Costanzo/hyloa/actions/workflows/test.yml)
![Version](https://img.shields.io/github/v/release/Francesco-Zeno-Costanzo/hyloa)

**Simple program for an analysis of hysteresis loops.**
---

## **Introduction**  
HYsteresis LOop Analyzer is a Python package that allows you to **load, analyze and visualize** hysteresis loops using a graphical interface.


### **Main features:**  
- Loading and managing experimental data files  
- Visualization of hysteresis loops with interactive tools  
- Correction and analysis of loops
- Wokrsheet for general purposes data analysis
- A simple code editor to write custom scripts for data analysis and visualization
- An integrated python shell  


🔗 **Complete documentation:**  
📚 [ReadTheDocs - hyloa](https://hysteresisanalysis.readthedocs.io/en/latest/)  

---

# Installation

HYLOA is distributed both with **pip** and with **a wheel (.whl)** through GitHub Releases.  
The recommended installation method is different between Linux and Windows, but in both cases it is possible
to use either method. The wheel installation allows to choose the version, and is recommended for Windows users,
bacuse it include a simple installer script which is the **setup.bat** file;
while the pip installation allows you to get the latest version directly from PyPI.

---

## Linux

Obviously is recomended to do this in a **virtual environment** to avoid conflicts with other packages.
```bash
python -m venv .venv
source .venv/bin/activate 
```

### **Recommended method: pip installation**
1. Open a terminal and run:

```bash
pip install hyloa
```
This will install the latest version of HYLOA from PyPI.

### **Alternative method: wheel installation**

1. Go to the release page:

   https://github.com/Francesco-Zeno-Costanzo/hyloa/releases

2. Download the file:

   ```
   hyloa-<version>-py3-none-any.whl
   ```

3. Open a terminal in the folder where the wheel was downloaded.

4. Install HYLOA with:

```bash
python -m pip install hyloa-<version>-py3-none-any.whl
```

---

## Windows (installation using setup.bat)

To make the installation process easier for Windows users,
each release includes a simple installer script: `setup.bat`.
You can use it to install HYLOA and create a desktop shortcut to launch the GUI.
You only need to do the following:

1. Download from the release page:
   - `hyloa-<version>-py3-none-any.whl`
   - `setup.bat`

2. Double-click **setup.bat**

The script will:
- install HYLOA,
- create a desktop shortcut to launch the GUI.

---

## **Usage**  
To start the graphical interface on **Linux**, use the command:
```bash
hyloa
```

On **Windows** just use the desktop shortcut.
