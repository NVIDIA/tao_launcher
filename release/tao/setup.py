# Copyright (c) 2016-2018, NVIDIA CORPORATION.  All rights reserved.
"""Setup script to build the TAO Toolkit CLI package."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import glob
import os
import setuptools
import sys

from release import utils

# Define env paths.
LOCAL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOP_LEVEL_DIR = utils.up_directory(LOCAL_DIR, 1)
LAUNCHER_SDK_PATH = os.path.join(TOP_LEVEL_DIR, 'nvidia_tao_cli')
IGNORE_LIST = ['__init__.py', 'version.py']


# Get current __version__
def get_version_locals(package_root):
    """Get the package information."""
    version_locals = {}
    with open(os.path.join(package_root, 'version.py')) as version_file:
        exec(version_file.read(), {}, version_locals)
    return version_locals


def get_python_requirements():
    """Python version requirement."""
    # Set the required version of python - required when doing obfuscation.
    __python_version__ = ">=3.6"
    return __python_version__


def get_launcher_package(package_root=LAUNCHER_SDK_PATH, is_build_action=True):
    """Get TAO Launcher packages."""
    req_subdirs = utils.get_subdirs(package_root)
    if is_build_action:
        # Pick up the TAO launcher.
        launcher_packages = setuptools.find_packages(LAUNCHER_SDK_PATH)
        launcher_packages = ["nvidia_tao_cli." + f for f in launcher_packages]
        launcher_packages.append("nvidia_tao_cli")
        return launcher_packages

    # Cleanup. Rename all .py_tmp files back to .py and delete pyc files
    for dir_path in req_subdirs:
        dir_path = os.path.join(TOP_LEVEL_DIR, dir_path)
        pyc_list = glob.glob(dir_path + '/*.pyc')
        for pyc_file in pyc_list:
            os.remove(pyc_file)
    return []


# Getting dependencies.
def get_requirements(package_root):
    """Simple function to get packages."""
    with open(os.path.join(TOP_LEVEL_DIR, "dependencies/requirements-pip.txt"), 'r') as req_file:
        requirements = [r.replace('\n', '')for r in req_file.readlines()]
    return requirements


def main(args=sys.argv[1:]):
    """Main wrapper to run setup.py"""
    # Get package related information.
    version_locals = get_version_locals(LAUNCHER_SDK_PATH)
    __python_version__ = get_python_requirements()
    __long_description__ = utils.get_long_description(TOP_LEVEL_DIR)
    __long_description_content_type__ = "text/markdown"
    requirements = get_requirements(LAUNCHER_SDK_PATH)
    launcher_packages = get_launcher_package(
        package_root=LAUNCHER_SDK_PATH,
        is_build_action=True
    )

    # TODO: Modify script entry points
    setuptools.setup(
        name='nvidia-tao',
        version=version_locals['__version__'],
        description=version_locals["__description__"],
        author=version_locals["__contact_names__"],
        author_email=version_locals["__contact_emails__"],
        long_description=__long_description__,
        long_description_content_type=__long_description_content_type__,
        classifiers=[
            # How mature is this project? Common values are
            #  3 - Alpha
            #  4 - Beta
            #  5 - Production/Stable
            #  6 - Mature
            #  7 - Inactive
            'Intended Audience :: Developers',
            # Indicate what your project relates to
            'Topic :: Software Development :: Libraries',
            'Topic :: Software Development :: Libraries :: Python Modules',
            'Environment :: Console',
            'License :: OSI Approved :: Apache Software License',
            'Programming Language :: Python :: {}'.format(
                sys.version_info.major
            ),
            'Topic :: Scientific/Engineering :: Artificial Intelligence',
        ],
        keywords=version_locals["__keywords__"],
        packages=launcher_packages,
        license="NVIDIA Proprietary Software",
        package_dir={'': os.path.relpath(TOP_LEVEL_DIR)},
        python_requires=__python_version__,
        package_data={
            '': ['*.py', '*.json', '*.pdf'],
        },
        include_package_data=True,
        install_requires=requirements,
        zip_safe=False,
        entry_points={
            'console_scripts': [
                'tao=nvidia_tao_cli.entrypoint.tao_launcher:main',
            ]
        }
    )
    # Clean up packages post installation.
    get_launcher_package(package_root=LAUNCHER_SDK_PATH, is_build_action=False)


if __name__ == "__main__":
    main()
