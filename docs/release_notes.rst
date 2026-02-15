=========================
HYLOA Release Notes
=========================

Version 1.11.0 - 2026-02-15
~~~~~~~~~~~~~~~~~~~~~~~~~~~
This release introduces major improvements to cross-worksheet data handling,
user interface organisation, and analysis flexibility.

**New Features**

- It is now possible to create plots using data coming from different worksheets.
 This is enabled by a runtime data cache that stores and manages the content
 of each worksheet, allowing seamless cross-referencing during plot creation.

- The column math dialogue has been enhanced to support more complex operations
 between multiple columns, enabling advanced expressions and combined
 transformations.

**Interface Improvements**

- The plot creation dialogue linked to worksheets has been redesigned for better
 clarity and usability.

- The curve-fitting window has been improved in both the Worksheet and the
 Plot Control Panel for a more consistent and streamlined workflow.

- The Worksheet interface has been reorganised with grouped tool sections
 (Data / Plot / Analysis) to improve readability and scalability.

- The Plot Control Panel now adopts a structured layout with grouped controls,
 reducing visual clutter and making navigation between data operations,
 styling, and analysis are more intuitive.

- The window to see all loaded files is now more clear and allows to easily identify data from each file.

**Fixes**

- Fixed minor issues related to logging file encoding.

- Fixed data saving behaviour in the loop correction window.

- The loop correction tool now allows users to choose whether to analyse if
 operations should be performed on the original data or on the corrected
 data, improving flexibility in the analysis workflow.

Version 1.10.3 - 2026-01-12
~~~~~~~~~~~~~~~~~~~~~~~~~~~
The main changes of this patch are the introduction of a loading screen, with the logo and the progress bar,
and the change of session files that are now compressed via "gzip", with an ".hyloa" extension and a simple signature.
The program can always handle the old session files.
There is also a bug fix in the loops' correction process: the second shift option is now applied only if the fit converges.
Visual re-adjustments of buttons in the worksheet and control windows.

Version 1.10.2 - 2025-12-17
~~~~~~~~~~~~~~~~~~~~~~~~~~~
This patch introduces improvements to the hysteresis loop correction panel, allowing you to fit a cubic Bspline to calculate the anisotropy field.
The correction procedure is now more fluid, allowing for multiple iterations on the same data.
The window has also been improved, making it more robust for multiple screens.
Changes have also been made to the shell, which now behaves more like a Python shell.

Version 1.10.1 - 2025-12-05
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Fix installation on windows via setup.bat file

Version 1.10.0 - 2025-12-05
~~~~~~~~~~~~~~~~~~~~~~~~~~~
This release introduces a new Loop Correction panel and several usability improvements.
It provides a dedicated workspace to correct common hysteresis-loop distortions by performing fits in the loop's saturation regions and
applying a data-driven correction. The correction uses a user-defined fitting function (polynomial), automatically removes the constant term,
and subtracts the remaining functional part from the affected segments. After correction, the panel offers additional analyses
(for example, coercive field or remanence estimation) performed on the corrected loop.

When an optional destination file is selected, corrected variables are stored using a one-to-one mapping between the source 2x2 grid (Up/Down x X/Y)
and the destination 2x2 grid, so the user explicitly chooses which destination columns will receive the corrected data.
Field-shift and field-scale controls are available; note that fit ranges should be selected on the original, unscaled data because scaling is applied later. 

The plotting area includes an always-visible grid and a Matplotlib Navigation Toolbar
to enable zoom, pan, coordinate readout and image saving, improving interactive inspection of raw and corrected loops.


Version 1.9.21 - 2025-11-19
~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. Add possibility to resize window with scroll area for sidebar.
2. Add connection between all file loaded and worksheets. Worksheets now
   have access to all dataframes loaded in the main application.

Version 1.9.20 - 2025-11-15
~~~~~~~~~~~~~~~~~~~~~~~~~~~
First release of the package to allow easy installation via the wheel file.