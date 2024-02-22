# SPDX-License-Identifier: GPL-3.0-only
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2021 Sarah Hoffmann
from dataclasses import dataclass

import pytest

from wmt_db.styles.piste_network_style import PisteNetworkStyle
from wmt_db.config.slopes import PisteTableConfig

@dataclass
class RelInfo:
    id: int
    top: bool
    symbol: str
    difficulty: int
    piste: int

@pytest.fixture
def style():
    return PisteNetworkStyle(PisteTableConfig.difficulty_map,
                             PisteTableConfig.piste_type)

@pytest.fixture
def collector(style):
    return style.new_collector()

def test_no_top(style, collector):
    style.add_to_collector(collector, RelInfo(id=1, top=False, symbol='A', difficulty=0, piste=0))
    style.add_to_collector(collector, RelInfo(id=2, top=True, symbol='B', difficulty=0, piste=0))

    cols = style.to_columns(collector)

    assert cols['symbol'] == ['B']

def test_symbol(style, collector):
    style.add_to_collector(collector, RelInfo(id=1, top=True, symbol='A', difficulty=0, piste=0))
    style.add_to_collector(collector, RelInfo(id=2, top=True, symbol='B', difficulty=0, piste=0))
    style.add_to_collector(collector, RelInfo(id=3, top=True, symbol='C', difficulty=0, piste=0))
    style.add_to_collector(collector, RelInfo(id=4, top=True, symbol='D', difficulty=0, piste=0))
    style.add_to_collector(collector, RelInfo(id=5, top=True, symbol='E', difficulty=0, piste=0))
    style.add_to_collector(collector, RelInfo(id=6, top=True, symbol='F', difficulty=0, piste=0))
    style.add_to_collector(collector, RelInfo(id=7, top=True, symbol='G', difficulty=0, piste=0))

    cols = style.to_columns(collector)

    assert cols['symbol'] == ['A', 'B', 'C', 'D', 'E']

def test_difficulty(style, collector):
    style.add_to_collector(collector, RelInfo(id=1235, top=True, difficulty=5, piste=0, symbol=None))

    cols = style.to_columns(collector)

    assert cols['expert']
    assert not cols['intermediate']

def test_piste(style, collector):
    style.add_to_collector(collector, RelInfo(id=7273, top=True, difficulty=0, piste=2, symbol=None))

    cols = style.to_columns(collector)

    assert cols['nordic']
    assert not cols['downhill']

