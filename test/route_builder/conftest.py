# SPDX-License-Identifier: GPL-3.0-or-later
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2024 Sarah Hoffmann
import pytest

from shapely import from_wkt

class Grid:
    """ Allows to define a point grid, which then can be used to create
        geometries.
    """
    # Coordinates are in mercator, so don't reduce spacing too much.
    def __init__(self, description, origin=(10, 30), spacing=1.0):
        self.nodes = {}
        for x, l in enumerate(description.splitlines()):
            for y, c in enumerate(l):
                if not c.isspace():
                    self.nodes[c] = [origin[0] + spacing * x, origin[1] + spacing * y]

    def coord(self, point):
        """ Return the coordinate tuple for a given point.
        """
        return self.nodes[str(point)]

    def coords(self, points):
        """ Return the given points as a coordinate list.
        """
        return list(map(self.nodes.__getitem__, points))

    def line(self, points):
        """ Create a Shapely LineString from the given points.
        """
        return from_wkt(self.wkt_line(points))

    def wkt_line(self, points):
        """ Create a line from the given points as a WKT string.
        """
        pts = [' '.join(map(str, p)) for p in self.coords(points)]
        return f"LINESTRING({','.join(pts)})"



@pytest.fixture
def grid():
    def _make(desc):
        return Grid(desc)

    return _make
