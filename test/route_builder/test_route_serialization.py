# SPDX-License-Identifier: GPL-3.0-or-later
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2024 Sarah Hoffmann
import pytest
import json

import wmt_db.geometry.route_types as rt
from osgende.common.tags import TagStore


EXAMPLES = [
    ('Simple Baseway', lambda g:
     rt.BaseWay(osm_id=1, tags=TagStore({'foo': 'bar'}), length=49,
                direction=0, geom=g.line('123'), role='', start=1)),
    ('Simple WaySegment', lambda g:
     rt.WaySegment(start=1, length=50,
                   ways=[rt.BaseWay(osm_id=1, tags=TagStore({'foo': 'bar'}),
                                    length=20, direction=0,
                                    geom=g.line('123'), role='x', start=1),
                         rt.BaseWay(osm_id=2, tags=TagStore({'foo': 'bar'}),
                                    length=30, direction=0,
                                    geom=g.line('34'), role='x', start=20)])),
    ('Simple SplitSegment', lambda g:
     rt.SplitSegment(start=1, length=50, first=tuple(g.coord(3)),
                     last=tuple(g.coord(4)),
                     forward=[rt.BaseWay(osm_id=1, tags=TagStore(),
                                    length=2, direction=1,
                                    geom=g.line('37'), role='', start=1),
                              rt.BaseWay(osm_id=2, tags=TagStore(),
                                    length=3, direction=0,
                                    geom=g.line('784'), role='', start=2)],
                    backward=[rt.BaseWay(osm_id=5, tags=TagStore(),
                                    length=2, direction=-1,
                                    geom=g.line('394'), role='', start=1)]
                    )),
    ('approach segment', lambda g:
     rt.AppendixSegment(start=1, end=None, length=50,
                   main=[rt.BaseWay(osm_id=1, tags=TagStore({'foo': 'bar'}),
                                    length=20, direction=0,
                                    geom=g.line('123'), role='x', start=1),
                         rt.BaseWay(osm_id=2, tags=TagStore({'foo': 'bar'}),
                                    length=30, direction=0,
                                    geom=g.line('34'), role='x', start=20)])),
    ('alternative segment', lambda g:
     rt.AppendixSegment(start=1, end=30, length=50,
                   main=[rt.BaseWay(osm_id=1, tags=TagStore({'foo': 'bar'}),
                                    length=20, direction=0,
                                    geom=g.line('123'), role='x', start=1),
                         rt.BaseWay(osm_id=2, tags=TagStore({'foo': 'bar'}),
                                    length=30, direction=0,
                                    geom=g.line('34'), role='x', start=20)])),
    ('route segment', lambda g:
     rt.RouteSegment(
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
        )),
]


@pytest.mark.parametrize('name,obj_builder', EXAMPLES)
def test_dumping(grid, name, obj_builder):
    g = grid("""\
              7 8
      1  2  3    4  5  6
               9
    """)

    obj = obj_builder(g)
    print(obj.to_json())

    assert obj == json.loads(obj.to_json(), object_hook=rt.json_decoder_hook)
