# SPDX-License-Identifier: GPL-3.0-only
#
# This file is part of Waymarked Trails
# Copyright (C) 2020 Sarah Hoffmann

import os
import dataclasses
from typing import Dict, List, Union

import sqlalchemy as sa
from sqlalchemy.sql import functions as saf
from sqlalchemy.dialects.postgresql import JSONB
from geoalchemy2 import Geometry

from osgende.common.table import TableSource
from osgende.common.sqlalchemy import DropIndexIfExists, CreateTableAs
from osgende.common.threads import ThreadableDBObject
from osgende.common.tags import TagStore

from ..common.route_types import Network
from ..common.data_transforms import make_itinerary, make_geometry

@dataclasses.dataclass
class RouteRow:
    id: int
    name: Union[None, str]
    intnames: Union[None, Dict[str, str]]
    ref: Union[None, str]
    itinerary: Union[None, List[str]]
    symbol: Union[None, str] = None
    country: Union[None, str] = None
    network: Union[None, str] = None
    level: int = Network.LOC()
    top: bool = True


class Routes(ThreadableDBObject, TableSource):
    """ Table that creates information about the routes. This includes
        general information as well as the geometry.
    """

    def __init__(self, meta, relations, ways, hierarchy, countries, config,
                 shield_factory):
        table = sa.Table(config.table_name, meta,
                         sa.Column('id', sa.BigInteger,
                                   primary_key=True, autoincrement=False),
                         sa.Column('name', sa.String),
                         sa.Column('intnames', JSONB),
                         sa.Column('ref', sa.String),
                         sa.Column('itinerary', JSONB),
                         sa.Column('symbol', sa.String),
                         sa.Column('country', sa.String),
                         sa.Column('network', sa.String),
                         sa.Column('level', sa.SmallInteger),
                         sa.Column('top', sa.Boolean),
                         sa.Column('geom', Geometry('GEOMETRY', srid=ways.srid)))

        super().__init__(table, relations.change)

        self.config = config

        self.rels = relations
        self.ways = ways
        self.rtree = hierarchy
        self.countries = countries

        self.symbols = shield_factory

        self.numthreads = meta.info.get('num_threads', 1)

    def _compute_route_level(self, network):
        # Multi-modal routes might have multiple network tags
        for n in network.split(';'):
            if n in self.config.network_map:
                return self.config.network_map[n]

        return Network.LOC()


    def _insert_objects(self, conn, subsel=None):
        h = self.rtree.data
        max_depth = conn.scalar(sa.select([saf.max(h.c.depth)]))

        subtab = sa.select([h.c.child, saf.max(h.c.depth).label("lvl")])\
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
                self.insert_objects(conn, subset)

        # Lastly, process all routes that are nobody's child.
        subset = self.rels.data.select()\
                 .where(self.rels.c.id.notin_(
                     sa.select([h.c.child], distinct=True).as_scalar()))
        if subsel is not None:
            subset = subset.where(subsel)
        self.insert_objects(conn, subset)


    def construct(self, engine):
        idx = sa.Index(self.data.name + '_iname_idx', sa.func.upper(self.data.c.name))

        with engine.begin() as conn:
            conn.execute(DropIndexIfExists(idx))
            self.truncate(conn)

        self._insert_objects(engine)

        with engine.begin() as conn:
            idx.create(conn)

    def update(self, engine):
        with engine.begin() as conn:
            # delete removed relations
            conn.execute(self.delete(self.rels.select_delete()))
            # collect all changed relations in a temporary table
            # 1. relations added or modified
            sels = [sa.select([self.rels.cc.id])]
            # 2. relations with modified geometries
            w = self.ways
            sels.append(sa.select([saf.func.unnest(w.c.rels).label('id')], distinct=True)
                          .where(w.c.id.in_(w.select_add_modify())))

            conn.execute('DROP TABLE IF EXISTS __tmp_osgende_routes_updaterels')
            conn.execute(CreateTableAs('__tmp_osgende_routes_updaterels',
                         sa.union(*sels), temporary=False))
            tmp_rels = sa.Table('__tmp_osgende_routes_updaterels',
                                sa.MetaData(), autoload_with=conn)

            # 3. parent relation of all of them
            conn.execute(tmp_rels.insert().from_select(tmp_rels.c,
                sa.select([self.rtree.c.parent], distinct=True)
                  .where(self.rtree.c.child.in_(sa.select([tmp_rels.c.id])))))

            # and insert/update all
            self._insert_objects(conn, self.rels.c.id.in_(tmp_rels.select()))

            tmp_rels.drop(conn)

    def insert_objects(self, engine, subset):
        res = engine.execution_options(stream_results=True).execute(subset)

        workers = self.create_worker_queue(engine, self._process_construct_next)
        for obj in res:
            workers.add_task(obj)

        workers.finish()


    def _process_construct_next(self, obj):
        cols = self._construct_row(obj, self.thread.conn)

        if cols is not None:
            print(cols)
            print([(k, type(v)) for k, v in cols.items()])
            sql = self.upsert_data().values(cols)
            self.thread.conn.execute(sql)
        else:
            self.thread.conn.execute(self.data.delete().where(self.c.id == obj['id']))

    def _filter_members(self, oid, members):
        """ Extract relation members and checks and breaks relation
            member cycles.
        """
        relids = [r['id'] for r in members if r['type'] == 'R']

        if relids:
            # Is this relation part of a cycle? Then drop the relation members
            # to not get us in trouble with geometry building.
            h1 = self.rtree.data.alias()
            h2 = self.rtree.data.alias()
            sql = sa.select([h1.c.parent])\
                    .where(h1.c.parent == oid)\
                    .where(h1.c.child == h2.c.parent)\
                    .where(h2.c.child == oid)
            if (self.thread.conn.execute(sql).rowcount > 0):
                members = [m for m in members if m['type'] == 'W']
                relids = []

        return members, relids


    def _construct_row(self, obj, conn):
        tags = TagStore(obj['tags'])
        is_node_network = tags.get('network:type') == 'node_network'

        outtags = RouteRow(
            id=obj['id'],
            name=tags.get('name'),
            ref=tags.get('ref'),
            intnames=tags.get_prefixed('name:'),
            itinerary=make_itinerary(tags)
        )

        if 'symbol' in tags:
            outtags.intnames['symbol'] = tags['symbol']

        if is_node_network:
            outtags.level = Network.LOC.min()
        elif 'network' in tags:
            outtags.level = self._compute_route_level(tags['network'])

        # child relations
        members, relids = self._filter_members(obj['id'], obj['members'])

        # geometry
        geom = make_geometry(conn, members, self.ways, self.data)

        if geom is None:
            return None

        # find the country
        if relids:
            sel = sa.select([self.c.country], distinct=True)\
                    .where(self.c.id.in_(relids))
        else:
            c = self.countries
            sel = sa.select([c.column_cc()], distinct=True)\
                    .where(c.column_geom().ST_Intersects(geom))

        cur = self.thread.conn.execute(sel)

        # should be counting when rowcount > 1
        if cur.rowcount >= 1:
            cntry = cur.scalar()
        else:
            cntry = None

        outtags.country = cntry

        sym = self.symbols.create(tags, cntry,
                                  style=Network.from_int(outtags.level).name)
        if sym is None:
            outtags.symbol = 'None'
        else:
            outtags.symbol = sym.uuid()
            sym.to_file(os.path.join(self.config.symbol_datadir,
                                     outtags.symbol + '.svg'), format='svg')

        # custom filter callback
        if self.config.tag_filter is not None:
            self.config.tag_filter(outtags, tags)

        if outtags.network is None and is_node_network:
            outtags.network = 'NDS'

        if 'network' in tags and not is_node_network:
            h = self.rtree.data
            r = self.rels.data
            sel = sa.select([sa.text("'a'")])\
                    .where(h.c.child == obj['id'])\
                    .where(r.c.id == h.c.parent)\
                    .where(h.c.depth == 2)\
                    .where(r.c.tags['network'].astext == tags['network'])\
                    .limit(1)

            top = self.thread.conn.scalar(sel)

            outtags.top = (top is None)

        outtags = dataclasses.asdict(outtags)
        outtags['geom'] = geom

        return outtags
