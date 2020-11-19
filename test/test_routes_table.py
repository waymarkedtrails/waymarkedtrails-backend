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

from wmt_db.tables.routes import Routes
from wmt_db.common.route_types import Network

@pytest.fixture
def tags():
    def _make_tags(**kwargs):
        tags = dict(type='route', route='hiking')
        tags.update(kwargs)
        return tags

    return _make_tags

@pytest.fixture
def members(mapdb):
    mapdb.insert_into('ways')\
       .line(1, rels=[1], nodes=[1,2,3], geom='SRID=4326;LINESTRING(0 0, 0.1 0.1)')

    return (dict(id=1, role='', type='W'),)

class TestRoutesTable:

    class Config:
        table_name = 'test'
        network_map = dict(iwn=Network.INT(), nwn=Network.NAT(),
                           rwn=Network.REG(), lwn=Network.LOC())
        symbol_datadir =  ''
        tag_filter = None


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
                   Routes(mapdb.metadata, rels, ways, hier,
                          countries, self.Config, shields))
        mapdb.create()


    def test_names(self, mapdb, tags, members):
        mapdb.insert_into('src_rels')\
            .line(1, tags=tags(name='Barn Route'), members=members)\
            .line(2, tags=tags(ref='CN1'), members=members)\
            .line(3, tags={'name:de' : 'Bergweg', 'name:en' : 'Mountain Road',
                           'name' : 'all'}, members=members)\
            .line(4, tags=tags(symbol='grüner Strich'), members=members)

        mapdb.construct()

        mapdb.table_equals('test',
            [dict(id=1, name='Barn Route', ref=None, intnames={}),
             dict(id=2, name=None, ref='CN1', intnames={}),
             dict(id=3, name='all', ref=None,
                  intnames=dict(de='Bergweg', en='Mountain Road')),
             dict(id=4, name=None, ref=None, intnames=dict(symbol='grüner Strich'))
            ])


    def test_networks(self, mapdb, tags, members):
        mapdb.insert_into('src_rels')\
            .line(1, tags=tags(), members=members)\
            .line(2, tags=tags(network='iwn'), members=members)\
            .line(3, tags=tags(network='foo,rwn'), members=members)\
            .line(4, tags=tags(network='lcn;nwn'), members=members)

        mapdb.construct()

        mapdb.table_equals('test',
            [dict(id=1, level=Network.LOC()),
             dict(id=2, level=Network.INT()),
             dict(id=3, level=Network.LOC()),
             dict(id=4, level=Network.NAT())
            ])

    def test_itinerary(self, mapdb, tags, members):
        mapdb.insert_into('src_rels')\
            .line(100, tags=tags(), members=members)\
            .line(101, tags=tags(to='France'), members=members)\
            .line(102, tags={'from': 'Germany'}, members=members)\
            .line(103, tags=tags(via='Canal'), members=members)\
            .line(104, tags=tags(via='A;B'), members=members)\
            .line(105, tags=tags(via='New-York - Rio - Tokyo'), members=members)\
            .line(106, tags={'from': 'Amsterdam', 'to': 'London', 'via': 'Dover'},
                  members=members)

        mapdb.construct()

        mapdb.table_equals('test',
            [dict(id=101, itinerary=['France']),
             dict(id=102, itinerary=['Germany']),
             dict(id=103, itinerary=['Canal']),
             dict(id=104, itinerary=['A', 'B']),
             dict(id=105, itinerary=['New-York', 'Rio', 'Tokyo']),
             dict(id=106, itinerary=['Amsterdam', 'Dover', 'London']),
             dict(id=100, itinerary=None),
            ])

    def test_node_network(self, mapdb, tags, members):
        mapdb.insert_into('src_rels')\
            .line(1, tags={'network:type': 'node_network'}, members=members)

        mapdb.construct()

        mapdb.table_equals('test',
            [dict(id=1, level=0, network='NDS', top=True)])

    def test_simple_update(self, mapdb, tags, members):
        mapdb.insert_into('src_rels')\
            .line(1, tags=tags(name='Old Route'), members=members)\
            .line(2, tags=tags(ref='1'), members=members)

        mapdb.construct()

        mapdb.table_equals('test', [
            dict(id=1, name='Old Route'),
            dict(id=2, ref='1', name=None)
            ])

        mapdb.modify('src_rels')\
            .delete(1)\
            .add(100, tags=tags(name='New Route'), members=members)\
            .modify(2, tags=tags(name='1'), members=members)

        mapdb.update()

        mapdb.table_equals('test', [
            dict(id=100, name='New Route'),
            dict(id=2, name='1', ref=None)
            ])
