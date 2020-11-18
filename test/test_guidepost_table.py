# SPDX-License-Identifier: GPL-3.0-only
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2020 Sarah Hoffmann

import pytest

from wmt_db.tables.guideposts import GuidePosts
from wmt_db.tables.updates import UpdatedGeometriesTable
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

    def test_simple(self, mapdb, tags):
        mapdb.insert_into('src')\
            .line(1, geom='SRID=4326;POINT(12 34)', tags=tags(name='X43', ele='34m'))\
            .line(2, geom='SRID=4326;POINT(0.1 -0.3)', tags=tags(ele='45.3 ft'))\
            .line(3, geom='SRID=4326;POINT(128 10.4)', tags=tags(ele='3029'))\
            .line(4, geom='SRID=4326;POINT(1 1)', tags=tags())

        mapdb.construct()

        mapdb.table_equals('test',
            [dict(id=1, name='X43', ele='34', geom='POINT(12 34)'),
             dict(id=2, name=None, ele='45.3', geom='POINT(0.1 -0.3)'),
             dict(id=3, name=None, ele='3029', geom='POINT(128 10.4)'),
             dict(id=4, name=None, ele=None, geom='POINT(1 1)')
            ])


class TestGuidepostTableWithSubtype:

    @pytest.fixture(autouse=True)
    def init_tables(self, mapdb):
        class Config:
            subtype = 'hiking'
            require_subtype = False
            table_name = 'test'

        src = mapdb.add_table('src', OsmSourceTables.create_node_table(mapdb.metadata))
        mapdb.add_table('test', GuidePosts(mapdb.metadata, src, Config))
        mapdb.create()
        yield

    def test_simple(self, mapdb, tags):
        mapdb.insert_into('src')\
            .line(1, geom='SRID=4326;POINT(1 1)', tags=tags())\
            .line(2, geom='SRID=4326;POINT(1 1)', tags=tags(hiking='yes'))\
            .line(3, geom='SRID=4326;POINT(1 1)', tags=tags(cycling='yes'))\
            .line(4, geom='SRID=4326;POINT(1 1)', tags=tags(hiking='no'))\
            .line(5, geom='SRID=4326;POINT(1 1)', tags=tags(hiking='yes', cycling='yes'))

        mapdb.construct()

        mapdb.table_equals('test',
            [dict(id=1, name=None, ele=None, geom='POINT(1 1)'),
             dict(id=2, name=None, ele=None, geom='POINT(1 1)'),
             dict(id=5, name=None, ele=None, geom='POINT(1 1)')
            ])


class TestGuidepostTableWithRequiredSubtype:

    @pytest.fixture(autouse=True)
    def init_tables(self, mapdb):
        class Config:
            subtype = 'hiking'
            require_subtype = True
            table_name = 'test'

        src = mapdb.add_table('src', OsmSourceTables.create_node_table(mapdb.metadata))
        mapdb.add_table('test', GuidePosts(mapdb.metadata, src, Config))
        mapdb.create()
        yield

    def test_simple(self, mapdb, tags):
        mapdb.insert_into('src')\
            .line(1, geom='SRID=4326;POINT(1 1)', tags=tags())\
            .line(2, geom='SRID=4326;POINT(1 1)', tags=tags(hiking='yes'))\
            .line(3, geom='SRID=4326;POINT(1 1)', tags=tags(cycling='yes'))\
            .line(4, geom='SRID=4326;POINT(1 1)', tags=tags(hiking='no'))\
            .line(5, geom='SRID=4326;POINT(1 1)', tags=tags(hiking='yes', cycling='yes'))

        mapdb.construct()

        mapdb.table_equals('test',
            [dict(id=2, name=None, ele=None, geom='POINT(1 1)'),
             dict(id=5, name=None, ele=None, geom='POINT(1 1)')
            ])

class TestGuidepostWithUpdateTable:

    @pytest.fixture(autouse=True)
    def init_tables(self, mapdb):
        class Config:
            subtype = 'hiking'
            require_subtype = False
            table_name = 'test'

        src = mapdb.add_table('src', OsmSourceTables.create_node_table(mapdb.metadata))
        uptable = mapdb.add_table('updates',
                      UpdatedGeometriesTable(mapdb.metadata, 'updates'))

        mapdb.add_table('test', GuidePosts(mapdb.metadata, src, Config))\
             .set_update_table(uptable)

        mapdb.create()
        yield

    def test_simple(self, mapdb, tags):
        mapdb.insert_into('src')\
            .line(1, geom='SRID=4326;POINT(1 1)', tags=tags())\
            .line(2, geom='SRID=4326;POINT(1 1)', tags=tags(hiking='yes'))\
            .line(3, geom='SRID=4326;POINT(1 1)', tags=tags(cycling='yes'))

        mapdb.construct()

        mapdb.table_equals('test',
            [dict(id=1, name=None, ele=None, geom='POINT(1 1)'),
             dict(id=2, name=None, ele=None, geom='POINT(1 1)'),
            ])

        mapdb.modify('src')\
            .delete(1)\
            .add(10, geom='SRID=4326;POINT(10 10)', tags=tags())\
            .modify(2, geom='SRID=4326;POINT(2 2)', tags=tags(cycling='yes'))\
            .modify(3, geom='SRID=4326;POINT(3 3)', tags=tags(hiking='yes'))

        mapdb.update()

        mapdb.table_equals('test',
            [dict(id=3, name=None, ele=None, geom='POINT(3 3)'),
             dict(id=10, name=None, ele=None, geom='POINT(10 10)'),
            ])

        mapdb.table_equals('updates',
            [dict(geom='POINT(10 10)'),
             dict(geom='POINT(2 2)'),
             dict(geom='POINT(3 3)')])
