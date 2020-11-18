# SPDX-License-Identifier: GPL-3.0-only
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2020 Sarah Hoffmann

import pytest

from wmt_db.tables.guideposts import GuidePosts
from osgende.osmdata import OsmSourceTables

@pytest.fixture
def tags():
    def _make_tags(**kwargs):
        tags = dict(tourism='information', information='guidepost')
        tags.update(kwargs)
        return tags

    return _make_tags

class TestGuidepostTableNoSubtype:

    @pytest.fixture(autouse=True)
    def init_tables(self, mapdb):
        class Config:
            subtype = None
            table_name = 'test'

        src = mapdb.add_table('src', OsmSourceTables.create_node_table(mapdb.metadata))
        mapdb.add_table('test', GuidePosts(mapdb.metadata, src, Config))
        mapdb.create()
        yield

    def test_simple(self, mapdb, tags):
        mapdb.insert_into('src')\
            .line(1, geom='SRID=4326;POINT(12 34)', tags=tags(name='X43', ele='34m'))

        mapdb.construct()

        mapdb.table_equals('test',
            [dict(id=1, name='X43', ele='34', geom='POINT(12 34)')])
