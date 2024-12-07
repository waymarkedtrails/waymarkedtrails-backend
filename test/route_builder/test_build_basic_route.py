# SPDX-License-Identifier: GPL-3.0-or-later
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2024 Sarah Hoffmann
import pytest

from shapely.testing import assert_geometries_equal

from osgende.common.tags import TagStore
from wmt_db.geometry import build_route
import wmt_db.geometry.route_types as rt

def assert_simple_segment_route(route, length):
    assert route.length == length
    assert not route.appendices
    assert len(route.main) == 1

    inner = route.main[0]

    assert isinstance(inner, rt.WaySegment)
    assert inner.length == length

    return inner


def test_single_way(grid):
    g = grid("1 2 3")
    members = [
        rt.BaseWay(1, {}, 10, 0, g.line('123'), '')
    ]
    route = build_route(members)

    inner = assert_simple_segment_route(route, 10)
    assert inner.ways == members
    assert inner.role == ''
    assert inner.direction == 0


@pytest.mark.parametrize('l1', ['12', '21'])
@pytest.mark.parametrize('l2', ['23', '32'])
def test_join_ways(grid, l1, l2):
    g = grid("1 2 3")
    route = build_route([
        rt.BaseWay(1, {}, 10, 0, g.line(l1), ''),
        rt.BaseWay(2, {}, 10, 0, g.line(l2), '')
    ])

    inner = assert_simple_segment_route(route, 20)
    assert len(inner.ways) == 2

    assert_geometries_equal(inner.ways[0].geom, g.line('12'))
    assert_geometries_equal(inner.ways[1].geom, g.line('23'))


@pytest.mark.parametrize('l1', ['12', '21'])
@pytest.mark.parametrize('l2, d', [('234', 1), ('432', -1)])
def test_join_ways_different_directions(grid, l1, l2, d):
    g = grid("1234")

    route = build_route([
        rt.BaseWay(1, {}, 10, 0, g.line(l1), ''),
        rt.BaseWay(2, {}, 10, d, g.line(l2), '')
    ])

    assert route == rt.RouteSegment(
        length=20, start=0, appendices = [],
        main=[rt.WaySegment(
                length=10, start=0,
                ways=[rt.BaseWay(osm_id=1, tags=TagStore(), length=10, start=0,
                                 direction=0, role='', geom=g.line('12'))]
                ),
              rt.WaySegment(
                length=10, start=10,
                ways=[rt.BaseWay(osm_id=2, tags=TagStore(), length=10, start=10,
                                 direction=1, role='', geom=g.line('234'))]
                )
             ]
        )


def test_single_relation(grid):
    g = grid("1 2 3")
    members = [
        rt.RouteSegment(
            length=10, start=0, appendices = [],
            main=[rt.WaySegment(
                length=10, start=0,
                ways=[rt.BaseWay(1, {}, 10, 0, g.line('123'), '')])])
    ]
    route = build_route(members)

    assert route == rt.RouteSegment(
        length=10, start=0, appendices = [],
        main=[rt.RouteSegment(
                length=10, start=0, appendices = [],
                main=[rt.WaySegment(
                    length=10, start=0,
                    ways=[rt.BaseWay(osm_id=1, tags=TagStore(), length=10, start=0,
                                     direction=0, role='', geom=g.line('123'))])])])


def test_all_members_with_roles(grid):
    g = grid("1 2 3 4")
    route = build_route([
        rt.BaseWay(1, {}, 10, 0, g.line('12'), 'approach'),
        rt.BaseWay(2, {}, 10, 0, g.line('234'), 'link')
    ])

    assert route == rt.RouteSegment(
        length=20, start=0, appendices = [],
        main=[rt.WaySegment(
                length=10, start=0,
                ways=[rt.BaseWay(osm_id=1, tags=TagStore(), length=10, start=0,
                                 direction=0, role='', geom=g.line('12'))]
                ),
              rt.WaySegment(
                length=10, start=10,
                ways=[
                      rt.BaseWay(osm_id=2, tags=TagStore(), length=10, start=10,
                                 direction=0, role='', geom=g.line('234'))]
                )
             ]
        )

