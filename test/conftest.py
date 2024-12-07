# SPDX-License-Identifier: GPL-3.0-only
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2020-2023 Sarah Hoffmann

import os

import pytest
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from geoalchemy2 import Geometry

import osgende
from osgende.common.table import TableSource

from wmt_db.tables.countries import CountryGrid

from db_helpers import DBValue

class Options:
    database = 'osgende_test'
    username = None
    password = None
    status = False

class TableInserter:

    def __init__(self, table, engine):
        self.table = table
        self.engine = engine

    def line(self, oid, **kwargs):
        kwargs['id'] = oid
        with self.engine.begin() as conn:
            conn.execute(self.table.data.insert().values(kwargs))
        return self

class TableChanger:

    def __init__(self, table, engine):
        self.table = table
        self.engine = engine

    def delete(self, oid):
        with self.engine.begin() as conn:
            conn.execute(self.table.data.delete().where(self.table.c.id == oid))
            conn.execute(self.table.change.insert().values([dict(id=oid, action='D')]))

        return self

    def add(self, oid, **kwargs):
        kwargs['id'] = oid
        with self.engine.begin() as conn:
            conn.execute(self.table.data.insert().values(kwargs))
            conn.execute(self.table.change.insert().values([dict(id=oid, action='A')]))

        return self

    def modify(self, oid, **kwargs):
        kwargs['id'] = oid
        with self.engine.begin() as conn:
            conn.execute(self.table.data.delete().where(self.table.c.id == oid))
            conn.execute(self.table.data.insert().values(kwargs))
            conn.execute(self.table.change.insert().values([dict(id=oid, action='M')]))

        return self

class TestableMapDB(osgende.mapdb.MapDB):

    def insert_into(self, table):
        return TableInserter(self.tables[table], self.engine)

    def modify(self, table):
        return TableChanger(self.tables[table], self.engine)

    def table_equals(self, name, expected):
        table = self.tables[name].data

        with self.engine.begin() as conn:
            res = conn.execute(table.select())

            assert len(expected) == res.rowcount, \
                   f"Number of rows in table {table.name} differ."

            todo = list(expected)
            for row in res:
                for exp in todo:
                    assert isinstance(exp, dict), "Expected data has wrong format."
                    for column, content in exp.items():
                        assert column in row._fields, f"Column missing in table {table.name}."
                        if not DBValue(row._mapping[column], table.c[column].type) == content:
                            break
                    else:
                        todo.remove(exp)
                        break
                else:
                    assert False, f"Unexpected row {str(row)}. Stil expected: {str(todo)}"

        assert len(todo) == 0, f"Missing rows in {table.name}: {str(todo)}"


@pytest.fixture
def mapdb():
    assert os.system('dropdb --if-exists ' + Options.database) == 0
    assert os.system('createdb ' + Options.database) == 0
    db = TestableMapDB(Options)
    with db.engine.begin() as conn:
        conn.execute(sa.text("CREATE EXTENSION postgis"))

    yield db
    db.engine.dispose()

@pytest.fixture
def countries(mapdb):
    table = CountryGrid(mapdb.metadata, 'countries')
    table.data.create(bind=mapdb.engine, checkfirst=True)

    with mapdb.engine.begin() as conn:
        conn.execute(table.data.insert().values([
            dict(country_code='de', geom='SRID=4326;POLYGON((0 0, 0 1, 1 1, 1 0, 0 0))'),
            dict(country_code='fr', geom='SRID=4326;POLYGON((0 0, 0 1, -1 1, -1 0, 0 0))'),
        ]))

    return table

@pytest.fixture
def segment_table(mapdb):
    table = mapdb.add_table('ways',
                TableSource(sa.Table('ways', mapdb.metadata,
                                     sa.Column('id', sa.BigInteger),
                                     sa.Column('nodes', ARRAY(sa.BigInteger)),
                                     sa.Column('rels', ARRAY(sa.BigInteger)),
                                     sa.Column('tags', JSONB),
                                     sa.Column('geom', Geometry('LINESTRING', 4326))
                                    ), change_table='way_changeset'))
    table.srid = 4326

    return table


class MockShieldFactory:

    def create(self, *args, **kwargs):
        return self

    def uuid(self):
        return '123'

    def to_file(self, *args, **kwargs):
        pass

@pytest.fixture
def shields():
    return MockShieldFactory()


