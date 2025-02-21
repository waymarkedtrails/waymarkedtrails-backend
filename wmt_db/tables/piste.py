# SPDX-License-Identifier: GPL-3.0-only
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2015 Michael Spreng
#               2018-2023 Sarah Hoffmann
""" Customized tables for piste routes and ways.
"""

import os

import sqlalchemy as sa
from sqlalchemy.sql import functions as saf
from sqlalchemy.dialects.postgresql import JSONB
from geoalchemy2 import Geometry

from osgende.common.table import TableSource
from osgende.common.sqlalchemy import DropIndexIfExists, CreateTableAs
from osgende.common.threads import ThreadableDBObject
from osgende.common.tags import TagStore
from osgende.lines import PlainWayTable

from ..common.data_transforms import make_geometry
from ..geometry.route_builder import build_route
from ..geometry.member_loader import get_relation_objects

def _add_piste_columns(table, name):
    table.append_column(sa.Column('name', sa.String))
    table.append_column(sa.Column('ref', sa.String))
    table.append_column(sa.Column('symbol', sa.String))
    table.append_column(sa.Column('difficulty', sa.SmallInteger))
    table.append_column(sa.Column('piste', sa.SmallInteger))
    table.append_column(sa.Column('intnames', JSONB))
    table.append_column(sa.Column('tags', JSONB))
    table.append_column(sa.Index(f'idx_{name}_iname', sa.text('upper(name)')))

def write_symbol(factory, tags, difficulty, datadir):
    sym = factory.create(tags, '', difficulty=difficulty)
    if sym is None:
        return 'None'

    symname = sym.uuid()
    sym.to_file(datadir / f'{symname}.svg', format='svg')
    return symname


def basic_tag_transform(tags: TagStore, config):
    difficulty = tags.get('piste:difficulty')
    difficulty = config.difficulty_map.get(difficulty, 0)

    return dict(
        intnames=tags.get_prefixed('name:'),
        name=tags.firstof('piste:name', 'name'),
        ref=tags.firstof('piste:ref', 'ref'),
        difficulty=difficulty,
        piste=config.piste_type.get(tags.get('piste:type'), 0),
        tags=tags
    )


