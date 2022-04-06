# SPDX-License-Identifier: GPL-3.0-only
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2020 Sarah Hoffmann

import pytest

from osgende.osmdata import OsmSourceTables

from wmt_db.tables.guideposts import GuidePosts
from wmt_db.tables.updates import UpdatedGeometriesTable

import wmt_db.config.hiking as hiking_config
import wmt_db.config.cycling as cycling_config
import wmt_db.config.mtb as mtb_config
import wmt_db.config.riding as riding_config
import wmt_db.config.skating as skating_config

@pytest.fixture
def src(mapdb):
    return mapdb.add_table('src', OsmSourceTables.create_node_table(mapdb.metadata))

@pytest.fixture
def tags():
    def _make_tags(**kwargs):
        tags = dict(tourism='information', information='guidepost')
        tags.update(kwargs)
        return tags

    return _make_tags

class TestGuidepostTableNoSubtype:

    @pytest.fixture(autouse=True)
    def init_tables(self, mapdb, src):
        class Config:
            subtype = None
            table_name = 'test'

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
            [dict(id=1, name='X43', ele=34.0, geom='POINT(12 34)'),
             dict(id=2, name=None, ele=13.80744, geom='POINT(0.1 -0.3)'),
             dict(id=3, name=None, ele=3029, geom='POINT(128 10.4)'),
             dict(id=4, name=None, ele=None, geom='POINT(1 1)')
            ])

    def test_ele_out_of_range(self, mapdb, tags):
        mapdb.insert_into('src')\
            .line(1, geom='SRID=4326;POINT(12 34)', tags=tags(ele='-3'))\
            .line(2, geom='SRID=4326;POINT(12 34)', tags=tags(ele='-33'))\
            .line(3, geom='SRID=4326;POINT(12 34)', tags=tags(ele='8849m'))\
            .line(4, geom='SRID=4326;POINT(12 34)', tags=tags(ele='29032ft'))\
            .line(5, geom='SRID=4326;POINT(12 34)', tags=tags(ele='100456'))

        mapdb.construct()

        mapdb.table_equals('test',
            [dict(id=1, name=None, ele=None, geom='POINT(12 34)'),
             dict(id=2, name=None, ele=None, geom='POINT(12 34)'),
             dict(id=3, name=None, ele=8849, geom='POINT(12 34)'),
             dict(id=4, name=None, ele=8848.9536, geom='POINT(12 34)'),
             dict(id=5, name=None, ele=None, geom='POINT(12 34)')
            ])



class TestGuidepostTableWithSubtype:

    @pytest.fixture(autouse=True)
    def init_tables(self, mapdb, src):
        class Config:
            subtype = 'hiking'
            require_subtype = False
            table_name = 'test'

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
    def init_tables(self, mapdb, src):
        class Config:
            subtype = 'hiking'
            require_subtype = True
            table_name = 'test'

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
    def init_tables(self, mapdb, src):
        class Config:
            subtype = 'hiking'
            require_subtype = False
            table_name = 'test'

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


def test_guidepost_hiking_style(mapdb, src, tags):
    mapdb.add_table('test', GuidePosts(mapdb.metadata, src, hiking_config.GUIDEPOSTS))
    mapdb.create()

    mapdb.insert_into('src')\
        .line(1, geom='SRID=4326;POINT(1 1)', tags=tags())\
        .line(2, geom='SRID=4326;POINT(1 1)', tags=tags(hiking='yes'))\

    mapdb.construct()

    mapdb.table_equals('test', [dict(id=1), dict(id=2)])

def test_guidepost_cycling_style(mapdb, src, tags):
    mapdb.add_table('test', GuidePosts(mapdb.metadata, src, cycling_config.GUIDEPOSTS))
    mapdb.create()

    mapdb.insert_into('src')\
        .line(1, geom='SRID=4326;POINT(1 1)', tags=tags())\
        .line(2, geom='SRID=4326;POINT(1 1)', tags=tags(bicycle='yes'))\

    mapdb.construct()

    mapdb.table_equals('test', [dict(id=2)])

def test_guidepost_mtb_style(mapdb, src, tags):
    mapdb.add_table('test', GuidePosts(mapdb.metadata, src, mtb_config.GUIDEPOSTS))
    mapdb.create()

    mapdb.insert_into('src')\
        .line(1, geom='SRID=4326;POINT(1 1)', tags=tags())\
        .line(2, geom='SRID=4326;POINT(1 1)', tags=tags(mtb='yes'))\

    mapdb.construct()

    mapdb.table_equals('test', [dict(id=2)])

def test_guidepost_riding_style(mapdb, src, tags):
    mapdb.add_table('test', GuidePosts(mapdb.metadata, src, riding_config.GUIDEPOSTS))
    mapdb.create()

    mapdb.insert_into('src')\
        .line(1, geom='SRID=4326;POINT(1 1)', tags=tags())\
        .line(2, geom='SRID=4326;POINT(1 1)', tags=tags(horse='yes'))\

    mapdb.construct()

    mapdb.table_equals('test', [dict(id=2)])

def test_guidepost_skating_style(mapdb, src, tags):
    mapdb.add_table('test', GuidePosts(mapdb.metadata, src, skating_config.GUIDEPOSTS))
    mapdb.create()

    mapdb.insert_into('src')\
        .line(1, geom='SRID=4326;POINT(1 1)', tags=tags())\
        .line(2, geom='SRID=4326;POINT(1 1)', tags=tags(skating='yes'))\

    mapdb.construct()

    mapdb.table_equals('test', [dict(id=2)])
