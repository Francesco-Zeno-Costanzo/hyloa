import re
import requests
from packaging import version
from PyQt5.QtWidgets import QMessageBox 

import hyloa

def get_latest_version_from_init():
    '''
    Fetches the latest version of the hyloa package
    from its __init__.py file on GitHub.

    Returns
    -------
    str or None
        The latest version string if found, otherwise None.
    '''
    repo = "Francesco-Zeno-Costanzo/hyloa/main/hyloa/__init__.py"
    url  = f"https://raw.githubusercontent.com/{repo}"
    
    response = requests.get(url)
    if response.status_code == 200:
        # Extract the version using regex
        match = re.search(r'__version__\s*=\s*["\']([\d\.]+)["\']', response.text)
        if match:
            return match.group(1)
    return None

def get_local_version():
    ''' Returns the local version of the hyloa package from its __init__.py file.
    '''
    return hyloa.__version__


def is_update_available(local_ver, remote_ver):
    '''
    Checks if a newer version of the hyloa package is available.
    
    Parameters
    ----------
    local_ver : str
        The local version of the hyloa package.
    remote_ver : str
        The remote version of the hyloa package.
    
    Returns
    -------
    bool
        True if a newer version is available, False otherwise.
    '''
    return version.parse(remote_ver) > version.parse(local_ver)


def check_for_updates():
    '''
    Checks for updates to the hyloa package by comparing the local version
    with the latest version available on GitHub.
    '''
    local_ver  = get_local_version()
    remote_ver = get_latest_version_from_init()

    if remote_ver is None:
        QMessageBox.critical(None, "Error", "Unable to check for updates. Please check your internet connection")
    elif is_update_available(local_ver, remote_ver):
        QMessageBox.information(None, "Update Available",
                                f"Version {remote_ver} available (your version: {local_ver}).\n")
        
        """
        Something to aoutomatically update the package.
        For now, we just inform the user.
        """
    else:
        QMessageBox.information(None, "Already update", f"You are already using the latest version ({local_ver}).")
