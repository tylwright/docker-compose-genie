#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name="docker-compose-genie",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "dcg=dcg.cli:cli",
        ],
    },
    install_requires=[
        "Click==8.0.3",
        "tabulate==0.9.0",
        "pyyaml==5.4.1",
        "rich",
    ],
    author="Tyler Wright",
    author_email="tylwright@gmail.com",
    description="docker-compose Genie is a helpful CLI wrapper for managing docker-compose deployments/stacks.",
    url="https://github.com/tylwright/docker-compose-genie",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GPL-3.0 license",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
