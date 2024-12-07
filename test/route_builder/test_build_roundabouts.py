# SPDX-License-Identifier: GPL-3.0-or-later
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2024 Sarah Hoffmann
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
        length=16, start=0, appendices=[],
        main=[rt.WaySegment(
                length=5, start=0,
                ways=[rt.BaseWay(osm_id=1, tags=TagStore(), length=5, start=0,
                                 direction=0, role='', geom=g.line('82'))
                     ]
                ),
              rt.SplitSegment(
                length=6, start=5,
                first=tuple(g.coord(2)),
                last=tuple(g.coord(4)),
                forward=[rt.WaySegment(
                            length=6, start=5,
                            ways=[rt.BaseWay(osm_id=2, tags=TagStore(), length=6, start=5,
                                             direction=1, role='', geom=g.line('234')
                                             )
                                 ]
                            )
                        ],
                backward=[rt.WaySegment(
                            length=6, start=5,
                            ways=[rt.BaseWay(osm_id=2, tags=TagStore(), length=6, start=5,
                                             direction=-1, role='', geom=g.line('214')
                                             )
                                 ]
                            )
                        ]
                ),
              rt.WaySegment(
                length=5, start=11,
                ways=[rt.BaseWay(osm_id=3, tags=TagStore(), length=5, start=11,
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
        length=14, start=0, appendices=[],
        main=[rt.SplitSegment(
                length=9, start=0,
                first=tuple(g.coord(1)),
                last=tuple(g.coord(4)),
                forward=[rt.WaySegment(
                            length=9, start=0,
                            ways=[rt.BaseWay(osm_id=2, tags=TagStore(), length=9, start=0,
                                             direction=1, role='', geom=g.line('1234')
                                             )
                                 ]
                            )
                        ],
                backward=[rt.WaySegment(
                            length=3, start=0,
                            ways=[rt.BaseWay(osm_id=2, tags=TagStore(), length=3, start=0,
                                             direction=-1, role='', geom=g.line('14')
                                             )
                                 ]
                            )
                        ]
                ),
              rt.WaySegment(
                length=5, start=9,
                ways=[rt.BaseWay(osm_id=3, tags=TagStore(), length=5, start=9,
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
        length=8, start=0, appendices=[],
        main=[rt.WaySegment(
                length=5, start=0,
                ways=[rt.BaseWay(osm_id=1, tags=TagStore(), length=5, start=0,
                                 direction=0, role='', geom=g.line('82'))
                     ]
                ),
              rt.SplitSegment(
                length=3, start=5,
                first=tuple(g.coord(2)),
                last=tuple(g.coord(3)),
                forward=[rt.WaySegment(
                            length=3, start=5,
                            ways=[rt.BaseWay(osm_id=2, tags=TagStore(), length=3, start=5,
                                             direction=1, role='', geom=g.line('23')
                                             )
                                 ]
                            )
                        ],
                backward=[rt.WaySegment(
                            length=9, start=5,
                            ways=[rt.BaseWay(osm_id=2, tags=TagStore(), length=9, start=5,
                                             direction=-1, role='', geom=g.line('2143')
                                             )
                                 ]
                            )
                        ]
                )
             ]
        )

