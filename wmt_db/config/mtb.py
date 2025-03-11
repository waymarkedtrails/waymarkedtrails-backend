# SPDX-License-Identifier: GPL-3.0-only
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2022 Sarah Hoffmann

from ..styles.route_network_style import RouteNetworkStyle
from ..common.route_types import Network
from wmt_shields.wmt_config import WmtConfig

from .common import *

MAPTYPE = 'routes'

DB_SCHEMA = 'mtb'
DB_TABLES = RouteDBTables()

DB_ROUTE_SUBSET  = """
    tags ? 'route' and tags->>'type' IN ('route', 'superroute')
    AND 'mtb' = any(regexp_split_to_array(tags->>'route', ';'))
    AND NOT (tags ? 'state' AND tags->>'state' = 'proposed')"""

ROUTES = RouteTableConfig()
ROUTES.network_map = {
        'icn': Network.INT(0),
        'ncn': Network.NAT(0),
        'rcn': Network.REG(0),
        'lcn': Network.LOC(0)
        }
ROUTES.symbols = ('.swiss_mobile',
                  '.jel_symbol',
                  '.ref_color_symbol',
                  '.ref_symbol',
                  '.osmc_symbol',
                  '.color_box')
ROUTES.symbol_datadir = SYMBOL_DIR / 'mtb'

GUIDEPOSTS = GuidePostConfig()
GUIDEPOSTS.subtype = 'mtb'
GUIDEPOSTS.require_subtype = True

DEFSTYLE = RouteNetworkStyle()

SYMBOLS = WmtConfig()
SYMBOLS.swiss_mobile_bgcolor = (0.88, 0.83, 0.32)
SYMBOLS.swiss_mobile_networks = ('rcn', 'ncn')
