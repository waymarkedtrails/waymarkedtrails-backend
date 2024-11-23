# SPDX-License-Identifier: GPL-3.0-or-later
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2024 Sarah Hoffmann
import pytest

from osgende.osmdata import OsmSourceTables
from osgende.common.tags import TagStore

from wmt_db.tables.route_ways import RouteWayTable
from wmt_db.geometry import get_relation_objects
from wmt_db.geometry.route_types import BaseWay

class TestGetRelationObjects:

    @pytest.fixture(autouse=True)
    def init_tables(self, mapdb):
        rels = mapdb.add_table('src_rels',
                   OsmSourceTables.create_relation_table(mapdb.metadata))
        ways = mapdb.add_table('src_ways',
                   OsmSourceTables.create_way_table(mapdb.metadata))
        mapdb.add_table('ways',
                        RouteWayTable(mapdb.metadata, 'way_rels', ways, rels,
                                      osmdata=mapdb.osmdata))

        mapdb.create()


    def run_test(self, mapdb, members):
        member_dict = [{'type': m[0], 'id': m[1], 'role': m[2]} for m in members]
        with mapdb.engine.begin() as conn:
            return get_relation_objects(conn, member_dict,
                                        mapdb.tables['ways'],
                                        mapdb.tables['ways'])


    @pytest.mark.parametrize('role', ['', 'main'])
    def test_simple_way(self, mapdb, role):
        mapdb.insert_into('ways')\
            .line(1, geom='LINESTRING(0 0, 0.1 0.1)', tags={'foo': 'bar'})

        objs = self.run_test(mapdb, [('W', 1, role)])

        assert len(objs) == 1

        result = objs[0]
        assert result.osm_id == 1
        assert result.tags == TagStore({'foo': 'bar'})
        assert result.direction == 0
        assert result.role == ''
        assert result.geom.wkt == 'LINESTRING (0 0, 0.1 0.1)'


    @pytest.mark.parametrize('role,direction', [('forward', 1),
                                                ('backward', -1)])
    def test_oneway_way(self, mapdb, role, direction):
        mapdb.insert_into('ways')\
            .line(1, geom='LINESTRING(0 0, 0.1 0.1)', tags={'foo': 'bar'})

        objs = self.run_test(mapdb, [('W', 1, role)])

        assert len(objs) == 1

        result = objs[0]
        assert result.direction == direction
        assert result.role == ''
        assert result.geom.wkt == 'LINESTRING (0 0, 0.1 0.1)'


    @pytest.mark.parametrize('members,out', [([('W', 1, ''), ('W', 2, '')], [1, 2]),
                                             ([('W', 2, ''), ('W', 1, '')], [2, 1]),
                                             ([('N', 34, ''), ('W', 2, ''), ('W', 1, '')], [2, 1])
                                             ])
    def test_multiway(self, mapdb, members, out):
        mapdb.insert_into('ways')\
            .line(1, geom='LINESTRING(0 0, 0.1 0.1)', tags={'foo': 'bar'})\
            .line(2, geom='LINESTRING(0 0, 0.1 0.1)', tags={'baz': '3'})

        objs = self.run_test(mapdb, members)

        assert [r.osm_id for r in objs] == out


    def test_circle_with_approach(self, mapdb):
        mapdb.insert_into('ways')\
            .line(1, geom='LINESTRING(0 0, 0 -0.01)', tags={})\
            .line(2, geom='LINESTRING(0 0, 0 0.1, 0.1 0.1, 0 0)', tags={})

        objs = self.run_test(mapdb, [('W', 1, ''), ('W', 2, ''), ('W', 1, '')])

        assert [r.osm_id for r in objs] == [1, 2, 1]
        assert [r.start for r in objs] == [0, 1, 2]
