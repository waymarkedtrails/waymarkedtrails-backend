# SPDX-License-Identifier: GPL-3.0-only
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2020 Sarah Hoffmann
from dataclasses import dataclass

import pytest

from wmt_db.styles.route_network_style import RouteNetworkStyle

@dataclass
class RelInfo:
    id: int
    top: bool
    network: str = ''
    symbol: str = ''
    network: str = ''
    level: int = 0


@pytest.fixture
def style():
    return RouteNetworkStyle()

@pytest.fixture
def collector(style):
    return style.new_collector()

def test_no_top(style, collector):
    style.add_to_collector(collector, RelInfo(id=123, top=False))

    cols = style.to_columns(collector)

    assert cols['cldrels'] == [123]
    assert cols['toprels'] == []

def test_network(style, collector):
    style.add_to_collector(collector,
        RelInfo(id=3, top=True, network='ABC', symbol=None, level=2))

    cols = style.to_columns(collector)

    assert cols['style'] == 'ABC'
    assert cols['class'] == 1 << 2
    assert cols['toprels'] == [3]
    assert cols['cldrels'] == []

def test_shields(style, collector):
    style.add_to_collector(collector,
        RelInfo(id=1, top=True, level=1, symbol='X', network=None))
    style.add_to_collector(collector,
        RelInfo(id=2, top=True, level=3, symbol='X', network=None))
    style.add_to_collector(collector,
        RelInfo(id=9, top=True, level=20, symbol='Y', network=None))

    cols = style.to_columns(collector)

    assert cols['style'] is None
    assert cols['toprels'] == [1, 2, 9]
    assert cols['lshields'] == ['X']
    assert cols['inrshields'] == ['Y']
