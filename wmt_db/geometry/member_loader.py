# SPDX-License-Identifier: GPL-3.0-or-later
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2024 Sarah Hoffmann
""" Main function for building a complex route geometry.
"""
import json
from copy import deepcopy

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

    ways = [m['id'] for m in members if m['type'] == 'W']
    if ways:
        t = way_table
        sql = sa.select(t.c.id, t.c.geom, t.c.tags,
                        sa.func.ST_Length(sa.func.ST_Transform(t.c.geom, 4326)
                          .cast(Geography)).label('length'))\
                .where(t.c.id.in_(ways))\
                .where(t.c.geom is not None)
        for way in conn.execute(sql):
            data[('W', way.id)] = rt.BaseWay(osm_id=way.id,
                                             tags=TagStore(way.tags or {}),
                                             length=int(way.length), direction=0,
                                             geom=to_shape(way.geom))


    rels = [m['id'] for m in members if m['type'] == 'R']
    if rels:
        t = route_table
        sql = sa.select(t.c.id, t.c.route)\
                .where(t.c.id.in_(rels))\
                .where(t.c.route is not None)

        for rel in conn.execute(sql):
            data[('R', rel.id)] = json.loads(rel.route,
                                             object_hook=rt.json_decoder_hook)

    finallist = []
    for i, m in enumerate(members):
        key = (m['type'], m['id'])
        if (seg := data.get(key)) is not None:
            # If a way appears two times, we need to make a copy because
            # the way may be reversed and moved around later.
            if seg.start is not None:
                seg = deepcopy(seg)
            seg.start = i
            seg.direction, seg.role = adjust_role(seg, m['role'])
            finallist.append(seg)

    return finallist


def adjust_role(seg, role) -> tuple[int, str]:
    match role:
        case 'forward':
            return 1, ''
        case 'backward':
            return -1, ''

    outrole = '' if role == 'main' else role.strip()
    if isinstance(seg, rt.BaseWay) and seg.is_closed\
            and seg.tags.get('junction') in ('roundabout', 'circular'):
        return 1, outrole

    return 0, outrole
