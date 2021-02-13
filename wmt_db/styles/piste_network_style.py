# SPDX-License-Identifier: GPL-3.0-only
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2021 Sarah Hoffmann

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY

from ..common.route_types import Network

class PisteNetworkStyle(object):
    table_name = 'piste_style'

    def __init__(self, difficulties, types):
        self.difficulty_map = difficulties
        self.piste_type = types

    def add_columns(self, table):
        table.append_column(sa.Column('symbol', ARRAY(sa.String)))
        table.append_column(sa.Column('sources', ARRAY(sa.BigInteger)))

        for c in self.difficulty_map:
            table.append_column(sa.Column(c, sa.Boolean))
        for c in self.piste_type:
            table.append_column(sa.Column(c, sa.Boolean))

    def new_collector(self):
        coll = dict(symbol=[], sources=[])
        for c in self.difficulty_map:
            coll[c] = False
        for c in self.piste_type:
            coll[c] = False

        return coll

    def add_to_collector(self, c, relinfo):
        for k, v in self.difficulty_map.items():
            if relinfo['difficulty'] == v:
                c[k] = True
        for k, v in self.piste_type.items():
            if relinfo['piste'] == v:
                c[k] = True

        if relinfo['symbol'] is not None and len(c['symbol']) < 5:
                c['symbol'].append(relinfo['symbol'])

        c['sources'].append(relinfo['id'])

    def to_columns(self, c):
        return c
