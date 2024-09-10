# SPDX-License-Identifier: GPL-3.0-only
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2021 Sarah Hoffmann

from types import MethodType
from ..styles.route_network_style import RouteNetworkStyle
from ..common.route_types import Network
from wmt_shields.wmt_config import WmtConfig

from .common import *

CAI_LEVEL = {'T' : '1', 'E' : '2', 'EE' : '3'}
VORARLBERG_SYMBOL = {'yellow:white:yellow_upper': 'AL1',
                     'red:white:red_bar': 'AL2',
                     'blue:white:blue_bar': 'AL3'}

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
        if ot.startswith('yellow:') and ot.endswith(':yellow_diamond'):
            outtags.network = 'AL1'
        elif ot == 'red:white:red_bar':
            outtags.network = 'AL2'
        elif ot == 'blue:white:blue_bar':
            outtags.network = 'AL4'
    if tags.get('operator', '') == 'Land Vorarlberg'\
       and network == 'rwn'\
       and tags.get('network:type', '') == 'basic_network':
        if (nw := VORARLBERG_SYMBOL.get(tags.get('osmc:symbol', ''))) is not None:
            outtags.network = nw

    # Italian hiking network (see #266), also uses Swiss system
    if outtags.country == 'it' and network == 'lwn' \
       and tags.get('osmc:symbol', '').startswith('red') and 'cai_scale' in tags:
        outtags.network = 'AL' + CAI_LEVEL.get(tags['cai_scale'], '4')

    # Fränkischer Albverein (around Nürnberg)
    #  too extensive regional network, so downgrade for later display
    if tags.get('operator', '') == u'Fränkischer Albverein':
        outtags.level -= 2


def hiking_add_to_collector(self, c, relinfo):
    if relinfo.top:
        c['toprels'].append(relinfo.id)
        if relinfo.network is None:
            c['class'] |= 1 << relinfo.level
            self.add_shield_to_collector(c, relinfo)
        else:
            c['style'] = relinfo.network
            if relinfo.network.startswith('AL'):
                if relinfo.country not in ('ch', 'at'):
                    self.add_shield_to_collector(c, relinfo)
            elif relinfo.network == 'NDS':
                pass # no shields, no coloring
            else:
                c['class'] |= 1 << relinfo.level
                self.add_shield_to_collector(c, relinfo)
    else:
        c['cldrels'].append(relinfo.id)


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
ROUTES.symbols = ('.image_symbol',
                  '.swiss_mobile',
                  '.jel_symbol',
                  '.kct_symbol',
                  '.cai_hiking_symbol',
                  '.osmc_symbol',
                  '.ref_color_symbol',
                  '.ref_symbol')
ROUTES.symbol_datadir = SYMBOL_DIR / 'hiking'

GUIDEPOSTS = GuidePostConfig()
GUIDEPOSTS.subtype = 'hiking'

NETWORKNODES = NetworkNodeConfig()
NETWORKNODES.node_tag = 'rwn_ref'


SYMBOLS = WmtConfig()
SYMBOLS.shield_path = DATA_DIR / 'shields'
SYMBOLS.shield_names = {
    # with friendly permission of Vogelsberg Touristik
    'vr_vb' :        {'operator': 'Vogelsberger Höhenclub',
                      'name': 'Vulkanring Vogelsberg'},
    # permission via Kulturverein Storndorf
    'judenpfad_vb' : {'name': 'Judenpfad Vogelsberg'},
    # permisson from Verkehrsverein Much
    'igel_much19' :  {'operator' : 'Verkehrsverein Much e.V.',
                      'name':'Familienwanderweg Much'},
    # permission from Stadtmarketing Eupen
    'eupen' : {'operator': 'Stadt Eupen - Stadtmarketing',
               'name': 'Eupen rundum'},
}

RENDER_OPTIONS['swiss_style'] = True
