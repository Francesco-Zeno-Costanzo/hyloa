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

"""
Simple script to bump the version of the package.
"""

import re
import sys
import subprocess
from pathlib import Path
from argparse import ArgumentParser

BASE_DIR       = Path(__file__).resolve().parent
PYPROJECT_PATH = BASE_DIR.parent / "pyproject.toml"
INIT_PATH      = BASE_DIR.parent / "hyloa" / "__init__.py"
SETUP_PATH     = BASE_DIR.parent / "setup.py"

INCREMENT_MODES = ('major', 'minor', 'patch')
VERSION_PATTERN = r'(\d+)\.(\d+)\.(\d+)'


def read_version_from_init():
    content = INIT_PATH.read_text()
    match = re.search(r'__version__\s*=\s*[\'"]' + VERSION_PATTERN + r'[\'"]', content)
    if not match:
        raise RuntimeError("Version not found in __init__.py")
    return '.'.join(match.groups())


def increment_version(version, mode):
    major, minor, patch = map(int, version.split('.'))
    if mode == 'major':
        return f"{major + 1}.0.0"
    elif mode == 'minor':
        return f"{major}.{minor + 1}.0"
    elif mode == 'patch':
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(f"Invalid mode: {mode}")


def update_file(file_path, regex_pattern, new_version, label='version'):
    content = file_path.read_text()
    new_content = re.sub(
        regex_pattern,
        lambda m: m.group(0).replace(m.group(2), new_version),
        content
    )
    file_path.write_text(new_content)
    print(f" Updated {label} in {file_path}")


def git_commit_and_push(new_version):
    try:
        subprocess.run(["git", "add", str(PYPROJECT_PATH), str(SETUP_PATH), str(INIT_PATH)], check=True)

        subprocess.run(["git", "commit", "-m", f"Bump version to {new_version}"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("Changes committed and pushed to origin.")
    except subprocess.CalledProcessError as e:
        print("Git command failed:", e)
        sys.exit(1)

def git_create_and_push_tag(new_version):
    tag_name = f"v{new_version}"
    try:
        # Create tag
        subprocess.run(["git", "tag", "-a", tag_name, "-m", f"Release {tag_name}"], check=True)

        # Push only the tag
        subprocess.run(["git", "push", "origin", tag_name], check=True)

        print(f"Tag {tag_name} created and uploaded.")
    except subprocess.CalledProcessError as e:
        print("Git tag command failed:", e)
        sys.exit(1)



def main(mode):
    if mode not in INCREMENT_MODES:
        raise RuntimeError(f"Invalid mode: {mode}. Choose from {INCREMENT_MODES}")

    old_version = read_version_from_init()
    new_version = increment_version(old_version, mode)
    print(f"Bumping version from {old_version} to {new_version}")

    update_file(INIT_PATH,
                rf'(__version__\s*=\s*[\'"])({VERSION_PATTERN})([\'"])',
                new_version,
                label="__init__.py")

    update_file(SETUP_PATH,
                rf'(version\s*=\s*[\'"])({VERSION_PATTERN})([\'"])',
                new_version,
                label="setup.py")

    update_file(PYPROJECT_PATH,
                rf'(version\s*=\s*[\'"])({VERSION_PATTERN})([\'"])',
                new_version,
                label="pyproject.toml")
    

    git_commit_and_push(new_version)
    git_create_and_push_tag(new_version)
    print("Version bump complete.")


if __name__ == "__main__":
    parser = ArgumentParser(description="Bump version")
    parser.add_argument('mode', choices=INCREMENT_MODES, help='Version increment mode')
    args = parser.parse_args()
    main(args.mode)
