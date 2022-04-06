# SPDX-License-Identifier: GPL-3.0-only
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2015-2020 Sarah Hoffmann
""" Tables for guide posts.
"""

from re import compile as re_compile

import sqlalchemy as sa
from geoalchemy2 import Geometry

from osgende.generic import TransformedTable
from osgende.common.tags import TagStore

class GuidePosts(TransformedTable):
    """ Information about guide posts. """

    def __init__(self, meta, source, config):
        self.srid = meta.info.get('srid', source.c.geom.type.srid)
        super().__init__(meta, config.table_name, source)
        self.config = config
        self.updates = None

    def add_columns(self, table, src):
        table.append_column(sa.Column('name', sa.String))
        table.append_column(sa.Column('ele', sa.Float))
        table.append_column(sa.Column('geom', Geometry('POINT', srid=self.srid)))

    def set_update_table(self, table):
        self.updates = table
        self.before_update = self._save_added_guideposts

    def _save_added_guideposts(self, engine):
        sql = sa.except_(sa.select([self.src.c.geom.ST_Transform(self.srid)])
                           .where(self.src.c.id.in_(self.src.select_add_modify())),
                         sa.select([self.c.geom])
                           .where(self.c.id.in_(self.src.select_add_modify())))
        self.updates.add_from_select(engine, sql)

    def transform(self, obj):
        tags = TagStore(obj['tags'])
        # filter by subtype
        if self.config.subtype is not None:
            booltags = tags.get_booleans()
            if booltags:
                if not booltags.get(self.config.subtype, False):
                    return None
            else:
                if self.config.require_subtype:
                    return None

        outtags = dict(name=tags.get('name'), ele=None)
        if 'ele' in tags:
            ele = tags.get_length('ele', unit='m', default='m')
            if ele is not None and ele < 9000:
                outtags['ele'] = ele

        if self.srid == self.src.c.geom.type.srid:
            outtags['geom'] = obj['geom']
        else:
            outtags['geom'] = obj['geom'].ST_Transform(self.srid)

        return outtags
