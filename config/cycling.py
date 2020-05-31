# SPDX-License-Identifier: GPL-3.0-only
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2020 Sarah Hoffmann

from db.styles.route_network_style import RouteNetworkStyle
from db.common.route_types import Network

from config.common import *

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
ROUTES.symbols = ( 'NorwichColorBox',
                   'SwissMobile',
                   'JelRef',
                   'TextColorBelow',
                   'TextSymbol',
                   'ColorBox')

GUIDEPOSTS = GuidePostConfig()
GUIDEPOSTS.subtype = 'bicycle'
GUIDEPOSTS.require_subtype = True

NETWORKNODES = NetworkNodeConfig()
NETWORKNODES.node_tag = 'rcn_ref'

DEFSTYLE = RouteNetworkStyle()
