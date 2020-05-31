# SPDX-License-Identifier: GPL-3.0-only
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2018-2020 Sarah Hoffmann

""" Database for the classic route view (hiking, cycling, etc.)
"""
from collections import namedtuple, OrderedDict

import osgende
from osgende.generic import FilteredTable
from osgende.lines import RelationWayTable, SegmentsTable
from osgende.relations import RelationHierarchy
from osgende.common.tags import TagStore
from wmt_shields import ShieldFactory

from sqlalchemy import MetaData, select, text

from db.tables.countries import CountryGrid
from db.tables.routes import Routes
from db.tables.route_nodes import GuidePosts, NetworkNodes
from db.tables.updates import UpdatedGeometriesTable
from db.tables.styles import StyleTable


class DB(osgende.MapDB):

    def __init__(self, site_config, options):
        self.site_config = site_config
        setattr(options, 'schema', site_config.DB_SCHEMA)
        osgende.MapDB.__init__(self, options)

        if not self.get_option('no_engine'):
            country = CountryGrid(MetaData(), site_config.DB_TABLES.country)
            if not country.data.exists(self.engine):
                raise RuntimeError("No country table found.")

    def create_table_dict(self, symbol_factory, route_class=Routes):
        self.metadata.info['srid'] = self.site_config.DB_SRID
        self.metadata.info['num_threads'] = self.get_option('numthreads')

        tabname = self.site_config.DB_TABLES

        tables = OrderedDict()
        # first the update table: stores all modified routes, points
        uptable = UpdatedGeometriesTable(self.metadata, tabname.change)
        tables['updates'] = uptable

        # First we filter all route relations into an extra table.
        rfilt = FilteredTable(self.metadata, tabname.route_filter,
                              self.osmdata.relation,
                              text("(%s)" % self.site_config.DB_ROUTE_SUBSET))
        tables['relfilter'] = rfilt

        # Then we create the connection between ways and relations.
        # This also adds geometries.
        relway = RelationWayTable(self.metadata, tabname.way_relation,
                                  self.osmdata.way, rfilt, osmdata=self.osmdata)
        tables['relway'] = relway

        # From that create the segmented table.
        segments = SegmentsTable(self.metadata, tabname.segment, relway,
                                 (relway.c.rels,))
        tables['segments'] = segments

        # hierarchy table for super relations
        rtree = RelationHierarchy(self.metadata, tabname.hierarchy, rfilt)
        tables['hierarchy'] = rtree

        # routes table: information about each route
        routes = route_class(self.metadata, rfilt, relway, rtree,
                             CountryGrid(MetaData(), tabname.country),
                             self.site_config.ROUTES, symbol_factory)
        tables['routes'] = routes

        # finally the style table for rendering
        style = StyleTable(self.metadata, routes, segments, rtree,
                           self.site_config.DEFSTYLE, uptable)
        tables['style'] = style

        # optional table for guide posts
        if self.site_config.GUIDEPOSTS is not None:
            cfg = self.site_config.GUIDEPOSTS
            filt = FilteredTable(self.metadata, cfg.table_name + '_view',
                                 self.osmdata.node, text(cfg.node_subset),
                                 view_only=True)
            tables['gp_filter'] = filt
            tables['guideposts'] = GuidePosts(self.metadata, filt, cfg)

        # optional table for network nodes
        if self.site_config.NETWORKNODES is not None:
            cfg = self.site_config.NETWORKNODES
            filt = FilteredTable(self.metadata, cfg.table_name + '_view',
                                 self.osmdata.node,
                                 self.osmdata.node.c.tags.has_key(cfg.node_tag),
                                 view_only=True)
            tables['nnodes_filter'] = filt
            tables['networknodes'] = NetworkNodes(self.metadata, filt, cfg)

        return tables

    def create_tables(self):
        symbol_factory = ShieldFactory(self.site_config.ROUTES.symbols,
                                       self.site_config.SYMBOLS)
        tables = self.create_table_dict(symbol_factory)

        _RouteTables = namedtuple('_RouteTables', tables.keys())

        return _RouteTables(**tables)

    def dataview(self):
        schema = self.get_option('schema', '')
        if schema:
            schema += '.'
        with self.engine.begin() as conn:
            conn.execute("""CREATE OR REPLACE VIEW %sdata_view AS
                            SELECT geom FROM %s%s"""
                         % (schema, schema, str(self.tables.style.data.name)))

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


