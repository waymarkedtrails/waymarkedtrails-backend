# SPDX-License-Identifier: GPL-3.0-only
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2020 Sarah Hoffmann

import os

import pytest
import sqlalchemy as sa
import osgende

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
            conn.execute(self.table.insert().values(kwargs))

class TestableMapDB(osgende.mapdb.MapDB):

    def insert_into(self, table):
        return TableInserter(self.tables[table].data, self.engine)

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
                        assert column in row, f"Column missing in table {table.name}."
                        if not DBValue(row[column], table.c[column].type) == content:
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
        conn.execute("CREATE EXTENSION postgis")

    yield db
    db.engine.dispose()
