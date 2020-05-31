# SPDX-License-Identifier: GPL-3.0-only
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2020 Sarah Hoffmann

import os

from db.styles.piste_network_style import PisteNetworkStyle
from wmt_shields.wmt_config import WmtConfig

from config.common import *

MAPTYPE = 'slopes'

DB_SCHEMA = 'slopes'
DB_TABLES = SlopeDBTables()

DB_ROUTE_SUBSET = """
    tags ? 'route' and tags->>'type' IN ('route', 'superroute')
    AND array['ski', 'piste'] && regexp_split_to_array(tags->>'route', ';')
    AND NOT (tags ? 'state' AND tags->>'state' = 'proposed')
    AND NOT (tags->>'piste:type' = 'skitour')"""

DB_WAY_SUBSET = """
    tags ? 'piste:type'
    AND NOT (tags ? 'state' AND tags->>'state' = 'proposed')
    AND NOT (tags->>'piste:type' = 'downhill'
             AND nodes[array_lower(nodes,1)] = nodes[array_upper(nodes,1)])
    AND NOT (tags->>'piste:type' = 'skitour')"""

ROUTES = PisteTableConfig()
ROUTES.symbols = ('.slope_symbol', '.nordic_symbol')
ROUTES.symbol_datadir = os.path.join(MEDIA_DIR, 'symbols/slopes')

DEFSTYLE = PisteNetworkStyle(ROUTES.difficulty_map, ROUTES.piste_type)

SYMBOLS = WmtConfig()
SYMBOLS.image_size = (20, 20)
SYMBOLS.text_color = (1, 1, 1) # white
SYMBOLS.text_bgcolor = (0, 0, 0) # black
