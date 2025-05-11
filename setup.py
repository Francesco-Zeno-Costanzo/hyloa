from setuptools import setup, find_packages

setup(
    name="hyloa", 
    version="1.2.7",
    author="Francesco Zeno Costanzo",
    author_email="zenofrancesco99@gmail.com",
    description="Un pacchetto per l'analisi dei cicli di isteresi",
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
