# SPDX-License-Identifier: GPL-3.0-or-later
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2024 Sarah Hoffmann
import pytest

import sqlalchemy as sa

from osgende.common.table import TableSource
from osgende.osmdata import OsmSourceTables
from osgende.common.tags import TagStore

from wmt_db.tables.route_ways import RouteWayTable
from wmt_db.geometry import get_relation_objects
import wmt_db.geometry.route_types as rt

class TestGetRelationObjectsWays:

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
        member_dict = [{'type': 'W', 'id': m[0], 'role': m[1]} for m in members]
        with mapdb.engine.begin() as conn:
            return get_relation_objects(conn, member_dict,
                                        mapdb.tables['ways'],
                                        mapdb.tables['ways'])


    @pytest.mark.parametrize('role', ['', 'main'])
    def test_simple_way(self, grid, mapdb, role):
        g = grid('1 2')
        mapdb.insert_into('ways')\
            .line(1, geom=g.wkt_line('12'), tags={'foo': 'bar'})

        objs = self.run_test(mapdb, [(1, role)])

        assert len(objs) == 1

        result = objs[0]
        assert result.osm_id == 1
        assert result.tags == TagStore({'foo': 'bar'})
        assert result.direction == 0
        assert result.role == ''
        assert result.geom == g.line('12')


    @pytest.mark.parametrize('role,direction', [('forward', 1),
                                                ('backward', -1)])
    def test_oneway_way(self, grid, mapdb, role, direction):
        g = grid('1 2')
        mapdb.insert_into('ways')\
            .line(1, geom=g.wkt_line('12'), tags={'foo': 'bar'})

        objs = self.run_test(mapdb, [(1, role)])

        assert len(objs) == 1

        result = objs[0]
        assert result.direction == direction
        assert result.role == ''
        assert result.geom == g.line('12')


    @pytest.mark.parametrize('members,out', [([(1, ''), (2, '')], [1, 2]),
                                             ([(2, ''), (1, '')], [2, 1]),
                                             ])
    def test_multiway(self, grid, mapdb, members, out):
        g = grid('123')
        mapdb.insert_into('ways')\
            .line(1, geom=g.wkt_line('12'), tags={'foo': 'bar'})\
            .line(2, geom=g.wkt_line('23'), tags={'baz': '3'})

        objs = self.run_test(mapdb, members)

        assert [r.osm_id for r in objs] == out


    def test_circle_with_approach(self, grid, mapdb):
        g = grid("""\
                5
            1 2   4
                3
             """)
        mapdb.insert_into('ways')\
            .line(1, geom=g.wkt_line('12'), tags={})\
            .line(2, geom=g.wkt_line('23452'), tags={'junction': 'roundabout'})

        objs = self.run_test(mapdb, [(1, ''), (2, ''), (1, '')])

        assert [r.osm_id for r in objs] == [1, 2, 1]
        assert [r.start for r in objs] == [0, 1, 2]
        assert objs[1].direction == 1


    def test_reuse_way_with_different_roles(self, grid, mapdb):
        g = grid('1 2 3 4 5 6')
        mapdb.insert_into('ways')\
            .line(1, geom=g.wkt_line('12'), tags={})\
            .line(3, geom=g.wkt_line('23'), tags={})\
            .line(2, geom=g.wkt_line('3456'), tags={})

        objs = self.run_test(mapdb, [(1, 'main'),
                                     (2, ''),
                                     (3, ' alternative'),
                                     (2, 'approach')])

        assert [r.osm_id for r in objs] == [1, 2, 3, 2]
        assert [r.role for r in objs] == ['', '', 'alternative', 'approach']


class RouteTestTable(TableSource):

    def __init__(self, meta):
        table = sa.Table('test_routes', meta,
                         sa.Column('id', sa.BigInteger,
                                   primary_key=True, autoincrement=False),
                         sa.Column('route', sa.String))
        super().__init__(table)


class TestGetRelationObjectsWaysAndRels:

    @pytest.fixture(autouse=True)
    def init_tables(self, mapdb):
        rels = mapdb.add_table('src_rels',
                   OsmSourceTables.create_relation_table(mapdb.metadata))
        ways = mapdb.add_table('src_ways',
                   OsmSourceTables.create_way_table(mapdb.metadata))
        mapdb.add_table('ways',
                        RouteWayTable(mapdb.metadata, 'way_rels', ways, rels,
                                      osmdata=mapdb.osmdata))
        mapdb.add_table('rels',
                        RouteTestTable(mapdb.metadata))

        mapdb.create()


    def run_test(self, mapdb, members):
        member_dict = [{'type': m[0], 'id': m[1], 'role': m[2]} for m in members]
        with mapdb.engine.begin() as conn:
            return get_relation_objects(conn, member_dict,
                                        mapdb.tables['ways'],
                                        mapdb.tables['rels'])


    def test_simple_way(self, grid, mapdb):
        g = grid('1 2')
        mapdb.insert_into('ways')\
            .line(1, geom=g.wkt_line('12'), tags={'foo': 'bar'})

        objs = self.run_test(mapdb, [('W', 1, '')])

        assert len(objs) == 1

        result = objs[0]
        assert result.osm_id == 1
        assert result.tags == TagStore({'foo': 'bar'})
        assert result.direction == 0
        assert result.role == ''
        assert result.geom == g.line('12')


    def test_simple_relation(self, grid, mapdb):
        g = grid('1 2')

        route = rt.RouteSegment(
            length=16, start=0, appendices=[],
            main=[rt.WaySegment(
                    length=5, start=0,
                    ways=[rt.BaseWay(osm_id=1, tags=TagStore(), length=5, start=0,
                            direction=0, role='', geom=g.line('12'))])])

        mapdb.insert_into('rels')\
            .line(23, route=route.to_json())

        objs = self.run_test(mapdb, [('R', 23, ''), ('N', 444, '')])

        route.role = ''
        route.id = 23
        assert objs == [route]
