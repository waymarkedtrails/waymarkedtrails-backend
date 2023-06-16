# SPDX-License-Identifier: GPL-3.0-only
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2011-2023 Sarah Hoffmann
"""
Tables to trace updates
"""

from sqlalchemy import Table, Column
from geoalchemy2 import Geometry

class UpdatedGeometriesTable:
    """Table that stores just a list of geometries that have been changed
       in the course of an update.

       This table contains created and modified geometries as well as
       deleted ones.
    """

    def __init__(self, meta, name):
        srid = meta.info.get('srid', 4326)
        self.data = Table(name, meta,
                          Column('geom', Geometry('GEOMETRY', srid=srid)))

    def clear(self, engine):
        with engine.begin() as conn:
            conn.execute(self.data.delete())

    def create(self, engine):
        self.data.create(bind=engine, checkfirst=True)

    def construct(self, engine):
        self.clear(engine)

    def update(self, engine):
        self.clear(engine)

    def add(self, conn, geom):
        conn.execute(self.data.insert().values(geom=geom))

    def add_from_select(self, engine, stm):
        with engine.begin() as conn:
            conn.execute(self.data.insert().from_select(self.data.c, stm))
