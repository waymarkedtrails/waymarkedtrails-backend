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
        length=16, start=0, linear='yes', appendices=[],
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
        length=14, start=0, linear='yes', appendices=[],
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
        length=8, start=0, linear='yes', appendices=[],
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

def test_roundabout_with_approaches(grid):
    g = grid("""\
               6
         2  3     a   b
      0 1                c d
         4  5     8   9
               7
    """)

    ways = [('01', 0), ('123', -1), ('145', 1),
            ('63578a6', 1), ('abc', -1), ('89c', 1), ('cd', 0)]

    route = build_route([rt.BaseWay(oid, {}, len(pts) - 1, dir, g.line(pts), '')
                         for oid, (pts, dir) in enumerate(ways, start=1)])

    assert route == rt.RouteSegment(
        length=8, start=0, linear='yes', appendices=[],
        main=[rt.WaySegment(
                length=1, start=0,
                ways=[rt.BaseWay(osm_id=1, tags=TagStore(), length=1, start=0,
                                 direction=0, role='', geom=g.line('01')
                                )
                     ]),
              rt.SplitSegment(
                length=6, start=1,
                first=tuple(g.coord('1')),
                last=tuple(g.coord('c')),
                forward=[rt.WaySegment(
                            length=2, start=1,
                            ways=[rt.BaseWay(osm_id=3, tags=TagStore(), length=2, start=1,
                                             direction=1, role='', geom=g.line('145')
                                             )
                                 ]
                            ),
                         rt.WaySegment(
                            length=2, start=3,
                            ways=[rt.BaseWay(osm_id=4, tags=TagStore(), length=2, start=3,
                                             direction=1, role='', geom=g.line('578')
                                             )
                                 ]
                            ),
                         rt.WaySegment(
                            length=2, start=5,
                            ways=[rt.BaseWay(osm_id=6, tags=TagStore(), length=2, start=5,
                                             direction=1, role='', geom=g.line('89c')
                                             )
                                 ]
                            )
                        ],
                backward=[rt.WaySegment(
                            length=2, start=1,
                            ways=[rt.BaseWay(osm_id=2, tags=TagStore(), length=2, start=1,
                                             direction=-1, role='', geom=g.line('123')
                                             )
                                 ]
                            ),
                          rt.WaySegment(
                            length=2, start=3,
                            ways=[rt.BaseWay(osm_id=4, tags=TagStore(), length=2, start=3,
                                             direction=-1, role='', geom=g.line('36a')
                                             )
                                 ]
                            ),
                          rt.WaySegment(
                            length=2, start=5,
                            ways=[rt.BaseWay(osm_id=5, tags=TagStore(), length=2, start=5,
                                             direction=-1, role='', geom=g.line('abc')
                                             )
                                 ]
                            )
                         ]
                ),
              rt.WaySegment(
                length=1, start=7,
                ways=[rt.BaseWay(osm_id=7, tags=TagStore(), length=1, start=7,
                                 direction=0, role='', geom=g.line('cd')
                                )
                     ])
            ])


