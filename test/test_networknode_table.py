# SPDX-License-Identifier: GPL-3.0-only
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2020 Sarah Hoffmann

import pytest

from wmt_db.tables.networknodes import NetworkNodes
from osgende.osmdata import OsmSourceTables

class TestNetworkNodeTable:

    @pytest.fixture(autouse=True)
    def init_tables(self, mapdb):
        class Config:
            table_name = 'test'
            node_tag = 'rwn_ref'

        src = mapdb.add_table('src', OsmSourceTables.create_node_table(mapdb.metadata))
        mapdb.add_table('test', NetworkNodes(mapdb.metadata, src, Config))
        mapdb.create()

    def test_simple(self, mapdb):
        mapdb.insert_into('src')\
            .line(1, tags=dict(building='yes'), geom='SRID=4326;POINT(12 34)')\
            .line(2, tags=dict(rwn_ref='34B'), geom='SRID=4326;POINT(-2 4)')

        mapdb.construct()

        mapdb.table_equals('test',
            [dict(id=2, name='34B', geom='POINT(-2 4)')])

