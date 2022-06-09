# This file is part of the guarantor project
# https://github.com/xkudev/guarantor
#
# Copyright (c) 2022 xkudev (xkudev@pm.me) - MIT License
# SPDX-License-Identifier: MIT

import os
import sys
import setuptools


def project_path(*sub_paths):
    project_dirpath = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(project_dirpath, *sub_paths)


def read(*sub_paths):
    with open(project_path(*sub_paths), mode="rb") as fh:
        return fh.read().decode("utf-8")


install_requires = [
    line.strip()
    for line in read("requirements", "pypi.txt").splitlines()
    if line.strip() and not line.startswith("#") and not line.startswith("-")
]


long_description = "\n\n".join((read("README.md"), read("CHANGELOG.md")))


python_requires = ">=3.10"

# See https://pypi.python.org/pypi?%3Aaction=list_classifiers
classifiers = [
    "Development Status :: 3 - Alpha",
    "Environment :: Console",
    "Environment :: Other Environment",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: Unix",
    "Operating System :: POSIX",
    "Operating System :: MacOS :: MacOS X",
    # "Operating System :: Microsoft :: Windows",
    "Programming Language :: Python",

    # "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 3",

    # Or more specific:
    # "Programming Language :: Python :: 2.7",
    # "Programming Language :: Python :: 3.6",
    # "Programming Language :: Python :: 3.7",
    # "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: Implementation :: CPython",
    "Programming Language :: Python :: Implementation :: PyPy",
    "Topic :: Software Development :: Libraries",
    "Topic :: Software Development :: Libraries :: Python Modules",
]


package_dir = {"": "src"}


setuptools.setup(
    name="guarantor",
    license="MIT",
    author="xkudev",
    author_email="xkudev@pm.me",
    url="https://github.com/xkudev/guarantor",
    version="2022.1001a0",
    keywords="guarantor",
    description="The Guarantor Project.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages("src"),
    package_dir=package_dir,
    # include_package_data=True,
    # package_data={"": ["*.txt"]},
    install_requires=install_requires,
    entry_points="""
        [console_scripts]
        guarantor=guarantor.__main__:cli
    """,
    python_requires=python_requires,
    zip_safe=True,
    classifiers=classifiers,
)
