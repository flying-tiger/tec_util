#!/usr/bin/env python3
from setuptools import setup
setup(
    name = 'tec_util',
    version = '0.1.0',
    descripion = 'Utilities for working with Tecplot data files',
    license = 'MIT',
    url = 'https://github.com/flying-tiger/tec_util',
    author = 'Jeffrey Hill',
    author_email = 'jeff.p.hill@gmail.com',
    packages = ['tec_util'],
    python_requires = '>=3.4',
    install_requires = ['pytecplot>=0.8'],
    entry_points= {
        'console_scripts': [
            'tec_util=tec_util.__main__:main',
        ]
    }
)