class PisteRoutes(ThreadableDBObject, TableSource):
    """ Table that creates information about the routes. This includes
        general information as well as the geometry.
    """

    def __init__(self, meta, relations, ways, hierarchy, countries, config,
                 shield_factory):
        table = sa.Table(config.table_name, meta)
        table.append_column(sa.Column('id', sa.BigInteger,
                                      primary_key=True, autoincrement=False))
        table.append_column(sa.Column('top', sa.Boolean))
        _add_piste_columns(table, config.table_name)
        table.append_column(sa.Column('route', sa.String))
        table.append_column(sa.Column('linear', sa.String))
        table.append_column(sa.Column('geom', Geometry('GEOMETRY', srid=ways.srid)))
        table.append_column(sa.Column('render_geom', Geometry('GEOMETRY', srid=ways.srid)))

        super().__init__(table, relations.change)

        self.config = config

        self.rels = relations
        self.ways = ways
        self.rtree = hierarchy
        self.countries = countries

        self.shield_fab = shield_factory


    def _insert_objects(self, engine, subsel=None):
        h = self.rtree.data
        with engine.begin() as conn:
            max_depth = conn.scalar(sa.select(saf.max(h.c.depth)))

        subtab = sa.select(h.c.child, saf.max(h.c.depth).label("lvl"))\
                   .group_by(h.c.child).alias()

        # Process relations by hierarchy, starting with the highest depth.
        # This guarantees that the geometry of member relations is already
        # available for processing the relation geometry.
        if max_depth is not None:
            for level in range(max_depth, 1, -1):
                subset = self.rels.data.select()\
                          .where(subtab.c.lvl == level)\
                          .where(self.rels.c.id == subtab.c.child)
                if subsel is not None:
                    subset = subset.where(subsel)
                self.insert_objects(engine, subset)

        # Lastly, process all routes that are nobody's child.
        subset = self.rels.data.select()\
                 .where(self.rels.c.id.notin_(
                     sa.select(h.c.child).distinct().scalar_subquery()))
        self.insert_objects(engine, subset)


    def construct(self, engine):
        h = self.rtree.data
        idx = sa.Index(self.data.name + '_iname_idx', sa.func.upper(self.c.name))

        with engine.begin() as conn:
            conn.execute(DropIndexIfExists(idx))
            self.truncate(conn)

            max_depth = conn.scalar(sa.select(saf.max(h.c.depth)))

        subtab = sa.select(h.c.child, saf.max(h.c.depth).label("lvl"))\
                   .group_by(h.c.child).alias()

        # Process relations by hierarchy, starting with the highest depth.
        # This guarantees that the geometry of member relations is already
        # available for processing the relation geometry.
        if max_depth is not None:
            for level in range(max_depth, 1, -1):
                subset = self.rels.data.select()\
                          .where(subtab.c.lvl == level)\
                          .where(self.rels.c.id == subtab.c.child)
                self.insert_objects(engine, subset)

        # Lastly, process all routes that are nobody's child.
        subset = self.rels.data.select()\
                 .where(self.rels.c.id.notin_(
                     sa.select(h.c.child).distinct().scalar_subquery()))
        self.insert_objects(engine, subset)

        idx.create(engine)

    def update(self, engine):
        with engine.begin() as conn:
            # delete removed relations
            conn.execute(self.delete(self.rels.select_delete()))
            # collect all changed relations in a temporary table
            # 1. relations added or modified
            sels = [sa.select(self.rels.cc.id)]
            # 2. relations with modified geometries
            w = self.ways
            sels.append(sa.select(saf.func.unnest(w.c.rels).label('id')).distinct()
                          .where(w.c.id.in_(w.select_add_modify())))

            conn.execute(sa.text('DROP TABLE IF EXISTS __tmp_osgende_routes_updaterels'))
            conn.execute(CreateTableAs('__tmp_osgende_routes_updaterels',
                                       sa.union(*sels), temporary=False))
            tmp_rels = sa.Table('__tmp_osgende_routes_updaterels',
                                sa.MetaData(), autoload_with=conn)

            # 3. parent relation of all of them
            conn.execute(tmp_rels.insert().from_select(tmp_rels.c,
                sa.select(self.rtree.c.parent).distinct()
                  .where(self.rtree.c.child.in_(sa.select(tmp_rels.c.id)))))

        # and insert/update all
        self._insert_objects(engine, self.rels.c.id.in_(tmp_rels.select()))

        with engine.begin() as conn:
            tmp_rels.drop(conn)

    def insert_objects(self, engine, subset):
        workers = self.create_worker_queue(engine, self._process_construct_next)

        with engine.execution_options(stream_results=True).begin() as conn:
            for obj in conn.execute(subset):
                workers.add_task(obj)

        workers.finish()


    def _process_construct_next(self, obj):
        cols = self._construct_row(obj, self.thread.conn)

        if cols is not None:
            self.thread.conn.execute(self.upsert_data().values(cols))

    def _construct_row(self, obj, conn):
        tags = TagStore(obj.tags)

        outtags = basic_tag_transform(TagStore(obj.tags), self.config)

        # we don't support hierarchy at the moment
        outtags['top'] = True

        # geometry
        geom, render_geom = make_geometry(conn, obj.members, self.ways, self.data)

        if geom is None:
            return None

        route_members = get_relation_objects(conn, obj.members, self.ways, self.data)
        assert len(route_members) > 0
        route = build_route(route_members)

        outtags['geom'] = geom
        outtags['render_geom'] = render_geom
        outtags['route'] = route.to_json()
        outtags['linear'] = route.get_linear_state()
        outtags['symbol'] = write_symbol(self.shield_fab, tags,
                                         outtags['difficulty'],
                                         self.config.symbol_datadir)
        outtags['id'] = obj.id

        return outtags


class PisteWayInfo(PlainWayTable):

    def __init__(self, meta, name, source, osmdata, uptable, config, shield_factory):
        super().__init__(meta, name, source, osmdata)
        self.config = config
        self.shield_fab = shield_factory
        self.uptable = uptable

    def add_columns(self, dest, src):
        _add_piste_columns(dest, 'piste_way_info')

    def before_update(self, engine):
        # save all old geometries that will be deleted
        sql = sa.select(self.c.geom)\
                .where(self.c.id.in_(self.src.select_delete()))
        self.uptable.add_from_select(engine, sql)

    def after_update(self, engine):
        # save all new and modified geometries
        sql = sa.select(self.c.geom)\
                .where(self.c.id.in_(self.src.select_add_modify()))
        self.uptable.add_from_select(engine, sql)

    def transform_tags(self, obj):
        tags = TagStore(obj.tags)

        outtags = basic_tag_transform(tags, self.config)
        outtags['symbol'] = write_symbol(self.shield_fab, tags,
                                         outtags['difficulty'],
                                         self.config.symbol_datadir)

        return outtags
