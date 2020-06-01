# SPDX-License-Identifier: GPL-3.0-only
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2020 Sarah Hoffmann

import os

from db.styles.route_network_style import RouteNetworkStyle
from db.common.route_types import Network
from wmt_shields.wmt_config import WmtConfig

from config.common import *

MAPTYPE = 'routes'

DB_SCHEMA = 'skating'
DB_TABLES = RouteDBTables()

DB_ROUTE_SUBSET  = """
    tags ? 'route' and tags->>'type' IN ('route', 'superroute')
    AND 'inline_skates' = any(regexp_split_to_array(tags->>'route', ';'))
    AND NOT (tags ? 'state' AND tags->>'state' = 'proposed')"""

ROUTES = RouteTableConfig()
ROUTES.network_map = {
        'national': Network.NAT(0),
        'regional': Network.REG(0),
        'rin': Network.REG(0),
        'local': Network.LOC(0)
        }
ROUTES.symbols = ( '.swiss_mobile',
                   '.ref_symbol',
                   '.color_box')
ROUTES.symbol_datadir = os.path.join(MEDIA_DIR, 'symbols/skating')

GUIDEPOSTS = GuidePostConfig()
GUIDEPOSTS.subtype = 'skating'
GUIDEPOSTS.require_subtype = True

NETWORKNODES = NetworkNodeConfig()
NETWORKNODES.node_tag = 'rin_ref'

DEFSTYLE = RouteNetworkStyle()

SYMBOLS = WmtConfig()
SYMBOLS.swiss_mobil_bgcolor = (0.82, 0.63, 0.83)
SYMBOLS.swiss_mobil_networks = ('national', 'regional')

#############################################################################
#
# Render settings

RENDERER['source'] = 'map-styles/skatingmap.xml'
