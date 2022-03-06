# SPDX-License-Identifier: GPL-3.0-only
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2021 Sarah Hoffmann

from ..styles.route_network_style import RouteNetworkStyle
from ..common.route_types import Network
from wmt_shields.wmt_config import WmtConfig
import wmt_shields.filters as filters

from .common import *

MAPTYPE = 'routes'

DB_SCHEMA = 'cycling'
DB_TABLES = RouteDBTables()

DB_ROUTE_SUBSET  = """
    tags ? 'route' and tags->>'type' IN ('route', 'superroute')
    AND 'bicycle' = any(regexp_split_to_array(tags->>'route', ';'))
    AND NOT (tags ? 'state' AND tags->>'state' = 'proposed')"""

ROUTES = RouteTableConfig()
ROUTES.network_map = {
        'icn': Network.INT(0),
        'ncn': Network.NAT(0),
        'rcn': Network.REG(0),
        'lcn': Network.LOC(0)
        }
ROUTES.symbols = (filters.tags_all('.color_box',
                                   {'operator' : 'Norwich City Council',}),
                  '.swiss_mobile',
                  '.jel_symbol',
                  '.ref_color_symbol',
                  '.ref_symbol',
                  '.color_box')
ROUTES.symbol_datadir = SYMBOL_DIR / 'cycling'

GUIDEPOSTS = GuidePostConfig()
GUIDEPOSTS.subtype = 'bicycle'
GUIDEPOSTS.require_subtype = True

NETWORKNODES = NetworkNodeConfig()
NETWORKNODES.node_tag = 'rcn_ref'

DEFSTYLE = RouteNetworkStyle()

SYMBOLS = WmtConfig()
SYMBOLS.swiss_mobile_bgcolor = (0.66, 0.93, 1.0)
SYMBOLS.swiss_mobile_networks = ('rcn', 'ncn')
