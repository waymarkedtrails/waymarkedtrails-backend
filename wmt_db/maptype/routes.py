# SPDX-License-Identifier: GPL-3.0-only
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2018-2020 Sarah Hoffmann

""" Database for the classic route view (hiking, cycling, etc.)
"""
from sqlalchemy import MetaData, select, text

import osgende
from osgende.generic import FilteredTable
from osgende.lines import RelationWayTable, SegmentsTable
from osgende.relations import RelationHierarchy
from osgende.common.tags import TagStore
from wmt_shields import ShieldFactory

from ..tables.countries import CountryGrid
from ..tables.routes import Routes
from ..tables.guideposts import GuidePosts
from ..tables.networknodes import NetworkNodes
from ..tables.updates import UpdatedGeometriesTable
from ..tables.styles import StyleTable

class RouteMapDB(osgende.MapDB):
    """ MapDB for standard route-relation-based activities. Adds special
        views and the ability to make shields.
    """

    def __init__(self, config, site_config):
        super().__init__(config)
        self.site_config = site_config

    def dataview(self):
        schema = self.get_option('schema', '')
        if schema:
            schema += '.'

        sql = f"SELECT geom FROM {self.tables.style.data.key}"
        if self.site_config.GUIDEPOSTS is not None:
            sql += f" UNION SELECT geom FROM {self.tables.guideposts.data.key}"

        with self.engine.begin() as conn:
            conn.execute(f"CREATE OR REPLACE VIEW {schema}data_view AS {sql}")

    def mkshield(self):
        route = self.tables.routes
        rel = self.osmdata.relation.data
        sel = select([rel.c.tags, route.data.c.country, route.data.c.level])\
                .where(rel.c.id == route.data.c.id)

        donesyms = set()

        with self.engine.begin() as conn:
            for r in conn.execution_options(stream_results=True).execute(sel):
                sym = route.symbols.create(TagStore(r["tags"]), r["country"],
                                           r["level"])

                if sym is not None:
                    symid = sym.get_id()

                    if symid not in donesyms:
                        donesyms.add(symid)
                        route.symbols.write(sym, True)


def create_mapdb(site_config, options):
    setattr(options, 'schema', site_config.DB_SCHEMA)
    db = RouteMapDB(options, site_config)

    setup_tables(db)

    return db


def setup_tables(db, route_class=Routes):
    if not db.get_option('no_engine'):
        country = CountryGrid(MetaData(), db.site_config.DB_TABLES.country)
        if not country.data.exists(db.engine):
            raise RuntimeError("No country table found.")

    db.set_metadata('srid', db.site_config.DB_SRID)
    db.set_metadata('num_threads', db.get_option('numthreads'))

    tabname = db.site_config.DB_TABLES

    # first the update table: stores all modified routes, points
    uptable = db.add_table('updates',
                           UpdatedGeometriesTable(db.metadata, tabname.change))

    # First we filter all route relations into an extra table.
    rfilt = db.add_table('relfilter',
                         FilteredTable(db.metadata, tabname.route_filter,
                                       db.osmdata.relation,
                                       text(f"({db.site_config.DB_ROUTE_SUBSET})")))

    # Then we create the connection between ways and relations.
    # This also adds geometries.
    relway = db.add_table('relway',
                          RelationWayTable(db.metadata, tabname.way_relation,
                                           db.osmdata.way, rfilt, osmdata=db.osmdata))

    # From that create the segmented table.
    segments = db.add_table('segments',
                            SegmentsTable(db.metadata, tabname.segment, relway,
                                          (relway.c.rels,)))

    # hierarchy table for super relations
    rtree = db.add_table('hierarchy',
                         RelationHierarchy(db.metadata, tabname.hierarchy, rfilt))

    # routes table: information about each route
    routes = db.add_table('routes',
                          route_class(db.metadata, rfilt, relway, rtree,
                                      CountryGrid(MetaData(), tabname.country),
                                      db.site_config.ROUTES,
                                      ShieldFactory(db.site_config.ROUTES.symbols,
                                                    db.site_config.SYMBOLS)))

    # finally the style table for rendering
    db.add_table('style',
                 StyleTable(db.metadata, routes, segments, rtree,
                            db.site_config.DEFSTYLE, uptable))

    # optional table for guide posts
    if db.site_config.GUIDEPOSTS is not None:
        cfg = db.site_config.GUIDEPOSTS
        filt = db.add_table('gp_filter',
                   FilteredTable(db.metadata, cfg.table_name + '_view',
                                 db.osmdata.node, text(cfg.node_subset),
                                 view_only=True))
        db.add_table('guideposts', GuidePosts(db.metadata, filt, cfg))\
           .set_update_table(uptable)

    # optional table for network nodes
    if db.site_config.NETWORKNODES is not None:
        cfg = db.site_config.NETWORKNODES
        filt = db.add_table('nnodes_filter',
                   FilteredTable(db.metadata, cfg.table_name + '_view',
                                 db.osmdata.node,
                                 db.osmdata.node.c.tags.has_key(cfg.node_tag),
                                 view_only=True))
        db.add_table('networknodes', NetworkNodes(db.metadata, filt, cfg))
