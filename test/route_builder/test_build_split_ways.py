# SPDX-License-Identifier: GPL-3.0-or-later
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2024 Sarah Hoffmann
import itertools

import pytest

from osgende.common.tags import TagStore
from wmt_db.geometry import build_route
import wmt_db.geometry.route_types as rt

def permute_directions(*ways):
    variants = []
    for w in ways:
        if isinstance(w, str):
            variants.append(((w, 0), (w[::-1], 0)))
        else:
            variants.append(((w[0], w[1]), (w[0][::-1], -w[1])))

    return itertools.product(*variants)


@pytest.mark.parametrize('ways', permute_directions('82', ('234', 1), ('412', 1), '49'))
def test_split_single_way(grid, ways):
    g = grid("""\
               1
           8 2   4  9
               3
        """)

    way_ids = (1, 11, 12, 3)
    way_lens = (5, 6, 6, 5)
    members = [rt.BaseWay(way_ids[i], {}, way_lens[i], w[1], g.line(w[0]), '')
               for i, w in enumerate(ways)]

    route = build_route(members)

    assert route == rt.RouteSegment(
        length=16, start=0, appendices=[], linear='yes',
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
                            ways=[rt.BaseWay(osm_id=11, tags=TagStore(), length=6, start=5,
                                             direction=1, role='', geom=g.line('234')
                                             )
                                 ]
                            )
                        ],
                backward=[rt.WaySegment(
                            length=6, start=5,
                            ways=[rt.BaseWay(osm_id=12, tags=TagStore(), length=6, start=5,
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


@pytest.mark.parametrize('ways', permute_directions('81',
                                                    ('123', 1), ('34', 1),
                                                    ('456', 1), ('61', 1),
                                                    '49'))
def test_split_multi_ways_as_circular(grid, ways):
    g = grid("""\
               6 5
           8 1     4  9
               2 3
        """)


    way_ids = (1, 11, 21, 12, 22, 3)
    way_lens = (5, 3, 4, 3, 4, 5)
    members = [rt.BaseWay(way_ids[i], {}, way_lens[i], w[1], g.line(w[0]), '')
               for i, w in enumerate(ways)]

    route = build_route(members)

    assert route == rt.RouteSegment(
        length=17, start=0, appendices=[], linear='yes',
        main=[rt.WaySegment(
                length=5, start=0,
                ways=[rt.BaseWay(osm_id=1, tags=TagStore(), length=5, start=0,
                                 direction=0, role='', geom=g.line('81'))
                     ]
                ),
              rt.SplitSegment(
                length=7, start=5,
                first=tuple(g.coord(1)),
                last=tuple(g.coord(4)),
                forward=[rt.WaySegment(
                            length=7, start=5,
                            ways=[rt.BaseWay(osm_id=11, tags=TagStore(), length=3, start=5,
                                             direction=1, role='', geom=g.line('123')
                                             ),
                                  rt.BaseWay(osm_id=21, tags=TagStore(), length=4, start=8,
                                             direction=1, role='', geom=g.line('34')
                                             )
                                 ]
                            )
                        ],
                backward=[rt.WaySegment(
                            length=7, start=5,
                            ways=[rt.BaseWay(osm_id=22, tags=TagStore(), length=4, start=5,
                                             direction=-1, role='', geom=g.line('16')
                                             ),
                                  rt.BaseWay(osm_id=12, tags=TagStore(), length=3, start=9,
                                             direction=-1, role='', geom=g.line('654')
                                             )
                                 ]
                            )
                        ]
                ),
              rt.WaySegment(
                length=5, start=12,
                ways=[rt.BaseWay(osm_id=3, tags=TagStore(), length=5, start=12,
                                 direction=0, role='', geom=g.line('49')
                                 )
                     ]
                )
              ]
        )

@pytest.mark.parametrize('ways', permute_directions('81',
                                                    ('123', 1), ('34', 1),
                                                    ('16', -1), ('654', -1),
                                                    '49'))
def test_split_multi_ways_as_directional(grid, ways):
    g = grid("""\
               6 5
           8 1     4  9
               2 3
        """)


    way_ids = (1, 11, 21, 22, 12, 3)
    way_lens = (5, 3, 4, 4, 3, 5)
    members = [rt.BaseWay(way_ids[i], {}, way_lens[i], w[1], g.line(w[0]), '')
               for i, w in enumerate(ways)]

    route = build_route(members)

    assert route == rt.RouteSegment(
        length=17, start=0, appendices=[], linear='yes',
        main=[rt.WaySegment(
                length=5, start=0,
                ways=[rt.BaseWay(osm_id=1, tags=TagStore(), length=5, start=0,
                                 direction=0, role='', geom=g.line('81'))
                     ]
                ),
              rt.SplitSegment(
                length=7, start=5,
                first=tuple(g.coord(1)),
                last=tuple(g.coord(4)),
                forward=[rt.WaySegment(
                            length=7, start=5,
                            ways=[rt.BaseWay(osm_id=11, tags=TagStore(), length=3, start=5,
                                             direction=1, role='', geom=g.line('123')
                                             ),
                                  rt.BaseWay(osm_id=21, tags=TagStore(), length=4, start=8,
                                             direction=1, role='', geom=g.line('34')
                                             )
                                 ]
                            )
                        ],
                backward=[rt.WaySegment(
                            length=7, start=5,
                            ways=[rt.BaseWay(osm_id=22, tags=TagStore(), length=4, start=5,
                                             direction=-1, role='', geom=g.line('16')
                                             ),
                                  rt.BaseWay(osm_id=12, tags=TagStore(), length=3, start=9,
                                             direction=-1, role='', geom=g.line('654')
                                             )
                                 ]
                            )
                        ]
                ),
              rt.WaySegment(
                length=5, start=12,
                ways=[rt.BaseWay(osm_id=3, tags=TagStore(), length=5, start=12,
                                 direction=0, role='', geom=g.line('49')
                                 )
                     ]
                )
              ]
        )


@pytest.mark.parametrize('ways', permute_directions('81',
                                                    ('12', 1), ('34', 1),
                                                    ('16', -1), ('654', -1),
                                                    '49'))
def test_split_multi_ways_as_directional_gap_forward(grid, ways):
    g = grid("""\
               6 5
           8 1     4  9
               2 3
        """)


    way_ids = (1, 11, 21, 22, 12, 3)
    way_lens = (5, 3, 4, 4, 3, 5)
    members = [rt.BaseWay(way_ids[i], {}, way_lens[i], w[1], g.line(w[0]), '')
               for i, w in enumerate(ways)]

    route = build_route(members)

    assert route == rt.RouteSegment(
        length=17, start=0, appendices=[], linear='yes',
        main=[rt.WaySegment(
                length=5, start=0,
                ways=[rt.BaseWay(osm_id=1, tags=TagStore(), length=5, start=0,
                                 direction=0, role='', geom=g.line('81'))
                     ]
                ),
              rt.SplitSegment(
                length=7, start=5,
                first=tuple(g.coord(1)),
                last=tuple(g.coord(4)),
                forward=[rt.WaySegment(
                            length=3, start=5,
                            ways=[rt.BaseWay(osm_id=11, tags=TagStore(), length=3, start=5,
                                             direction=1, role='', geom=g.line('12')
                                             )
                                 ]
                            ),
                         rt.WaySegment(
                            length=4, start=10,
                            ways=[rt.BaseWay(osm_id=21, tags=TagStore(), length=4, start=10,
                                             direction=1, role='', geom=g.line('34')
                                             )
                                 ]
                            )
                        ],
                backward=[rt.WaySegment(
                            length=7, start=5,
                            ways=[rt.BaseWay(osm_id=22, tags=TagStore(), length=4, start=5,
                                             direction=-1, role='', geom=g.line('16')
                                             ),
                                  rt.BaseWay(osm_id=12, tags=TagStore(), length=3, start=9,
                                             direction=-1, role='', geom=g.line('654')
                                             )
                                 ]
                            )
                        ]
                ),
              rt.WaySegment(
                length=5, start=14,
                ways=[rt.BaseWay(osm_id=3, tags=TagStore(), length=5, start=14,
                                 direction=0, role='', geom=g.line('49')
                                 )
                     ]
                )
              ]
        )


@pytest.mark.parametrize('ways', permute_directions('81',
                                                    ('123', 1), ('34', 1),
                                                    ('16', -1), ('54', -1),
                                                    '49'))
def test_split_multi_ways_as_directional_gap_backward(grid, ways):
    g = grid("""\
               6 5
           8 1     4  9
               2 3
        """)


    way_ids = (1, 11, 21, 22, 12, 3)
    way_lens = (5, 3, 4, 4, 3, 5)
    members = [rt.BaseWay(way_ids[i], {}, way_lens[i], w[1], g.line(w[0]), '')
               for i, w in enumerate(ways)]

    route = build_route(members)

    assert route == rt.RouteSegment(
        length=17, start=0, appendices=[], linear='yes',
        main=[rt.WaySegment(
                length=5, start=0,
                ways=[rt.BaseWay(osm_id=1, tags=TagStore(), length=5, start=0,
                                 direction=0, role='', geom=g.line('81'))
                     ]
                ),
              rt.SplitSegment(
                length=7, start=5,
                first=tuple(g.coord(1)),
                last=tuple(g.coord(4)),
                forward=[rt.WaySegment(
                            length=7, start=5,
                            ways=[rt.BaseWay(osm_id=11, tags=TagStore(), length=3, start=5,
                                             direction=1, role='', geom=g.line('123')
                                             ),
                                  rt.BaseWay(osm_id=21, tags=TagStore(), length=4, start=8,
                                             direction=1, role='', geom=g.line('34')
                                             )
                                 ]
                            )
                        ],
                backward=[rt.WaySegment(
                            length=4, start=5,
                            ways=[rt.BaseWay(osm_id=22, tags=TagStore(), length=4, start=5,
                                             direction=-1, role='', geom=g.line('16')
                                             )
                                  ]
                            ),
                          rt.WaySegment(
                            length=3, start=11,
                            ways=[
                                  rt.BaseWay(osm_id=12, tags=TagStore(), length=3, start=11,
                                             direction=-1, role='', geom=g.line('54')
                                             )
                                 ]
                            )
                        ]
                ),
              rt.WaySegment(
                length=5, start=14,
                ways=[rt.BaseWay(osm_id=3, tags=TagStore(), length=5, start=14,
                                 direction=0, role='', geom=g.line('49')
                                 )
                     ]
                )
              ]
        )


@pytest.mark.parametrize('ways', permute_directions('81',
                                                    ('23', 1), ('34', 1),
                                                    ('16', -1), ('654', -1),
                                                    '49'))
def test_split_multi_ways_as_directional_gap_forward_beginning(grid, ways):
    g = grid("""\
               6 5
           8 1     4  9
               2 3
        """)


    way_ids = (1, 11, 21, 22, 12, 3)
    way_lens = (5, 3, 4, 4, 3, 5)
    members = [rt.BaseWay(way_ids[i], {}, way_lens[i], w[1], g.line(w[0]), '')
               for i, w in enumerate(ways)]

    route = build_route(members)

    assert route == rt.RouteSegment(
        length=17, start=0, appendices=[], linear='yes',
        main=[rt.WaySegment(
                length=5, start=0,
                ways=[rt.BaseWay(osm_id=1, tags=TagStore(), length=5, start=0,
                                 direction=0, role='', geom=g.line('81'))
                     ]
                ),
              rt.SplitSegment(
                length=7, start=5,
                first=tuple(g.coord(1)),
                last=tuple(g.coord(4)),
                forward=[rt.WaySegment(
                            length=7, start=7,
                            ways=[rt.BaseWay(osm_id=11, tags=TagStore(), length=3, start=7,
                                             direction=1, role='', geom=g.line('23')
                                             ),
                                  rt.BaseWay(osm_id=21, tags=TagStore(), length=4, start=10,
                                             direction=1, role='', geom=g.line('34')
                                             )
                                 ]
                            )
                        ],
                backward=[rt.WaySegment(
                            length=7, start=5,
                            ways=[rt.BaseWay(osm_id=22, tags=TagStore(), length=4, start=5,
                                             direction=-1, role='', geom=g.line('16')
                                             ),
                                  rt.BaseWay(osm_id=12, tags=TagStore(), length=3, start=9,
                                             direction=-1, role='', geom=g.line('654')
                                             )
                                 ]
                            )
                        ]
                ),
              rt.WaySegment(
                length=5, start=14,
                ways=[rt.BaseWay(osm_id=3, tags=TagStore(), length=5, start=14,
                                 direction=0, role='', geom=g.line('49')
                                 )
                     ]
                )
              ]
        )


@pytest.mark.parametrize('ways', permute_directions('81',
                                                    ('123', 1), ('34', 1),
                                                    ('65', -1), ('54', -1),
                                                    '49'))
def test_split_multi_ways_as_directional_gap_backward_beginning(grid, ways):
    g = grid("""\
               6 5
           8 1     4  9
               2 3
        """)


    way_ids = (1, 11, 21, 22, 12, 3)
    way_lens = (5, 3, 4, 4, 3, 5)
    members = [rt.BaseWay(way_ids[i], {}, way_lens[i], w[1], g.line(w[0]), '')
               for i, w in enumerate(ways)]

    route = build_route(members)

    assert route == rt.RouteSegment(
        length=17, start=0, appendices=[], linear='yes',
        main=[rt.WaySegment(
                length=5, start=0,
                ways=[rt.BaseWay(osm_id=1, tags=TagStore(), length=5, start=0,
                                 direction=0, role='', geom=g.line('81'))
                     ]
                ),
              rt.SplitSegment(
                length=7, start=5,
                first=tuple(g.coord(1)),
                last=tuple(g.coord(4)),
                forward=[rt.WaySegment(
                            length=7, start=5,
                            ways=[rt.BaseWay(osm_id=11, tags=TagStore(), length=3, start=5,
                                             direction=1, role='', geom=g.line('123')
                                             ),
                                  rt.BaseWay(osm_id=21, tags=TagStore(), length=4, start=8,
                                             direction=1, role='', geom=g.line('34')
                                             )
                                 ]
                            )
                        ],
                backward=[rt.WaySegment(
                            length=7, start=7,
                            ways=[rt.BaseWay(osm_id=22, tags=TagStore(), length=4, start=7,
                                             direction=-1, role='', geom=g.line('65')
                                             ),
                                  rt.BaseWay(osm_id=12, tags=TagStore(), length=3, start=11,
                                             direction=-1, role='', geom=g.line('54')
                                             )
                                 ]
                            )
                        ]
                ),
              rt.WaySegment(
                length=5, start=14,
                ways=[rt.BaseWay(osm_id=3, tags=TagStore(), length=5, start=14,
                                 direction=0, role='', geom=g.line('49')
                                 )
                     ]
                )
              ]
        )


@pytest.mark.parametrize('ways', permute_directions('81',
                                                    ('12', 1), ('23', 1),
                                                    ('16', -1), ('654', -1),
                                                    '49'))
def test_split_multi_ways_as_directional_gap_forward_end(grid, ways):
    g = grid("""\
               6 5
           8 1     4  9
               2 3
        """)


    way_ids = (1, 11, 21, 22, 12, 3)
    way_lens = (5, 3, 4, 4, 3, 5)
    members = [rt.BaseWay(way_ids[i], {}, way_lens[i], w[1], g.line(w[0]), '')
               for i, w in enumerate(ways)]

    route = build_route(members)

    assert route == rt.RouteSegment(
        length=17, start=0, appendices=[], linear='yes',
        main=[rt.WaySegment(
                length=5, start=0,
                ways=[rt.BaseWay(osm_id=1, tags=TagStore(), length=5, start=0,
                                 direction=0, role='', geom=g.line('81'))
                     ]
                ),
              rt.SplitSegment(
                length=7, start=5,
                first=tuple(g.coord(1)),
                last=tuple(g.coord(4)),
                forward=[rt.WaySegment(
                            length=7, start=5,
                            ways=[rt.BaseWay(osm_id=11, tags=TagStore(), length=3, start=5,
                                             direction=1, role='', geom=g.line('12')
                                             ),
                                  rt.BaseWay(osm_id=21, tags=TagStore(), length=4, start=8,
                                             direction=1, role='', geom=g.line('23')
                                             )
                                 ]
                            )
                        ],
                backward=[rt.WaySegment(
                            length=7, start=5,
                            ways=[rt.BaseWay(osm_id=22, tags=TagStore(), length=4, start=5,
                                             direction=-1, role='', geom=g.line('16')
                                             ),
                                  rt.BaseWay(osm_id=12, tags=TagStore(), length=3, start=9,
                                             direction=-1, role='', geom=g.line('654')
                                             )
                                 ]
                            )
                        ]
                ),
              rt.WaySegment(
                length=5, start=14,
                ways=[rt.BaseWay(osm_id=3, tags=TagStore(), length=5, start=14,
                                 direction=0, role='', geom=g.line('49')
                                 )
                     ]
                )
              ]
        )


@pytest.mark.parametrize('ways', permute_directions('81',
                                                    ('123', 1), ('34', 1),
                                                    ('16', -1), ('65', -1),
                                                    '49'))
def test_split_multi_ways_as_directional_gap_backward_end(grid, ways):
    g = grid("""\
               6 5
           8 1     4  9
               2 3
        """)


    way_ids = (1, 11, 21, 22, 12, 3)
    way_lens = (5, 3, 4, 4, 3, 5)
    members = [rt.BaseWay(way_ids[i], {}, way_lens[i], w[1], g.line(w[0]), '')
               for i, w in enumerate(ways)]

    route = build_route(members)

    assert route == rt.RouteSegment(
        length=17, start=0, appendices=[], linear='yes',
        main=[rt.WaySegment(
                length=5, start=0,
                ways=[rt.BaseWay(osm_id=1, tags=TagStore(), length=5, start=0,
                                 direction=0, role='', geom=g.line('81'))
                     ]
                ),
              rt.SplitSegment(
                length=7, start=5,
                first=tuple(g.coord(1)),
                last=tuple(g.coord(4)),
                forward=[rt.WaySegment(
                            length=7, start=5,
                            ways=[rt.BaseWay(osm_id=11, tags=TagStore(), length=3, start=5,
                                             direction=1, role='', geom=g.line('123')
                                             ),
                                  rt.BaseWay(osm_id=21, tags=TagStore(), length=4, start=8,
                                             direction=1, role='', geom=g.line('34')
                                             )
                                 ]
                            )
                        ],
                backward=[rt.WaySegment(
                            length=7, start=5,
                            ways=[rt.BaseWay(osm_id=22, tags=TagStore(), length=4, start=5,
                                             direction=-1, role='', geom=g.line('16')
                                             ),
                                  rt.BaseWay(osm_id=12, tags=TagStore(), length=3, start=9,
                                             direction=-1, role='', geom=g.line('65')
                                             )
                                 ]
                            )
                        ]
                ),
              rt.WaySegment(
                length=5, start=14,
                ways=[rt.BaseWay(osm_id=3, tags=TagStore(), length=5, start=14,
                                 direction=0, role='', geom=g.line('49')
                                 )
                     ]
                )
              ]
        )


@pytest.mark.parametrize('ways', permute_directions(('23', 1), ('34', 1),
                                                    ('65', -1), ('54', -1),
                                                    '49'))
def test_split_multi_ways_as_directional_gap_both_beginning(grid, ways):
    g = grid("""\
               6 5
           8 1     4  9
               2 3
        """)


    way_ids = (11, 21, 22, 12, 3)
    way_lens = (3, 4, 4, 3, 5)
    members = [rt.BaseWay(1, {}, 5, 0, g.line('81'), '')] + \
              [rt.BaseWay(way_ids[i], {}, way_lens[i], w[1], g.line(w[0]), '')
               for i, w in enumerate(ways)]

    route = build_route(members)

    assert route == rt.RouteSegment(
        length=17, start=0, appendices=[], linear='no',
        main=[rt.WaySegment(
                length=5, start=0,
                ways=[rt.BaseWay(osm_id=1, tags=TagStore(), length=5, start=0,
                                 direction=0, role='', geom=g.line('81'))
                     ]
                ),
              rt.SplitSegment(
                length=7, start=7,
                first=tuple(g.coord(2)),
                last=tuple(g.coord(4)),
                forward=[rt.WaySegment(
                            length=7, start=7,
                            ways=[rt.BaseWay(osm_id=11, tags=TagStore(), length=3, start=7,
                                             direction=1, role='', geom=g.line('23')
                                             ),
                                  rt.BaseWay(osm_id=21, tags=TagStore(), length=4, start=10,
                                             direction=1, role='', geom=g.line('34')
                                             )
                                 ]
                            )
                        ],
                backward=[rt.WaySegment(
                            length=7, start=9,
                            ways=[rt.BaseWay(osm_id=22, tags=TagStore(), length=4, start=9,
                                             direction=-1, role='', geom=g.line('65')
                                             ),
                                  rt.BaseWay(osm_id=12, tags=TagStore(), length=3, start=13,
                                             direction=-1, role='', geom=g.line('54')
                                             )
                                 ]
                            )
                        ]
                ),
              rt.WaySegment(
                length=5, start=16,
                ways=[rt.BaseWay(osm_id=3, tags=TagStore(), length=5, start=16,
                                 direction=0, role='', geom=g.line('49')
                                 )
                     ]
                )
              ]
        )


@pytest.mark.parametrize('ways', permute_directions('81',
                                                    ('12', 1), ('23', 1),
                                                    ('16', -1), ('65', -1)))
def test_split_multi_ways_as_directional_gap_both_end(grid, ways):
    g = grid("""\
               6 5
           8 1     4  9
               2 3
        """)


    way_ids = (1, 11, 21, 22, 12)
    way_lens = (5, 3, 4, 4, 3)
    members = [rt.BaseWay(way_ids[i], {}, way_lens[i], w[1], g.line(w[0]), '')
               for i, w in enumerate(ways)] + \
              [rt.BaseWay(3, {}, 5, 0, g.line('49'), '')]

    route = build_route(members)

    assert route == rt.RouteSegment(
        length=17, start=0, appendices=[], linear='no',
        main=[rt.WaySegment(
                length=5, start=0,
                ways=[rt.BaseWay(osm_id=1, tags=TagStore(), length=5, start=0,
                                 direction=0, role='', geom=g.line('81'))
                     ]
                ),
              rt.SplitSegment(
                length=7, start=5,
                first=tuple(g.coord(1)),
                last=tuple(g.coord(3)),
                forward=[rt.WaySegment(
                            length=7, start=5,
                            ways=[rt.BaseWay(osm_id=11, tags=TagStore(), length=3, start=5,
                                             direction=1, role='', geom=g.line('12')
                                             ),
                                  rt.BaseWay(osm_id=21, tags=TagStore(), length=4, start=8,
                                             direction=1, role='', geom=g.line('23')
                                             )
                                 ]
                            )
                        ],
                backward=[rt.WaySegment(
                            length=7, start=5,
                            ways=[rt.BaseWay(osm_id=22, tags=TagStore(), length=4, start=5,
                                             direction=-1, role='', geom=g.line('16')
                                             ),
                                  rt.BaseWay(osm_id=12, tags=TagStore(), length=3, start=9,
                                             direction=-1, role='', geom=g.line('65')
                                             )
                                 ]
                            )
                        ]
                ),
              rt.WaySegment(
                length=5, start=16,
                ways=[rt.BaseWay(osm_id=3, tags=TagStore(), length=5, start=16,
                                 direction=0, role='', geom=g.line('49')
                                 )
                     ]
                )
              ]
        )


@pytest.mark.parametrize('ways', permute_directions(('234', 1),
                                                    ('654', -1),
                                                    '49'))
def test_split_simple_ways_as_directional_gap_both_beginning(grid, ways):
    g = grid("""\
               6 5
           8 1     4  9
               2 3
        """)


    way_ids = (11, 12, 3)
    way_lens = (7, 7, 5)
    members = [rt.BaseWay(1, {}, 5, 0, g.line('81'), '')] + \
              [rt.BaseWay(way_ids[i], {}, way_lens[i], w[1], g.line(w[0]), '')
               for i, w in enumerate(ways)]

    route = build_route(members)

    assert route == rt.RouteSegment(
        length=17, start=0, appendices=[], linear='no',
        main=[rt.WaySegment(
                length=5, start=0,
                ways=[rt.BaseWay(osm_id=1, tags=TagStore(), length=5, start=0,
                                 direction=0, role='', geom=g.line('81'))
                     ]
                ),
              rt.SplitSegment(
                length=7, start=7,
                first=tuple(g.coord(2)),
                last=tuple(g.coord(4)),
                forward=[rt.WaySegment(
                            length=7, start=7,
                            ways=[rt.BaseWay(osm_id=11, tags=TagStore(), length=7, start=7,
                                             direction=1, role='', geom=g.line('234')
                                             )
                                 ]
                            )
                        ],
                backward=[rt.WaySegment(
                            length=7, start=9,
                            ways=[rt.BaseWay(osm_id=12, tags=TagStore(), length=7, start=9,
                                             direction=-1, role='', geom=g.line('654')
                                             )
                                 ]
                            )
                        ]
                ),
              rt.WaySegment(
                length=5, start=16,
                ways=[rt.BaseWay(osm_id=3, tags=TagStore(), length=5, start=16,
                                 direction=0, role='', geom=g.line('49')
                                 )
                     ]
                )
              ]
        )

