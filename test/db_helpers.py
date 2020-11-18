# SPDX-License-Identifier: GPL-3.0-only
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2020 Sarah Hoffmann

from geoalchemy2 import Geometry
from geoalchemy2.elements import WKTElement
from geoalchemy2.shape import to_shape

from shapely import wkt

class DBValue:

    def __init__(self, value, db_type):
        self.value = value
        self.db_type = db_type

    def __eq__(self, other):
        if isinstance(self.db_type, Geometry):
            return wkt.loads(other) == to_shape(self.value)
        return self.value == other
