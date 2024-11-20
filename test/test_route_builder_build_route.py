# SPDX-License-Identifier: GPL-3.0-or-later
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2024 Sarah Hoffmann
import pytest

from shapely import from_wkt
from shapely.testing import assert_geometries_equal

from wmt_db.geometry import build_route
from wmt_db.geometry.route_types import BaseWay, WaySegment, RouteSegment


def line(coords):
    return from_wkt(f"LINESTRING({coords})")


def assert_simple_segment_route(route, length):
    assert route.length == length
    assert not route.appendices
    assert len(route.main) == 1

    inner = route.main[0]

    assert isinstance(inner, WaySegment)
    assert inner.length == length

    return inner


def test_single_way():
    members = [
        BaseWay(1, {}, 10, 0, line('10 1, 10.1 1'), '')
    ]
    route = build_route(members)

    inner = assert_simple_segment_route(route, 10)
    assert inner.ways == members
    assert inner.role == ''
    assert inner.direction == 0


@pytest.mark.parametrize('l1,l2', [('3 4, 3.1 4', '3.1 4, 3.2 4'),
                                   ('3 4, 3.1 4', '3.2 4, 3.1 4'),
                                   ('3.1 4, 3 4', '3.1 4, 3.2 4'),
                                   ('3.1 4, 3 4', '3.2 4, 3.1 4')])
def test_join_ways(l1, l2):
    members = [
        BaseWay(1, {}, 10, 0, line(l1), ''),
        BaseWay(2, {}, 10, 0, line(l2), '')
    ]
    route = build_route(members)

    inner = assert_simple_segment_route(route, 20)
    assert len(inner.ways) == 2

    assert_geometries_equal(inner.ways[0].geom, line('3 4, 3.1 4'))
    assert_geometries_equal(inner.ways[1].geom, line('3.1 4, 3.2 4'))


@pytest.mark.parametrize('l1,l2, d', [('3 4, 3.1 4', '3.1 4, 3.2 4', 1),
                                      ('3 4, 3.1 4', '3.2 4, 3.1 4', -1),
                                      ('3.1 4, 3 4', '3.1 4, 3.2 4', 1),
                                      ('3.1 4, 3 4', '3.2 4, 3.1 4', -1)])
def test_join_ways_different_directions(l1, l2, d):
    members = [
        BaseWay(1, {}, 10, 0, line(l1), ''),
        BaseWay(2, {}, 10, d, line(l2), '')
    ]
    route = build_route(members)

    assert route.length == 20
    assert not route.appendices
    assert len(route.main) == 2

    inner = route.main[0]

    assert isinstance(inner, WaySegment)
    assert inner.length == 10
    assert len(inner.ways) == 1
    assert inner.direction == 0
    assert_geometries_equal(inner.ways[0].geom, line('3 4, 3.1 4'))

    inner = route.main[1]

    assert isinstance(inner, WaySegment)
    assert inner.length == 10
    assert len(inner.ways) == 1
    assert inner.direction == 1
    assert_geometries_equal(inner.ways[0].geom, line('3.1 4, 3.2 4'))

