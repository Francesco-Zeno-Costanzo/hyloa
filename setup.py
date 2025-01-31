from setuptools import setup, find_packages

setup(
    name="HysteresisAnalysis",  # Senza underscore
    version="0.1.0",
    author="Francesco Zeno Costanzo",
    author_email="zenofrancesco99@gmail.com",
    description="Un pacchetto per l'analisi dei cicli di isteresi",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Francesco-Zeno-Costanzo/Hysteresis",
    packages=find_packages(where="."),  # Cerca pacchetti in Hysteresis/
    package_dir={"": "."},  # Indica che Hysteresis/ è la root del pacchetto
    include_package_data=True,
    install_requires=[
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
            "hysteresis-analysis=Hysteresis.main:main",  # Assicurati che `main.py` sia dentro `Hysteresis/`
        ],
    },
)
