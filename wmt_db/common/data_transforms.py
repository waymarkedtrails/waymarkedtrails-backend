# SPDX-License-Identifier: GPL-3.0-only
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2020 Sarah Hoffmann
""" Various helper functions to process the tags of a route relation.
"""

from shapely.ops import linemerge
from geoalchemy2.shape import from_shape

from osgende.common.build_geometry import build_route_geometry

def make_itinerary(tags):
    """ Create an itinerary from 'to', 'from' and 'via' tags.
    """
    ret = []

    frm = tags.get('from')
    if frm is not None:
        ret.append(frm)

    via = tags.get('via')
    if via is not None:
        if ';' in via:
            ret.extend(via.split(';'))
        else:
            ret.extend(via.split(' - '))

    to = tags.get('to')
    if to is not None:
        ret.append(to)

    return ret if ret else None

def make_geometry(conn, members, ways, table):
    """ Create the geometry for a route relation.
    """
    geom = build_route_geometry(conn, members, ways, table)

    if geom is None:
        return None

    if geom.geom_type not in ('MultiLineString', 'LineString'):
        raise RuntimeError("Bad geometry %s for %d" % (geom.geom_type, obj['id']))

    # if the route is unsorted but linear, sort it
    if geom.geom_type == 'MultiLineString':
        fixed_geom = linemerge(geom)
        if fixed_geom.geom_type == 'LineString':
            geom = fixed_geom

    return from_shape(geom, srid=table.c.geom.type.srid)