def test_double_roundabout_attached(grid):
    g = grid("""\
        4   7
    0 1   3   6 9
        2   5

     """)

    ways = [('01', 0), ('12341', 1), ('73567', 1), ('69', 0)]

    route = build_route([rt.BaseWay(oid, {}, len(pts) - 1, dir, g.line(pts), '')
                         for oid, (pts, dir) in enumerate(ways, start=1)])

    assert route == rt.RouteSegment(
        length=6, start=0, linear='yes', appendices=[],
        main=[rt.WaySegment(
                length=1, start=0,
                ways=[rt.BaseWay(osm_id=1, tags=TagStore(), length=1, start=0,
                                 direction=0, role='', geom=g.line('01')
                                )
                     ]),
              rt.SplitSegment(
                length=4, start=1,
                first=tuple(g.coord('1')),
                last=tuple(g.coord('6')),
                forward=[rt.WaySegment(
                            length=2, start=1,
                            ways=[rt.BaseWay(osm_id=2, tags=TagStore(), length=2, start=1,
                                             direction=1, role='', geom=g.line('123')
                                             )
                                 ]
                            ),
                         rt.WaySegment(
                            length=2, start=3,
                            ways=[rt.BaseWay(osm_id=3, tags=TagStore(), length=2, start=3,
                                             direction=1, role='', geom=g.line('356')
                                             )
                                 ]
                            )
                        ],
                backward=[rt.WaySegment(
                            length=2, start=1,
                            ways=[rt.BaseWay(osm_id=2, tags=TagStore(), length=2, start=1,
                                             direction=-1, role='', geom=g.line('143')
                                             )
                                 ]
                            ),
                          rt.WaySegment(
                            length=2, start=3,
                            ways=[rt.BaseWay(osm_id=3, tags=TagStore(), length=2, start=3,
                                             direction=-1, role='', geom=g.line('376')
                                             )
                                 ]
                            )
                         ]
                ),
              rt.WaySegment(
                length=1, start=5,
                ways=[rt.BaseWay(osm_id=4, tags=TagStore(), length=1, start=5,
                                 direction=0, role='', geom=g.line('69')
                                )
                     ])
            ])


def test_double_roundabout_with_split_join(grid):
    g = grid("""\
        4   a   7
    0 1   3   8   6 9
        2   b   5

     """)

    ways = [('01', 0), ('12341', 1), ('2b5', 1), ('7a4', 1), ('78567', 1), ('69', 0)]

    route = build_route([rt.BaseWay(oid, {}, len(pts) - 1, dir, g.line(pts), '')
                         for oid, (pts, dir) in enumerate(ways, start=1)])

    assert route == rt.RouteSegment(
        length=6, start=0, linear='yes', appendices=[],
        main=[rt.WaySegment(
                length=1, start=0,
                ways=[rt.BaseWay(osm_id=1, tags=TagStore(), length=1, start=0,
                                 direction=0, role='', geom=g.line('01')
                                )
                     ]),
              rt.SplitSegment(
                length=4, start=1,
                first=tuple(g.coord('1')),
                last=tuple(g.coord('6')),
                forward=[rt.WaySegment(
                            length=1, start=1,
                            ways=[rt.BaseWay(osm_id=2, tags=TagStore(), length=1, start=1,
                                             direction=1, role='', geom=g.line('12')
                                             )
                                 ]
                            ),
                         rt.WaySegment(
                            length=2, start=2,
                            ways=[rt.BaseWay(osm_id=3, tags=TagStore(), length=2, start=2,
                                             direction=1, role='', geom=g.line('2b5')
                                             )
                                 ]
                            ),
                         rt.WaySegment(
                            length=1, start=4,
                            ways=[rt.BaseWay(osm_id=5, tags=TagStore(), length=1, start=4,
                                             direction=1, role='', geom=g.line('56')
                                             )
                                 ]
                            )
                        ],
                backward=[rt.WaySegment(
                            length=1, start=1,
                            ways=[rt.BaseWay(osm_id=2, tags=TagStore(), length=1, start=1,
                                             direction=-1, role='', geom=g.line('14')
                                             )
                                 ]
                            ),
                          rt.WaySegment(
                            length=2, start=2,
                            ways=[rt.BaseWay(osm_id=4, tags=TagStore(), length=2, start=2,
                                             direction=-1, role='', geom=g.line('4a7')
                                             )
                                 ]
                            ),
                          rt.WaySegment(
                            length=1, start=4,
                            ways=[rt.BaseWay(osm_id=5, tags=TagStore(), length=1, start=4,
                                             direction=-1, role='', geom=g.line('76')
                                             )
                                 ]
                            )
                         ]
                ),
              rt.WaySegment(
                length=1, start=5,
                ways=[rt.BaseWay(osm_id=6, tags=TagStore(), length=1, start=5,
                                 direction=0, role='', geom=g.line('69')
                                )
                     ])
            ])
