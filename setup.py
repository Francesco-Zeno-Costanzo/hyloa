# This file is part of HYLOA - HYsteresis LOop Analyzer.
# Copyright (C) 2024 Francesco Zeno Costanzo

# HYLOA is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# HYLOA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with HYLOA. If not, see <https://www.gnu.org/licenses/>.


from setuptools import setup, find_packages


setup(
    name="hyloa", 
    version="1.9.18",
    author="Francesco Zeno Costanzo",
    author_email="zenofrancesco99@gmail.com",
    description="A package for analyzing hysteresis loops",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Francesco-Zeno-Costanzo/hyloa",
    packages=find_packages(where="."),  # Search package in hyloa/
    package_dir={"": "."},  # Means that hyloa/ in the root
    include_package_data=True,
    install_requires=[
        "PyQt5",
        "numpy",
        "scipy",
        "pandas",
        "matplotlib",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10.12",
    entry_points={
        "console_scripts": [
            "hyloa=hyloa.main:main",
        ],
    },
)
