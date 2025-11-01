# SPDX-License-Identifier: GPL-3.0-only
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2018-2023 Sarah Hoffmann

""" Database for the classic route view (hiking, cycling, etc.)
"""
import types

import sqlalchemy as sa

import osgende
from osgende.generic import FilteredTable
from osgende.lines import RelationWayTable, SegmentsTable
from osgende.relations import RelationHierarchy
from osgende.common.tags import TagStore
from wmt_shields import ShieldFactory

from wmt_db.common.route_types import Network
from ..tables.countries import CountryGrid
from ..tables.routes import Routes
from ..tables.guideposts import GuidePosts
from ..tables.networknodes import NetworkNodes
from ..tables.updates import UpdatedGeometriesTable
from ..tables.styles import StyleTable
from ..tables.route_ways import RouteWayTable

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
            conn.execute(sa.text(f"CREATE OR REPLACE VIEW {schema}data_view AS {sql}"))

    def mkshield(self):
        route = self.tables.routes
        rel = self.osmdata.relation.data
        sel = sa.select(rel.c.tags, route.data.c.country, route.data.c.level)\
                .where(rel.c.id == route.data.c.id)

        donesyms = set()

        with self.engine.begin() as conn:
            for r in conn.execution_options(stream_results=True).execute(sel):
                sym = route.symbols.create(TagStore(r.tags), r.country,
                                           style=Network.from_int(r.level).name)

                if sym is not None:
                    symid = sym.uuid()

                    if symid not in donesyms:
                        donesyms.add(symid)
                        sym.to_file(self.site_config.ROUTES.symbol_datadir / f'{symid}.svg', format='svg')


def create_mapdb(site_config, options):
    setattr(options, 'schema', site_config.DB_SCHEMA)
    db = RouteMapDB(options, site_config)

    setup_tables(db)

    return db


def _filtered_table_index(tab, engine):
    sa.Index('idx_filtered_relations_members', tab.c.members,
             postgresql_using='gin').create(engine)

def _segments_table_index(tab, engine):
    sa.Index('idx_segment_rels', tab.c.rels, postgresql_using='gin').create(engine)

def setup_tables(db, route_class=Routes):
    if not db.get_option('no_engine'):
        insp = sa.inspect(db.engine)
        if not insp.has_table(db.site_config.DB_TABLES.country):
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
                                       sa.literal_column(f"({db.site_config.DB_ROUTE_SUBSET})")))
    rfilt.after_construct = types.MethodType(_filtered_table_index, rfilt)

    # Then we create the connection between ways and relations.
    # This also adds geometries.
    relway = db.add_table('relway',
                          RouteWayTable(db.metadata, tabname.way_relation,
                                        db.osmdata.way, rfilt, osmdata=db.osmdata))

    # From that create the segmented table.
    segments = db.add_table('segments',
                            SegmentsTable(db.metadata, tabname.segment, relway,
                                          (relway.c.rels,)))
    segments.after_construct = types.MethodType(_segments_table_index, segments)

    # hierarchy table for super relations
    rtree = db.add_table('hierarchy',
                         RelationHierarchy(db.metadata, tabname.hierarchy, rfilt,
                                           track_changes=True))

    # routes table: information about each route
    routes = db.add_table('routes',
                          route_class(db.metadata, rfilt, relway, rtree,
                                      CountryGrid(sa.MetaData(), tabname.country),
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
                                 db.osmdata.node, sa.text(cfg.node_subset),
                                 view_only=True))
        db.add_table('guideposts', GuidePosts(db.metadata, filt, cfg))\
           .set_update_table(uptable)

        def _add_index(tab, engine):
            tc = db.osmdata.node.c
            where= 'tags @> \'{"tourism": "information", "information": "guidepost"}\'::jsonb'
            sa.Index(f'idx_nodes_guidepost', tc.id,
                     postgresql_where=sa.text(where)).create(engine, checkfirst=True)

        filt.after_construct = types.MethodType(_add_index, filt)

    # optional table for network nodes
    if db.site_config.NETWORKNODES is not None:
        cfg = db.site_config.NETWORKNODES
        filt = db.add_table('nnodes_filter',
                   FilteredTable(db.metadata, cfg.table_name + '_view',
                                 db.osmdata.node,
                                 db.osmdata.node.c.tags.has_key(cfg.node_tag),
                                 view_only=True))
        db.add_table('networknodes', NetworkNodes(db.metadata, filt, cfg))

        def _add_index(tab, engine):
            tc = db.osmdata.node.c
            tag = db.site_config.NETWORKNODES.node_tag
            sa.Index(f'idx_nodes_{tag}', tc.id,
                     postgresql_where=tc.tags.has_key(tag)).create(engine, checkfirst=True)

        filt.after_construct = types.MethodType(_add_index, filt)
