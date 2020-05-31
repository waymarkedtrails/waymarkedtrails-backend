# SPDX-License-Identifier: GPL-3.0-only
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2020 Sarah Hoffmann

from db.styles.route_network_style import RouteNetworkStyle
from db.common.route_types import Network

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
ROUTES.symbols = ( 'SwissMobile',
                   'TextSymbol',
                   'ColorBox')

GUIDEPOSTS = GuidePostConfig()
GUIDEPOSTS.subtype = 'skating'
GUIDEPOSTS.require_subtype = True

NETWORKNODES = NetworkNodeConfig()
NETWORKNODES.node_tag = 'rin_ref'

DEFSTYLE = RouteNetworkStyle()
