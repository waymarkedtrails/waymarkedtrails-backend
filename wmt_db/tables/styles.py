# SPDX-License-Identifier: GPL-3.0-only
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2018-2023 Sarah Hoffmann

import sqlalchemy as sa
from geoalchemy2 import Geometry

from osgende.common.table import TableSource
from osgende.common.threads import ThreadableDBObject

class StyleTable(ThreadableDBObject, TableSource):
    """ Generic way table with styling information.
    """
    def __init__(self, meta, routes, segments, hierarchy, style_config, uptable):
        self.config = style_config
        srid = segments.srid

        table = sa.Table(self.config.table_name, meta,
                         sa.Column('id', sa.BigInteger,
                                   primary_key=True, autoincrement=False),
                         sa.Column('geom', Geometry('LINESTRING', srid=srid)),
                         sa.Column('geom100', Geometry('LINESTRING', srid=srid))
                         )

        self.config.add_columns(table)

        super().__init__(table, segments.change)

        self.rels = routes
        self.ways = segments
        self.rtree = hierarchy
        if self.rtree.change is None:
            raise RuntimeError("Hierarchy table is missing changes.")

        # table that holds geometry updates
        self.uptable = uptable

        self.numthreads = meta.info.get('num_threads', 1)

    def construct(self, engine):
        self.route_cache = {}
        self.synchronize_ways(engine)
        del self.route_cache
        self.copy_geometries(engine)

    def before_update(self, engine):
        # save all old geometries that will be deleted
        sql = sa.select(self.c.geom)\
                .where(self.c.id.in_(self.ways.select_delete()))
        self.uptable.add_from_select(engine, sql)

    def update(self, engine):
        self.route_cache = {}
        with engine.begin() as conn:
            conn.execute(self.data.delete()
                             .where(self.c.id.in_(self.ways.select_delete())))
        self.synchronize_ways(engine, self.ways.c.id.in_(self.ways.select_add_modify()))
        self.synchronize_rels(engine)
        del self.route_cache
        self.copy_geometries(engine)

    def after_update(self, engine):
        # save all new and modified geometries
        sql = sa.select(self.c.geom)\
                .where(self.c.id.in_(self.ways.select_add_modify()))
        self.uptable.add_from_select(engine, sql)


    def synchronize_ways(self, engine, subset=None):
        sql = self._synchronise_sql()
        if subset is not None:
            sql = sql.where(subset)

        route_sql = sa.select(*(c for c in self.rels.c if c.name != 'geom'))

        with engine.begin() as conn:
            workers = self.create_worker_queue(engine, self._process_construct_next)
            cache_todo = set()
            workers_todo = []

            with engine.execution_options(stream_results=True).begin() as wconn:
                for obj in wconn.execute(sql):
                    # build cache in the main thread, so that workers only read
                    cache_todo.update([x for x in obj.rels
                                       if x not in self.route_cache])
                    workers_todo.append(obj)
                    # We don't want an extra query for each relation, so collect
                    # a couple of todos.
                    if len(cache_todo) > 20:
                        subres = conn.execute(route_sql.where(self.rels.c.id.in_(cache_todo)))
                        for route in subres:
                            self.route_cache[route.id] = route
                        for w in workers_todo:
                            workers.add_task(w)
                        cache_todo = set()
                        workers_todo = []

            # add the remaining stuff
            if cache_todo:
                subres = conn.execute(route_sql.where(self.rels.c.id.in_(cache_todo)))
                for route in subres:
                    self.route_cache[route.id] = route

            for w in workers_todo:
                workers.add_task(w)

            workers.finish()

    def synchronize_rels(self, engine):
        # select ways with changed rels joined with data with geom not null
        hd = self.rtree.change

        relset = sa.union(
            self.rels.select_add_modify(),
            sa.select(hd.c.child)
              .where(hd.c.parent == sa.func.any(sa.select(self.rels.change.c.id).scalar_subquery()))
        )

        sql = self._synchronise_sql([c for c in self.c
                                     if c.name not in ('id', 'geom')])\
                .where(self.ways.c.rels.op('&& ARRAY')(relset.scalar_subquery()))\
                .where(self.ways.c.id == self.c.id)\
                .where(self.c.geom is not None)

        route_sql = sa.select(*(c for c in self.rels.c if c.name != 'geom'))

        with engine.begin() as conn:
            workers = self.create_worker_queue(engine, self._process_rel_segment)

            with engine.execution_options(stream_results=True).begin() as wconn:
                for obj in wconn.execute(sql):
                    missing = [x for x in obj.rels if x not in self.route_cache]
                    if missing:
                        subres = conn.execute(route_sql.where(self.rels.c.id.in_(missing)))
                        for route in subres:
                            self.route_cache[route.id] = route
                    workers.add_task(obj)

            workers.finish()


    def copy_geometries(self, engine):
        """ Update all missing geometries from the way source.
        """
        m = self.ways
        sql = self.data.update().values(geom=m.c.geom.ST_Simplify(1),
                                        geom100=m.c.geom.ST_Simplify(100))\
                                .where(self.data.c.geom == None)\
                                .where(self.data.c.id == m.c.id)
        with engine.begin() as conn:
            conn.execute(sql)

    def _synchronise_sql(self, add_rows=None):
        h = self.rtree
        m = self.ways
        parents = sa.select(h.c.parent)\
                      .where(h.c.child == sa.func.any(m.c.rels))\
                      .distinct().scalar_subquery()

        rows = [m.c.id, (m.c.rels + sa.func.array(parents)).label('rels')]
        if add_rows is not None:
            rows.extend(add_rows)

        return sa.select(*rows)


    def _process_construct_next(self, obj):
        cols = self._construct_row(obj)
        self.thread.conn.execute(self.upsert_data().values(cols))


    def _process_rel_segment(self, obj):
        cols = self._construct_row(obj, extra_data=False)

        for k, v in cols.items():
            objval = obj._mapping[k]
            if v is None:
                if objval is None:
                    continue
                else:
                    break
            if v is not None and objval is None:
                break
            if isinstance(v, list):
                if set(v) != set(objval):
                    break
            else:
                if v != objval:
                    break
        else:
            return

        self.thread.conn.execute(self.data.update().values(cols)
                                     .where(self.data.c.id == obj.id))
        self.uptable.add(self.thread.conn, obj.geom100)


    def _construct_row(self, obj, extra_data=True):
        seginfo = self.config.new_collector()
        for rel in obj.rels:
            if rel not in self.route_cache:
                print("Warning: no information for relation", rel)
            else:
                self.config.add_to_collector(seginfo, self.route_cache[rel])

        outdata = self.config.to_columns(seginfo)
        if extra_data:
            outdata['id'] = obj.id
            outdata['geom'] = None
            outdata['geom100'] = None

        return outdata
