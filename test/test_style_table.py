# SPDX-License-Identifier: GPL-3.0-only
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2020 Sarah Hoffmann

import pytest
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY

from osgende.common.table import TableSource
from osgende.relations import RelationHierarchy
from osgende.osmdata import OsmSourceTables

from wmt_db.tables.updates import UpdatedGeometriesTable
from wmt_db.tables.styles import StyleTable

@pytest.fixture
def route_table(mapdb):
    table = mapdb.add_table('routes',
                TableSource(sa.Table('routes', mapdb.metadata,
                                     sa.Column('id', sa.BigInteger),
                                     sa.Column('name', sa.Text)),
                            change_table='route_changeset'))

    return table


class TestStyleTable:

    class Config:
        table_name = 'test'

        def add_columns(self, table):
            table.append_column(sa.Column('names', ARRAY(sa.String)))

        def new_collector(self):
            return list()

        def add_to_collector(self, seginfo, route):
            seginfo.append(route.name)

        def to_columns(self, seginfo):
            seginfo.sort()
            return dict(names=seginfo)

    @pytest.fixture(autouse=True)
    def init_tables(self, mapdb, route_table, segment_table):
        rels = mapdb.add_table('src_rels',
                   OsmSourceTables.create_relation_table(mapdb.metadata))
        hier = mapdb.add_table('hierarchy',
                   RelationHierarchy(mapdb.metadata, 'hierarchy', rels))
        uptable = mapdb.add_table('updates',
                      UpdatedGeometriesTable(mapdb.metadata, 'updates'))

        mapdb.add_table('test',
                        StyleTable(mapdb.metadata, route_table, segment_table,
                                   hier, self.Config(), uptable))
        mapdb.create()

        mapdb.insert_into('routes')\
            .line(1, name='A')\
            .line(2, name='B')\
            .line(3, name='C')

    def test_single_relation(self, mapdb):
        mapdb.insert_into('ways')\
            .line(1, rels=[1], geom='SRID=4326;LINESTRING(0 0, 0.1 0.1)')

        mapdb.construct()

        mapdb.table_equals('test',
            [dict(id=1, names=['A'], geom='LINESTRING(0 0, 0.1 0.1)')
            ])


    def test_multi_relation(self, mapdb):
        mapdb.insert_into('ways')\
            .line(23, rels=[2, 3], geom='SRID=4326;LINESTRING(0 0, 0.1 0.1)')\
            .line(25, rels=[1, 2, 3], geom='SRID=4326;LINESTRING(1 1, 0.1 0.1)')

        mapdb.construct()

        mapdb.table_equals('test',
            [dict(id=23, names=['B', 'C']),
             dict(id=25, names=['A', 'B', 'C'])
            ])

    def test_updates(self, mapdb):
        mapdb.insert_into('ways')\
            .line(12, rels=[1, 2, 3], geom='SRID=4326;LINESTRING(0 0, 0.1 0.1)')\
            .line(20, rels=[3], geom='SRID=4326;LINESTRING(0 0, 0.1 0.1)')

        mapdb.construct()

        mapdb.table_equals('test',
            [dict(id=12, names=['A', 'B', 'C']),
             dict(id=20, names=['C'])
            ])

        mapdb.modify('ways')\
            .delete(12)\
            .add(13, rels=[1], geom='SRID=4326;LINESTRING(0 0, 0.1 0.1)')

        mapdb.modify('routes').modify(3, name='X')

        mapdb.update()

        mapdb.table_equals('test',
            [dict(id=13, names=['A']),
             dict(id=20, names=['X'])])

    def test_hierarchy(self, mapdb):
        mapdb.insert_into('src_rels')\
            .line(1, tags={}, members=[dict(id=2, role='', type='R')])

        mapdb.insert_into('ways')\
            .line(10, rels=[1], geom='SRID=4326;LINESTRING(0 0, 0.1 0.1)')\
            .line(11, rels=[2], geom='SRID=4326;LINESTRING(0 0, 0.1 0.1)')

        mapdb.construct()

        mapdb.table_equals('test',
            [dict(id=10, names=['A']),
             dict(id=11, names=['A', 'B'])
            ])

        mapdb.modify('src_rels')\
            .delete(1)\
            .add(2, tags={}, members=[dict(id=1, role='', type='R')])

        mapdb.modify('ways')\
            .modify(10, rels=[1], geom='SRID=4326;LINESTRING(0 0, 0.1 0.1)')\
            .modify(11, rels=[2], geom='SRID=4326;LINESTRING(0 0, 0.1 0.1)')

        mapdb.update()

        mapdb.table_equals('test',
            [dict(id=10, names=['A', 'B']),
             dict(id=11, names=['B'])
            ])
