# SPDX-License-Identifier: GPL-3.0-or-later
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2024 Sarah Hoffmann
""" Main function for building a complex route geometry.
"""
from collections import defaultdict
from itertools import pairwise

from shapely import LineString

from . import route_types as rt


def build_route(members: list[rt.BaseWay | rt.RouteSegment]) -> rt.RouteSegment:
    """ Create a Route representation for the given list of members.

        Members is a list of SimpleWays and Routes as generated by
        get_base_objects().
    """

    members = _ways_to_segments(members)

    if len(members) == 1:
        return rt.RouteSegment(length=members[0].length, main=[members[0]],
                               appendices=[])

    mains = []
    alternatives = []
    appendices = []
    for m in members:
        match m.role:
            case '':
                mains.append(m)
            case 'alternative' | 'detour' | 'alternate' | 'alternate_route' | 'variant':
                alternatives.append(m)
            case _:
                appendices.append(m)

    _flip_order(mains)
    _join_oneways(mains)
    _flip_order(mains)

    return rt.RouteSegment(length=sum(seg.length for seg in mains),
                           main=mains, appendices=appendices)



def _ways_to_segments(members: list[rt.BaseWay | rt.RouteSegment]
                      ) -> list[rt.WaySegment | rt.RouteSegment]:
    """ Combine any BaseWays in the list to WaySegments.
        Return the new list.
    """
    out = []

    for member in members:
        if not isinstance(member, rt.BaseWay):
            # Already a segment, leave untouched
            out.append(member)
        else:
            if not (out and isinstance(out[-1], rt.WaySegment) and out[-1].append_way(member)):
                out.append(rt.WaySegment(length=member.length, ways=[member]))

    return out


def _flip_order(segments: list[rt.WaySegment | rt.RouteSegment]) -> None:
    """ Recheck the order of single-element WaySegments. They might still
        need to be flipped according to their neighbours.
    """
    for s1, s2 in pairwise(segments):
        if s1.last != s2.first:
            if s1.is_reversable() and s1.first == s2.first:
                s1.reverse()
            elif s2.is_reversable() and s1.first == s2.last:
                s1.reverse()
                s2.reverse()
            elif s1.is_reversable() and s2.is_reversable() and s1.last == s2.last:
                s2.reverse()


def _join_oneways(segments: list[rt.AnySegment]) -> None:
    """ Convert adjoining one-ways and roundabouts to
        alternative segments.
    """
    next_id = 0
    while (seg := _next_oneway(segments, next_id)) is not None:
        new_segments = _process_oneways(segments, seg[0], seg[1])
        segments[seg[0]:seg[1]] = new_segments
        if seg[1] < 0:
            break
        next_id = seg[0] + len(new_segments)


def _next_oneway(segments: list[rt.AnySegment], start_at: int) -> None:
    """ Fine the next continuous line of segments that are directional.

        A closed oneway is always returned on its own.
    """
    for i, seg in enumerate(segments[start_at:]):
        if seg.direction != 0:
            oneway_start = i + start_at
            break
    else:
        return None

    first = segments[oneway_start]
    if first.is_closed:
        return (oneway_start, oneway_start + 1)

    endpoints = set((first.first, first.last))
    for i, seg in enumerate(segments[oneway_start:]):
        if seg.direction == 0 or seg.is_closed:
            return (oneway_start, oneway_start + i + 1)
        for pt in (seg.first, seg.last):
            if pt in endpoints:
                endpoints.remove(pt)
            else:
                endpoints.add(pt)
        if not endpoints:
            return (oneway_start, oneway_start + i + 1)

    return (oneway_start, -1)


def _process_oneways(segments: list[rt.AnySegment], frm: int, to: int):
    """ Convert the given subset of segments into a split segment.
    """
    # Compute the possible connection points.
    start_points = []
    if frm > 0:
        prevseg = segments[frm - 1]
        start_points.append(prevseg.last)
        if prevseg.is_reversable() and \
           (frm <= 1 or prevseg.first != segments[frm - 2].last):
           start_points.append(prevseg.first)

    end_points = []
    if to > 0 and to < len(segments):
        nextseg = segments[to]
        end_points.append(nextseg.first)
        if nextseg.is_reversable() and \
         (to >= len(segments) - 1 or nextseg.last != segments[to + 1].first):
            end_points.append(nextseg.last)

    first = segments[frm]
    if isinstance(first, rt.WaySegment) and first.ways[0].is_closed:
        assert to == frm + 1
        assert len(first.ways) == 1
        return [_make_roundabout(first.ways[0], start_points, end_points)]

    if segments[0].first == segments[-1].last:
        return _make_oneways_from_circle(segments[frm:to], start_points, end_points)

    return _make_oneways_directional(segments[frm:to], start_points, end_points)


def _make_roundabout(seg: rt.BaseWay, start_points, end_points) -> rt.SplitSegment:
    """ Build a split section from a single roundabout way.
    """
    if seg.direction == -1:
        seg.reverse()

    points = seg.geom.coords
    spt = None
    ept = None
    for i, pt in enumerate(points):
        if spt is None and pt in start_points:
            spt = i
        if ept is None and pt in end_points:
            ept = i

    if spt is None:
        spt = 0 if ept != 0 else int(len(points)/2)
    if ept is None:
        ept = int(len(points)/2)
        if ept == spt:
            ept = 0

    fwd_way = LineString(points[spt:ept + 1] if spt < ept else points[spt:] + points[1:ept + 1])
    bwd_way = LineString(points[ept:spt + 1] if ept < spt else points[ept:] + points[1:spt + 1])
    fwd = rt.BaseWay(osm_id=seg.osm_id, tags=seg.tags,
                     length=int(round(seg.length*fwd_way.length/seg.geom.length)),
                     direction=1, geom=fwd_way, role=seg.role)
    bwd = rt.BaseWay(osm_id=seg.osm_id, tags=seg.tags,
                     length=int(round(seg.length*bwd_way.length/seg.geom.length)),
                     direction=-1, geom=bwd_way.reverse(), role=seg.role)

    return rt.SplitSegment(length=int((fwd.length + bwd.length)/2),
                           forward=[rt.WaySegment(length=fwd.length, ways=[fwd])],
                           backward=[rt.WaySegment(length=bwd.length, ways=[bwd])])


def _make_oneways_from_circle(segments: list[rt.AnySegment], start_points, end_points):
    """ Build a split section from a list of segments arranged in a circle.
    """
    return segments


def _make_oneways_directional(segments: list[rt.AnySegment], start_points, end_points):
    """ Build a split section from a list of segments arranged in direction
        or the route.

        This is the fallback implementation that also deals with holes in the
        route and badly ordered routes.
    """
    return segments

