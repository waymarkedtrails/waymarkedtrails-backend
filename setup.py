# SPDX-License-Identifier: GPL-3.0-only
# This file is part of the Waymarkedtrails Project
# Copyright (C) 2021 Sarah Hoffmann

from setuptools import setup

with open('README.md', 'r') as descfile:
    long_description = descfile.read()


setup(name='waymarkedtrails-backend',
      description='Database backend and rendering data for the Waymarkedtrails project.',
      long_description=long_description,
      version='0.1',
      maintainer='Sarah Hoffmann',
      maintainer_email='lonvia@denofr.de',
      url='https://github.com/waymarkedtrails/waymarkedtrails-backend',
      license='GPL 3.0',
      packages=['wmt_db',
                'wmt_db.config',
                'wmt_db.common',
                'wmt_db.styles',
                'wmt_db.tables',
                'wmt_db.maptype'
               ],
      package_data = {'wmt_db' : ['data/mapnik/**', 'data/shields/**', 'data/map-styles/**']},
      scripts=['wmt-makedb'],
      python_requires = ">=3.6",
      )
