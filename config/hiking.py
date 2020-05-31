# SPDX-License-Identifier: GPL-3.0-only
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2020 Sarah Hoffmann

from types import MethodType
from db.styles.route_network_style import RouteNetworkStyle
from db.common.route_types import Network

from config.common import *

def filter_route_tags(outtags, tags):
    """ Additional tag filtering specifically for hiking routes.
    """
    network = tags.get('network', '')
    if network == 'uk_ldp':
        if tags.get('operator', '') == 'National Trails':
            outtags.level = Network.NAT()
        else:
            outtags.level = Network.REG()

    # Czech system
    for (k,v) in tags.items():
        if k.startswith('kct_'):
            outtags.network = 'CT'
            if network == '' and v == 'major':
                outtags.level = Network.NAT(-1) if k[4:] == 'red' else Network.REG(-1)

    # Region-specific tagging:

    # in the UK slightly downgrade nwns (to distinguish them from National Trails)
    if outtags.country == 'gb' and network == 'nwn':
        outtags.level = Network.NAT(-1)

    # find Swiss hiking network
    if outtags.country == 'ch' and network == 'lwn':
        ot = tags.get('osmc:symbol', '')
        if ot.startswith('yellow:'):
            outtags.network = 'AL1'
        if ot.startswith('red:'):
            outtags.network = 'AL2'
        if ot.startswith('blue:'):
            outtags.network = 'AL4'

    # Italian hiking network (see #266), also uses Swiss system
    if outtags.country == 'it' and network == 'lwn' \
        and tags.get('osmc:symbol', '').startswith('red') and 'cai_scale' in tags:
        outtags.network = 'AL' + cai_level.get(tags['cai_scale'], '4')

    # Fränkischer Albverein (around Nürnberg)
    #  too extensive regional network, so downgrade for later display
    if tags.get('operator', '') == u'Fränkischer Albverein':
        outtags.level -= 2


def hiking_add_to_collector(self, c, relinfo):
    if relinfo['top']:
        c['toprels'].append(relinfo['id'])
        if relinfo['network'] is None:
            c['class'] |= 1 << relinfo['level']
            self.add_shield_to_collector(c, relinfo)
        else:
            c['style'] = relinfo['network']
            if relinfo['network'].startswith('AL'):
                if relinfo['country'] != 'ch':
                    self.add_shield_to_collector(c, relinfo)
            elif relinfo['network'] == 'NDS':
                pass # no shields, no coloring
            else:
                c['class'] |= 1 << relinfo['level']
                self.add_shield_to_collector(c, relinfo)
    else:
        c['cldrels'].append(relinfo['id'])


MAPTYPE = 'routes'

DB_SCHEMA = 'hiking'
DB_TABLES = RouteDBTables()

DB_ROUTE_SUBSET = """
    tags ? 'route' and tags->>'type' IN ('route', 'superroute')
    AND array['hiking', 'foot', 'walking'] && regexp_split_to_array(tags->>'route', ';')
    AND NOT (tags ? 'state' AND tags->>'state' = 'proposed')"""

DEFSTYLE = RouteNetworkStyle()
DEFSTYLE.add_to_collector = MethodType(hiking_add_to_collector, DEFSTYLE)

ROUTES = RouteTableConfig()
ROUTES.network_map = {
        'iwn': Network.INT(),
        'nwn': Network.NAT(),
        'rwn': Network.REG(),
        'lwn': Network.LOC()
        }
ROUTES.tag_filter = filter_route_tags
ROUTES.symbols = ( 'ShieldImage',
                   'SwissMobile',
                   'JelRef',
                   'KCTRef',
                   'ItalianHikingRefs',
                   'OSMCSymbol',
                   'TextColorBelow',
                   'TextSymbol')

GUIDEPOSTS = GuidePostConfig()
GUIDEPOSTS.subtype = 'hiking'

NETWORKNODES = NetworkNodeConfig()
NETWORKNODES.node_tag = 'rwn_ref'
