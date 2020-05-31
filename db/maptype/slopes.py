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

from db.tables.piste import PisteRoutes, PisteWayInfo
from db.maptype.routes import DB as RoutesDB

class DB(RoutesDB):
    def create_tables(self):
        symbol_factory = ShieldFactory(self.site_config.ROUTES.symbols,
                                       self.site_config.SYMBOLS)

        # all the route stuff we take from the RoutesDB implmentation
        tables = self.create_table_dict(symbol_factory, PisteRoutes)

        # now create the additional joined ways
        tabname = self.site_config.DB_TABLES
        subset = and_(text(self.site_config.DB_WAY_SUBSET),
                      column('id').notin_(select([tables['relway'].c.id])))
        filt = FilteredTable(self.metadata, tabname.way_table + '_view',
                             self.osmdata.way, subset)
        tables['norelway_filter'] = filt
        ways = PisteWayInfo(self.metadata, tabname.way_table,
                            filt, self.osmdata, self.site_config.ROUTES,
                            symbol_factory)
        tables['ways'] = ways

        cols = ('name', 'symbol', 'difficulty', 'piste')
        joins = GroupedWayTable(self.metadata, tabname.joinedway, ways, cols)
        tables['joined_ways'] = joins

        _RouteTables = namedtuple('_RouteTables', tables.keys())

        return _RouteTables(**tables)

    def dataview(self):
        schema = self.get_option('schema', '')
        if schema:
            schema += '.'
        with self.engine.begin() as conn:
            conn.execute("""CREATE OR REPLACE VIEW %sdata_view AS
                            (SELECT geom FROM %s%s
                             UNION SELECT geom FROM %s%s)"""
                         % (schema, schema, str(self.tables.style.data.name),
                            schema, str(self.tables.ways.data.name)))


    def mkshield(self):
        route = self.tables.routes
        sway = self.tables.ways

        rel = self.osmdata.relation.data
        way = self.osmdata.way.data
        todo = ((route, select([rel.c.tags]).where(rel.c.id == route.data.c.id)),
                (sway, select([way.c.tags]).where(way.c.id == sway.data.c.id)))

        donesyms = set()

        with self.engine.begin() as conn:
            for src, sel in todo:
                for r in conn.execution_options(stream_results=True).execute(sel):
                    tags = TagStore(r["tags"])
                    t, difficulty = self.tables.routes.basic_tag_transform(0, tags)
                    sym = src.symbols.create(tags, '', difficulty)

                    if sym is not None:
                        symid = sym.get_id()

                        if symid not in donesyms:
                            donesyms.add(symid)
                            src.symbols.write(sym, True)
