# SPDX-License-Identifier: GPL-3.0-only
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2020 Sarah Hoffmann

from db.styles.route_network_style import RouteNetworkStyle
from db.common.route_types import Network

from config.common import *

MAPTYPE = 'routes'

DB_SCHEMA = 'riding'
DB_TABLES = RouteDBTables()

DB_ROUTE_SUBSET  = """
    tags ? 'route' and tags->>'type' IN ('route', 'superroute')
    AND 'horse' = any(regexp_split_to_array(tags->>'route', ';'))
    AND NOT (tags ? 'state' AND tags->>'state' = 'proposed')"""

ROUTES = RouteTableConfig()
ROUTES.network_map = {
        'nhn': Network.NAT(0),
        'nwn': Network.NAT(0),
        'nwn:kct': Network.NAT(0),
        'ncn': Network.NAT(0),
        'rhn': Network.REG(0),
        'rwn': Network.REG(0),
        'rcn': Network.REG(0),
        'lhn': Network.LOC(0),
        'lwn': Network.LOC(0),
        'lcn': Network.LOC(0),
        }
ROUTES.symbols = ( 'OSMCSymbol',
                   'TextSymbol',
                   'ColorBox')

GUIDEPOSTS = GuidePostConfig()
GUIDEPOSTS.subtype = 'horse'
GUIDEPOSTS.require_subtype = True

NETWORKNODES = NetworkNodeConfig()
NETWORKNODES.node_tag = 'rhn_ref'

DEFSTYLE = RouteNetworkStyle()
