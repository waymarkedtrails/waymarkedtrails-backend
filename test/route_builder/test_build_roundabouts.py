# SPDX-License-Identifier: GPL-3.0-or-later
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2024 Sarah Hoffmann
import json

import pytest

from osgende.common.tags import TagStore
from wmt_db.geometry import build_route
import wmt_db.geometry.route_types as rt

@pytest.mark.parametrize('rd', ['12341', '23412', '34123', '41234'])
@pytest.mark.parametrize('l1', ['82', '28'])
@pytest.mark.parametrize('l2', ['49', '94'])
def test_roundabout_middle(grid, rd, l1, l2):
    g = grid("""\
               1
           8 2   4  9
               3
        """)
    route = build_route([
        rt.BaseWay(1, {}, 5, 0, g.line(l1), ''),
        rt.BaseWay(2, {}, 12, 1, g.line(rd), ''),
        rt.BaseWay(3, {}, 5, 0, g.line(l2), '')
    ])

    assert route == rt.RouteSegment(
        length=16, appendices=[],
        main=[rt.WaySegment(
                length=5,
                ways=[rt.BaseWay(osm_id=1, tags=TagStore(), length=5,
                                 direction=0, role='', geom=g.line('82'))
                     ]
                ),
              rt.SplitSegment(
                length=6,
                forward=[rt.WaySegment(
                            length=6,
                            ways=[rt.BaseWay(osm_id=2, tags=TagStore(), length=6,
                                             direction=1, role='', geom=g.line('234')
                                             )
                                 ]
                            )
                        ],
                backward=[rt.WaySegment(
                            length=6,
                            ways=[rt.BaseWay(osm_id=2, tags=TagStore(), length=6,
                                             direction=1, role='', geom=g.line('412')
                                             )
                                 ]
                            )
                        ]
                ),
              rt.WaySegment(
                length=5,
                ways=[rt.BaseWay(osm_id=3, tags=TagStore(), length=5,
                                 direction=0, role='', geom=g.line('49')
                                 )
                     ]
                )
              ]
        )


@pytest.mark.parametrize('l2', ['49', '94'])
def test_roundabout_beginning(grid, l2):
    g = grid("""\
               1
             2   4  9
               3
        """)

    route = build_route([
        rt.BaseWay(2, {}, 12, 1, g.line('12341'), ''),
        rt.BaseWay(3, {}, 5, 0, g.line(l2), '')
    ])

    assert route == rt.RouteSegment(
        length=11, appendices=[],
        main=[rt.SplitSegment(
                length=6,
                forward=[rt.WaySegment(
                            length=9,
                            ways=[rt.BaseWay(osm_id=2, tags=TagStore(), length=9,
                                             direction=1, role='', geom=g.line('1234')
                                             )
                                 ]
                            )
                        ],
                backward=[rt.WaySegment(
                            length=3,
                            ways=[rt.BaseWay(osm_id=2, tags=TagStore(), length=3,
                                             direction=1, role='', geom=g.line('41')
                                             )
                                 ]
                            )
                        ]
                ),
              rt.WaySegment(
                length=5,
                ways=[rt.BaseWay(osm_id=3, tags=TagStore(), length=5,
                                 direction=0, role='', geom=g.line('49')
                                 )
                     ]
                )
              ]
        )


@pytest.mark.parametrize('l1', ['82', '28'])
def test_roundabout_end(grid, l1):
    g = grid("""\
               1
           8 2   4
               3
        """)
    route = build_route([
        rt.BaseWay(1, {}, 5, 0, g.line(l1), ''),
        rt.BaseWay(2, {}, 12, 1, g.line('12341'), '')
    ])

    assert route == rt.RouteSegment(
        length=11, appendices=[],
        main=[rt.WaySegment(
                length=5,
                ways=[rt.BaseWay(osm_id=1, tags=TagStore(), length=5,
                                 direction=0, role='', geom=g.line('82'))
                     ]
                ),
              rt.SplitSegment(
                length=6,
                forward=[rt.WaySegment(
                            length=3,
                            ways=[rt.BaseWay(osm_id=2, tags=TagStore(), length=3,
                                             direction=1, role='', geom=g.line('23')
                                             )
                                 ]
                            )
                        ],
                backward=[rt.WaySegment(
                            length=9,
                            ways=[rt.BaseWay(osm_id=2, tags=TagStore(), length=9,
                                             direction=1, role='', geom=g.line('3412')
                                             )
                                 ]
                            )
                        ]
                )
             ]
        )

