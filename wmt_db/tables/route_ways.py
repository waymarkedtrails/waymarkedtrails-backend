# SPDX-License-Identifier: GPL-3.0-only
#
# This file is part of Waymarked Trails
# Copyright (C) 2024 Sarah Hoffmann

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
import shapely.geometry as sgeom

from osgende.lines import RelationWayTable

class RouteWayTable(RelationWayTable):

    def make_geometry(self, points):
        if len(points) <= 1:
            return None

        geom = sgeom.LineString(points)

        return geom if geom.length < 500000 else None
