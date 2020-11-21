# SPDX-License-Identifier: GPL-3.0-only
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2015-2020 Sarah Hoffmann
""" Tables for administrative structures
"""
import sqlalchemy as sa
from geoalchemy2 import Geometry

class CountryGrid:
    """Wraps a Nominatim country_osm_grid table.
    """

    def __init__(self, meta, name='country_osm_grid'):
        self.data = sa.Table(name, meta,
                             sa.Column('country_code', sa.String),
                             sa.Column('area', sa.Float),
                             sa.Column('geom', Geometry)
                            )

    def column_cc(self):
        """ Returns the column with the country code.
        """
        return self.data.c.country_code

    def column_geom(self):
        """ Returns the column with the geometry.
        """
        return self.data.c.geom
