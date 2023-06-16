# SPDX-License-Identifier: GPL-3.0-only
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2022-2023 Sarah Hoffmann

import os

import pytest
import sqlalchemy as sa
from sqlalchemy.engine.url import URL

from wmt_db.maptype.routes import create_mapdb
from wmt_db.maptype.slopes import create_mapdb as create_slopes_mapdb

import wmt_db.config.hiking
import wmt_db.config.cycling
import wmt_db.config.mtb
import wmt_db.config.riding
import wmt_db.config.skating
import wmt_db.config.slopes as slopes_config

class Options:
    database = 'osgende_test'
    status = False
    no_engine = True

@pytest.fixture(autouse=True)
def clear_db():
    assert os.system('dropdb --if-exists ' + Options.database) == 0
    assert os.system('createdb ' + Options.database) == 0

@pytest.fixture(scope="module", params=['hiking', 'cycling', 'mtb', 'riding', 'skating'])
def site_config(request):
    return getattr(wmt_db.config, request.param)


def run_import(db):
    db.osmdata.node.data.create(bind=db.engine, checkfirst=True)
    db.osmdata.way.data.create(bind=db.engine, checkfirst=True)
    db.osmdata.relation.data.create(bind=db.engine, checkfirst=True)
    db.osmdata.node.change.create(bind=db.engine, checkfirst=True)
    db.osmdata.way.change.create(bind=db.engine, checkfirst=True)
    db.osmdata.relation.change.create(bind=db.engine, checkfirst=True)

    db.create()
    db.construct()
    db.dataview()
    db.update()


def test_routedb(site_config):
    db = create_mapdb(site_config, Options)
    db.engine = sa.create_engine(URL.create('postgresql', database=Options.database))
    with db.engine.begin() as conn:
        conn.execute(sa.text("CREATE EXTENSION postgis"))

    run_import(db)

    db.engine.dispose()

def test_pistedb():
    db = create_slopes_mapdb(slopes_config, Options)
    db.engine = sa.create_engine(URL.create('postgresql', database=Options.database))
    with db.engine.begin() as conn:
        conn.execute(sa.text("CREATE EXTENSION postgis"))

    run_import(db)

    db.engine.dispose()

