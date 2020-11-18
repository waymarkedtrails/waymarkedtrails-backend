# SPDX-License-Identifier: GPL-3.0-only
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2015 Michael Spreng
#               2015-2020 Sarah Hoffmann
""" Database for the combinded route/way view (slopes)
"""
from collections import namedtuple, OrderedDict

import osgende
from osgende.generic import FilteredTable
from osgende.common.tags import TagStore
from osgende.lines import GroupedWayTable
from wmt_shields import ShieldFactory

from sqlalchemy import text, select, func, and_, column, exists, not_

from ..tables.piste import PisteRoutes, PisteWayInfo
from ..maptype.routes import create_mapdb as create_route_mapdb

def create_mapdb(site_config, options):
    # all the route stuff we take from the RoutesDB implmentation
    db = create_route_mapdb(site_config, options, PisteRoutes)

    # now create the additional joined ways
    tabname = site_config.DB_TABLES
    subset = and_(text(site_config.DB_WAY_SUBSET),
                  column('id').notin_(select([db.tables.relway.c.id])))
    filt = db.add_table('norelway_filter',
               FilteredTable(db.metadata, tabname.way_table + '_view',
                             db.osmdata.way, subset))

    ways = db.add_table('ways',
               PisteWayInfo(db.metadata, tabname.way_table,
                            filt, db.osmdata, db.tables.updates,
                            site_config.ROUTES,
                            db.tables.routes.shield_fab))

    cols = ('name', 'symbol', 'difficulty', 'piste')
    db.add_table('joinded_ways',
                 GroupedWayTable(db.metadata, tabname.joinedway, ways, cols))

    db.add_function('dataview', _mapdb_dataview)
    db.add_function('mkshield', _mapdb_mkshield)

    return db

def _mapdb_dataview(db):
    schema = db.get_option('schema', '')
    if schema:
        schema += '.'

    with db.engine.begin() as conn:
        conn.execute(f"""CREATE OR REPLACE VIEW {schema}data_view AS
                        (SELECT geom FROM {db.tables.style.data.key}
                         UNION SELECT geom FROM {db.tables.ways.data.key})""")

def _mapdb_mkshield(db):
    route = db.tables.routes
    sway = db.tables.ways

    rel = db.osmdata.relation.data
    way = db.osmdata.way.data
    todo = ((route, select([rel.c.tags]).where(rel.c.id == route.data.c.id)),
            (sway, select([way.c.tags]).where(way.c.id == sway.data.c.id)))

    donesyms = set()

    with db.engine.begin() as conn:
        for src, sel in todo:
            for r in conn.execution_options(stream_results=True).execute(sel):
                tags = TagStore(r["tags"])
                t, difficulty = db.tables.routes.basic_tag_transform(0, tags)
                sym = src.symbols.create(tags, '', difficulty)

                if sym is not None:
                    symid = sym.get_id()

                    if symid not in donesyms:
                        donesyms.add(symid)
                        src.symbols.write(sym, True)
