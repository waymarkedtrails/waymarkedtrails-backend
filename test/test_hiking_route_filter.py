# SPDX-License-Identifier: GPL-3.0-only
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2020 Sarah Hoffmann

import pytest

from wmt_db.config.hiking import filter_route_tags
from wmt_db.common.route_types import Network

class Outtags:

    def __init__(self, country):
        self.country = country

def test_national_trails():
    outtags = Outtags('gb')

    filter_route_tags(outtags, dict(network='uk_ldp', operator='National Trails'))
    assert outtags.level == Network.NAT()
    filter_route_tags(outtags, dict(network='uk_ldp', operator='Trails'))
    assert outtags.level == Network.REG()

def test_czech_system_major_red():
    outtags = Outtags('cz')
    filter_route_tags(outtags, dict(kct_red='major'))
    assert outtags.network == 'CT'
    assert outtags.level == Network.NAT(-1)

def test_czech_system_major_blue():
    outtags = Outtags('cz')
    filter_route_tags(outtags, dict(kct_blue='major'))
    assert outtags.network == 'CT'
    assert outtags.level == Network.REG(-1)

def test_czech_system_major_red_with_network():
    outtags = Outtags('cz')
    filter_route_tags(outtags, dict(kct_red='major', network='rwn'))
    assert not hasattr(outtags, 'level')
    assert outtags.network == 'CT'
