# SPDX-License-Identifier: GPL-3.0-only
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2020 Sarah Hoffmann

import pytest
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY
from geoalchemy2 import Geometry

from osgende.relations import RelationHierarchy
from osgende.osmdata import OsmSourceTables
from osgende.common.table import TableSource

from wmt_db.tables.piste import PisteRoutes
from wmt_db.common.route_types import Network
from wmt_db.config.common import PisteTableConfig

@pytest.fixture
def tags():
    def _make_tags(**kwargs):
        tags = dict(type='route', route='ski')
        tags.update(kwargs)
        return tags

    return _make_tags

@pytest.fixture
def members(mapdb):
    mapdb.insert_into('ways')\
       .line(1, rels=[1], nodes=[1,2,3], geom='SRID=4326;LINESTRING(0 0, 0.1 0.1)')

    return (dict(id=1, role='', type='W'),)


class TestPisteTable:

    class Config(PisteTableConfig):
        table_name = 'test'
        symbol_datadir = ''

    @pytest.fixture(autouse=True)
    def init_tables(self, mapdb, countries, shields):
        rels = mapdb.add_table('src_rels',
                   OsmSourceTables.create_relation_table(mapdb.metadata))
        ways = mapdb.add_table('ways',
                   TableSource(sa.Table('ways', mapdb.metadata,
                                        sa.Column('id', sa.BigInteger),
                                        sa.Column('nodes', ARRAY(sa.BigInteger)),
                                        sa.Column('rels', ARRAY(sa.BigInteger)),
                                        sa.Column('geom', Geometry('LINESTRING', 4326))
                                       ), change_table='way_changeset'))
        ways.srid = 4326
        hier = mapdb.add_table('hierarchy',
                   RelationHierarchy(mapdb.metadata, 'hierarchy', rels))
        mapdb.add_table('test',
                   PisteRoutes(mapdb.metadata, rels, ways, hier,
                               countries, self.Config, shields))
        mapdb.create()

    def test_names(self, mapdb, tags, members):
        mapdb.insert_into('src_rels')\
            .line(1, tags=tags(), members=members)\
            .line(2, tags={'piste:name' : 'A', 'name' : 'B'}, members=members)\
            .line(3, tags={'piste:ref' : 'A', 'ref' : 'B'}, members=members)\
            .line(4, tags={'name': 'Zzz', 'ref': '45'}, members=members)\
            .line(5, tags={'ref': '3'}, members=members)\

        mapdb.construct()

        mapdb.table_equals('test',
            [dict(id=1, name=None),
             dict(id=2, name='A'),
             dict(id=3, name='[A]'),
             dict(id=4, name='Zzz'),
             dict(id=5, name='[3]'),
            ])

    def test_simple_update(self, mapdb, tags, members):
        mapdb.insert_into('src_rels')\
            .line(1, tags=tags(), members=members)\
            .line(2, tags={'piste:name' : 'A', 'name' : 'B'}, members=members)

        mapdb.construct()

        mapdb.table_equals('test',
            [dict(id=1, name=None),
             dict(id=2, name='A')])

        mapdb.modify('src_rels')\
            .delete(2)\
            .modify(1, tags=tags(name='FastSki'), members=members)\
            .add(3, tags=tags(ref='23'), members=members)

        mapdb.update()

        mapdb.table_equals('test',
            [dict(id=1, name='FastSki'),
             dict(id=3, name='[23]')])
