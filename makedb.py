#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-only
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2011-2020 Sarah Hoffmann
"""
Create, import and modify tables for a route map.
"""

from argparse import ArgumentParser, RawTextHelpFormatter
from textwrap import dedent
import os
import sys
import logging
import importlib
import sqlalchemy as sa
from sqlalchemy.engine.url import URL
from osgende.common.status import StatusManager

import config.common as config

class BaseDb(object):

    def __init__(self, options):
        dba = URL('postgresql', username=options.username,
                      password=options.password, database=options.database)
        self.engine = sa.create_engine(dba, echo=options.echo_sql)
        self.options = options

    def prepare(self):
        """ Creates the necessary indices on a new DB."""
        with self.engine.begin() as conn:
            conn.execute("CREATE INDEX idx_node_changeset on node_changeset(id)")
            conn.execute("ANALYSE")
            conn.execute("CREATE EXTENSION pg_trgm")

        return 0

    def construct(self):
        args = self._osgende_import_args()
        args.extend(('-i', '-c', options.input_file))

        print('osgende-import', args)
        os.execvp('osgende-import', args)

        return 1

    def update(self):
        if not self._is_base_map_update_needed():
            print("Derived maps not yet updated. Skipping base map update.")
            return 0

        args = self._osgende_import_args()
        args.extend(('-S', str(options.diff_size * 1024)))

        print('osgende-import', args)
        os.execvp('osgende-import', args)

        return 1

    def _is_base_map_update_needed(self):
        status = StatusManager(sa.MetaData())
        basemap_seq = status.get_sequence(self.engine, 'base')
        oldest = status.get_min_sequence(self.engine)

        return basemap_seq <= oldest

    def _osgende_import_args(self):
        args = ['osgende-import', '-d', options.database, '-r', options.replication]
        if options.username:
            args.extend(('-u', options.username))
        if options.password:
            args.extend(('-p', options.password))
        if options.nodestore:
            args.extend(('-n', options.nodestore))

        return args


class MapStyleDb(object):

    def __init__(self, options):
        self.mapname = options.routemap

        try:
            site_config = importlib.import_module('config.' + self.mapname)
        except ModuleNotFoundError:
            print("Cannot find route map named '{}'.".format(self.mapname))
            raise

        try:
            mapdb_pkg = importlib.import_module(
                          'db.maptype.' + site_config.MAPTYPE)
        except ModuleNotFoundError:
            print("Unknown map type '{}'.".format(site_config.MAPTYPE))
            raise

        self.mapdb = mapdb_pkg.DB(site_config, options)

    def construct(self):
        # make sure to delete traces of previous imports
        self.mapdb.status.remove_status(self.mapdb.engine, self.mapname)

        self.mapdb.construct()
        self._finalize(False)

    def update(self):
        with self.mapdb.engine.begin() as conn:
            self.basemap_seq = self.mapdb.status.get_sequence(conn, 'base')
            self.map_date = self.mapdb.status.get_sequence(conn, self.mapname)

        if self.map_date is None:
            print("Map not available.")
            return 1

        if self.basemap_seq <= self.map_date:
            print("Data already up-to-date. Skipping.")
            return 0

        self.mapdb.update()
        self._finalize(True)

    def create(self):
        self.mapdb.create()

    def dataview(self):
        self.mapdb.dataview()

    def mkshield(self):
        self.mapdb.mkshield()

    def _finalize(self, dovacuum):
        self.mapdb.status.set_status_from(self.mapdb.engine, self.mapname, 'base')
        self.mapdb.finalize(dovacuum)


if __name__ == "__main__":
    # fun with command line options
    parser = ArgumentParser(usage='%(prog)s [options] <routemap> <action>',
                            formatter_class=RawTextHelpFormatter,
                            description=__doc__)
    parser.add_argument('-d', action='store', dest='database',
                        default=config.DB_NAME,
                        help='name of database')
    parser.add_argument('-u', action='store', dest='username',
                        default=config.DB_USER,
                        help='database user')
    parser.add_argument('-U', action='store', dest='ro_user',
                        default=config.DB_RO_USER,
                        help='read-only database user')
    parser.add_argument('-p', action='store', dest='password',
                        default=config.DB_PASSWORD,
                        help='password for database')
    parser.add_argument('-j', action='store', dest='numthreads', default=1,
                        type=int, help='number of parallel threads to use')
    parser.add_argument('-n', action='store', dest='nodestore',
                        default=config.DB_NODESTORE,
                        help='location of nodestore')
    parser.add_argument('-r', action='store', dest='replication',
                        default=config.REPLICATION_URL,
                        help='URL of OSM data replication service to use')
    parser.add_argument('-S', action='store', dest='diff_size',
                        type=int, default=config.REPLICATION_SIZE)
    parser.add_argument('-v', '--verbose', action="store_const", dest="loglevel",
                        const=logging.DEBUG, default=logging.INFO,
                        help="Enable debug output")
    parser.add_argument('-V', '--verbose-sql', action='store_true', dest="echo_sql",
                        help="Enable output of SQL statements")
    parser.add_argument('-f', action='store', dest='input_file', default=None,
                        help='name of input file ("db import" only)')
    parser.add_argument('routemap',
                        help='name of map (available: TODO) or db for the OSM data DB')
    parser.add_argument('action',
                        help=dedent("""\
                        one of the following:
                          prepare  - create the necessary indexes on a new osgende DB
                                     (routemap must be 'db')
                          create   - discard any existing tables and create new empty ones
                          import   - truncate all tables and create new content from the osm data tables
                                     (with db: create a new database and import osm data tables)
                          dataview - create or update data_view table containing all visible
                                     geometries (needed for tile creation)
                          update   - update all tables (from the *_changeset tables)
                                     (with db: update from given replication service)
                          mkshield - force remaking of all shield bitmaps"""))

    options = parser.parse_args()

    # setup logging
    logging.basicConfig(format='%(asctime)s %(message)s', level=options.loglevel,
                        datefmt='%y-%m-%d %H:%M:%S')

    # Update of the base DB.
    if options.routemap == 'db':
        db = BaseDb(options)
        name = 'base'
    else:
        db = MapStyleDb(options)
        name = options.routemap

    if options.action == 'import':
        action = getattr(db, 'construct')
    else:
        action = getattr(db, options.action)

    if action is None:
        print("Action '{}' not available for {} DB.".format(options.action, name))
        raise

    exit(action())
