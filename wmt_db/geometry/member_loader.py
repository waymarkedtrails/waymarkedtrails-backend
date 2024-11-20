# SPDX-License-Identifier: GPL-3.0-or-later
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2024 Sarah Hoffmann
""" Main function for building a complex route geometry.
"""
import sqlalchemy as sa
from geoalchemy2.shape import to_shape
from geoalchemy2 import Geography
from osgende.common.tags import TagStore

from . import route_types as rt

def get_relation_objects(conn, members, way_table, route_table):
    """ Load all necessary data for relation members from the database.

        Returns an ordered list of SimpleWays (for ways) and
        Routes (for relations) with an additional 'role' property set
        to the member list.
    """
    data = {}

    ways = {m['id']: m['role'] for m in members if m['type'] == 'W'}

    if ways:
        data.update(_extract_ways(conn, ways, way_table))

    rels = {m['id']: None for m in members if m['type'] == 'R'}

    return [data[(m['type'], m['id'])] for m in members
            if (m['type'], m['id']) in data]


def _extract_ways(conn, ways: dict[int, str], t: sa.FromClause):
        sql = sa.select(t.c.id, t.c.geom, t.c.tags,
                        sa.func.ST_Length(sa.func.ST_Transform(t.c.geom, 4326)
                          .cast(Geography)).label('length'))\
                .where(t.c.id.in_(list(ways.keys())))\
                .where(t.c.geom is not None)
        for way in conn.execute(sql):
            geom = to_shape(way.geom)
            match ways[way.id]:
                case 'forward':
                    direction = 1
                    role = ''
                case 'backward':
                    direction = -1
                    role = ''
                case 'main':
                    direction = 0
                    role = ''
                case _:
                    direction = 0
                    role = ways[way.id].strip()
            yield ('W', way.id), rt.BaseWay(osm_id=way.id, tags=TagStore(way.tags),
                                           length=int(way.length), direction=direction,
                                           role=role, geom=geom)
