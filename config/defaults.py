# SPDX-License-Identifier: GPL-3.0-only
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2015-2020 Sarah Hoffmann

REPLICATION_URL='https://planet.openstreetmap.org/replication/minute/'
REPLICATION_SIZE=50

#############################################################################
#
# Database settings

DB_NAME = 'planet'
DB_USER = None
DB_PASSWORD = None
DB_RO_USER = 'www-data'
DB_NODESTORE = None

#############################################################################
#
# Local settings

try:
    from config.local import *
except ImportError:
    pass # no local settings provided

