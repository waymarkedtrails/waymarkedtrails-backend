# SPDX-License-Identifier: GPL-3.0-only
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2015-2023 Sarah Hoffmann
""" Various tables for nodes in a route network.
"""
import sqlalchemy as sa
from geoalchemy2 import Geometry

from osgende.generic import TransformedTable

class NetworkNodes(TransformedTable):
    """ Information about referenced nodes in a route network.
    """

    def __init__(self, meta, source, config):
        self.srid = meta.info.get('srid', source.c.geom.type.srid)
        super().__init__(meta, config.table_name, source)
        self.config = config

    def add_columns(self, table, src):
        table.append_column(sa.Column('name', sa.String))
        table.append_column(sa.Column('geom', Geometry('POINT', srid=self.srid)))

    def transform(self, obj):
        tags = obj.tags

        if self.config.node_tag not in tags:
            return None

        outtags = dict(name=tags[self.config.node_tag])

        if self.srid == self.src.c.geom.type.srid:
            outtags['geom'] = obj.geom
        else:
            outtags['geom'] = obj.geom.ST_Transform(self.srid)

        return outtags
