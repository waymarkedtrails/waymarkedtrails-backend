# SPDX-License-Identifier: GPL-3.0-only
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2015 Michael Spreng
#               2015-2023 Sarah Hoffmann
""" Database for the combinded route/way view (slopes)
"""
import sqlalchemy as sa

import osgende
from osgende.generic import FilteredTable
from osgende.common.tags import TagStore
from osgende.lines import GroupedWayTable

from ..tables.piste import PisteRoutes, PisteWayInfo
from ..maptype.routes import setup_tables

class SlopesMapDB(osgende.MapDB):
    """ MapDB for activities that may be mapped as relations or simple ways.
    """

    def __init__(self, config, site_config):
        super().__init__(config)
        self.site_config = site_config

    def dataview(self):
        schema = self.get_option('schema', '')
        if schema:
            schema += '.'

        with self.engine.begin() as conn:
            conn.execute(sa.text(f"""CREATE OR REPLACE VIEW {schema}data_view AS
                                     (SELECT geom FROM {self.tables.style.data.key}
                                     UNION SELECT geom FROM {self.tables.ways.data.key})"""))

    def mkshield(self):
        route = self.tables.routes
        sway = self.tables.ways
        rel = self.osmdata.relation.data
        way = self.osmdata.way.data

        donesyms = set()
        self._write_shields(route,
                            sa.select(rel.c.tags).where(rel.c.id == route.data.c.id),
                            donesyms)
        self._write_shields(sway,
                            sa.select(way.c.tags).where(way.c.id == sway.data.c.id),
                            donesyms)

    def _write_shields(self, source, subset, donesyms):
        with self.engine.begin() as conn:
            for r in conn.execution_options(stream_results=True).execute(subset):
                tags = TagStore(r.tags)
                _, difficulty = self.tables.routes.basic_tag_transform(0, tags)
                sym = source.symbols.create(tags, '', difficulty)

                if sym is not None:
                    symid = sym.get_id()

                    if symid not in donesyms:
                        donesyms.add(symid)
                        source.symbols.write(sym, True)


def create_mapdb(site_config, options):
    # all the route stuff we take from the RoutesDB implmentation
    setattr(options, 'schema', site_config.DB_SCHEMA)
    db = SlopesMapDB(options, site_config)

    setup_tables(db, PisteRoutes)

    # now create the additional joined ways
    tabname = site_config.DB_TABLES
    subset = sa.and_(sa.text(site_config.DB_WAY_SUBSET),
                     sa.column('id').notin_(sa.select(db.tables.relway.c.id)))
    filt = db.add_table('norelway_filter',
                        FilteredTable(db.metadata, tabname.way_table + '_view',
                                      db.osmdata.way, subset))

    ways = db.add_table('ways',
                        PisteWayInfo(db.metadata, tabname.way_table,
                                     filt, db.osmdata, db.tables.updates,
                                     site_config.ROUTES,
                                     db.tables.routes.shield_fab))

    cols = ('name', 'symbol', 'difficulty', 'piste')
    db.add_table('joined_ways',
                 GroupedWayTable(db.metadata, tabname.joinedway, ways, cols))

    return db
