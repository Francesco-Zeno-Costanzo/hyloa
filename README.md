# **HYLOA**

<p align="center">
  <img src="https://raw.githubusercontent.com/Francesco-Zeno-Costanzo/Hysteresis/main/docs/_static/hysteresis_logo.png" alt="Hysteresis Logo" width="250">
</p>

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Documentation Status](https://readthedocs.org/projects/hysteresisanalysis/badge/?version=latest)](https://hysteresisanalysis.readthedocs.io/en/latest/?badge=latest)
[![Python Tests](https://github.com/Francesco-Zeno-Costanzo/hyloa/actions/workflows/test.yml/badge.svg)](https://github.com/Francesco-Zeno-Costanzo/hyloa/actions/workflows/test.yml)

**Simple program for an analysis of hysteresis loops.**
---

## **Introduction**  
HYsteresis LOop Analyzer is a Python package that allows you to **load, analyze and visualize** hysteresis loops using a graphical interface.


### **Main features:**  
- ✔️ Loading and managing experimental data files  
- ✔️ Visualization of hysteresis loops with interactive tools  
- ✔️ Normalization and closing of cycles for drift correction  
- ✔️ Custom fits with user-defined templates  
- ✔️ Saving modified data

🔗 **Complete documentation:**  
📚 [ReadTheDocs - hyloa](https://hysteresisanalysis.readthedocs.io/en/latest/)  

---

# Installation

HYLOA is distributed **exclusively as a wheel (.whl)** through GitHub Releases.  
The recommended installation method is to install the `.whl` file directly, without cloning the repository.
Is also recommended to use the last releases.

---

## Linux

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

Each release includes a simple installer script: `setup.bat`.

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
