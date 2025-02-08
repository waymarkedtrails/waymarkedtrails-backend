# SPDX-License-Identifier: GPL-3.0-or-later
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2024 Sarah Hoffmann
""" Main function for building a complex route geometry.
"""
from typing import Iterator
from collections import defaultdict
from itertools import pairwise

import shapely

from . import route_types as rt


def build_route(members: list[rt.BaseWay | rt.RouteSegment]) -> rt.RouteSegment:
    """ Create a Route representation for the given list of members.

        Members is a list of WaySegments and Routes as generated by
        get_base_objects().
    """

    members = _ways_to_segments(members)

    if len(members) == 1:
        members[0].adjust_start_point(0)
        return rt.RouteSegment(length=members[0].length, main=members, appendices=[], start=0)

    simple_mains, appendices = _split_off_main_route(members)

    # no mains found? Odd. Then build the way as if no roles were given.
    if not simple_mains:
        if not appendices:
            return None

        for sub in appendices:
            for seg in sub:
                if isinstance(seg, rt.RouteSegment):
                    seg.role = ''
                else:
                    for w in seg.ways:
                        w.role = ''
                simple_mains.append(seg)
        appendices = []

    # create the split segments
    mains: list[rt.AnySegment] = []

    for seg in _generate_oneways(simple_mains):
        if seg.oneway and not seg[0].is_roundabout():
            _process_oneways(seg, mains)
        else:
            mains.extend(seg)

    _flip_order(mains)

    # now we have enough information to split roundabouts
    for i, seg in enumerate(mains):
        if isinstance(seg, rt.WaySegment) and seg.is_roundabout():
            _make_roundabout(mains, i)

    # merge split segments where possible
    merged = []
    for seg in mains:
        if not (merged and isinstance(merged[-1], rt.SplitSegment) and merged[-1].merge_split(seg)):
            merged.append(seg)

    assert merged
    route = rt.RouteSegment(length=sum(seg.length for seg in merged), main=merged, appendices=[])
    route.adjust_start_point(0)

    for appendix in appendices:
        _add_appendix_to_route(route, appendix)

    return route


def _split_off_main_route(members: rt.BaseSegmentList
                          ) -> tuple[rt.BaseSegmentList, list[rt.BaseSegmentList]]:
    """ Split the member list into mains and appendices.

        The appendices will be sorted into lists of continuous pieces with the
        same role and instance type.
    """
    mains = []
    appendices = []
    current_appendix = []
    current_role = ''

    for m in members:
        if m.role:
            if isinstance(m, rt.RouteSegment):
                if current_appendix:
                    appendices.append(current_appendix)
                    current_appendix = []
                appendices.append([m])
            else:
                if current_appendix and current_role != m.role:
                    appendices.append(current_appendix)
                    current_appendix = []
                current_role = m.role
                current_appendix.append(m)
        else:
            # a piece of main section.
            if current_appendix:
                appendices.append(current_appendix)
                current_appendix = []
            mains.append(m)

    if current_appendix:
        appendices.append(current_appendix)

    return mains, appendices


def _ways_to_segments(members: list[rt.BaseWay | rt.RouteSegment]) -> list[rt.BaseSegment]:
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


def _flip_order(segments: list[rt.AnySegment]) -> None:
    """ Recheck the order of flippable segments. They might still
        need to be flipped according to their neighbours.
    """
    for i, seg in enumerate(segments):
        if not seg.is_reversable() or seg.is_roundabout():
            continue
        if i > 0:
            prev = segments[i - 1]
            if prev.last == seg.first \
               or (prev.is_roundabout() and seg.first in prev.ways[0].geom.coords):
               continue
        if i < len(segments) - 1:
            nxt = segments[i + 1]
            if seg.last == nxt.first \
               or (nxt.is_roundabout() and seg.last in nxt.ways[0].geom.coords) \
               or (nxt.is_reversable() and seg.last == nxt.last):
                continue

        if i > 0:
            prev = segments[i - 1]
            if prev.last == seg.last \
               or (prev.is_roundabout() and seg.last in prev.ways[0].geom.coords):
                seg.reverse()
                continue
        if i < len(segments) - 1:
            nxt = segments[i + 1]
            if seg.first == nxt.first \
               or (nxt.is_roundabout() and seg.first in nxt.ways[0].geom.coords) \
               or (nxt.is_reversable() and seg.first == nxt.last):
                seg.reverse()


def _generate_oneways(segments: rt.BaseSegmentList) -> Iterator[rt.BaseSegmentView]:
    """ Return pieces of continuous oneway/twoway segments.
    """
    start_id = 0
    oneway = None
    for i, seg in enumerate(segments):
        if oneway != (seg.direction != 0) or seg.is_roundabout():
            if start_id < i:
                yield rt.BaseSegmentView(segments, start_id, i, oneway)
            start_id = i
            oneway = seg.direction != 0
        if seg.is_roundabout():
            yield rt.BaseSegmentView(segments, i, i + 1, oneway)
            start_id = i + 1
            oneway = None

    if oneway is not None:
        yield rt.BaseSegmentView(segments, start_id, len(segments), oneway)


def _process_oneways(segments: rt.BaseSegmentView, outlist: list[rt.AnySegment]) -> None:
    """ Create a sequence of split segments from the given list of base segments
        and it to the 'outlist'.
    """
    start_points = []
    if (prevseg := segments.get_predecessor()) is not None:
        if prevseg.is_roundabout():
            start_points.extend(prevseg.ways[0].geom.coords)
        else:
            start_points.append(prevseg.last)
            if prevseg.is_reversable():
                prevprevseg = segments.get_predecessor(2)
                if prevprevseg is None or prevseg.first != prevprevseg.last:
                    start_points.append(prevseg.first)

    end_points = []
    if (nextseg := segments.get_successor()) is not None:
        if nextseg.is_roundabout():
            end_points.extend(nextseg.ways[0].geom.coords)
        else:
            end_points.append(nextseg.first)
            if nextseg.is_reversable():
                nextnextseg = segments.get_successor(2)
                if nextnextseg is None or nextseg.last != nextnextseg.first:
                    end_points.append(nextseg.last)

    if len(segments) == 1:
        seg = segments[0]
        if isinstance(seg, rt.WaySegment):
            assert not seg.is_roundabout()
            if seg.is_closed:
                outlist.append(_make_circular(seg, start_points, end_points))
            else:
                outlist.append(_make_simple_splitway(seg, start_points, end_points))
        else:
            # with only one segment, this can't possibly be split, add as is
            outlist.append(seg)
    else:
        _make_oneways_directional(segments, start_points, end_points, outlist)


def _make_roundabout(segments: list[rt.AnySegment], pos: int) -> None:
    """ Build a split section from a single roundabout way.
    """
    seg = segments[pos].ways[0]
    if seg.direction == -1:
        seg.reverse()

    points = list(seg.geom.coords)
    prev = segments[pos - 1] if pos > 0 else None
    nxt = segments[pos + 1] if pos < len(segments) - 1 else None

    def _find_point(pt):
        try:
            return points.index(pt)
        except ValueError:
            return None

    # forward direction
    if prev is not None:
        spt = _find_point(prev.forward[-1].last if isinstance(prev, rt.SplitSegment) else prev.last)
    else:
        spt = None
    if nxt is not None:
        if nxt.is_roundabout():
            for pt in nxt.ways[0].geom.coords:
                try:
                    ept = points.index(pt)
                    break
                except ValueError:
                    pass
            else:
                ept = None
        else:
            ept = _find_point(nxt.forward[0].first if isinstance(nxt, rt.SplitSegment) else nxt.first)
    else:
        ept = None

    if spt is None:
        spt = 0 if ept != 0 else int(len(points)/2)
    if ept is None:
        ept = int(len(points)/2)
        if ept == spt:
            ept = 0

    fwd_way = shapely.LineString(points[spt:ept + 1] if spt < ept else points[spt:] + points[1:ept + 1])
    assert fwd_way.length > 0

    # backward direction
    if prev is not None:
        spt = _find_point(prev.backward[-1].last if isinstance(prev, rt.SplitSegment) else prev.last)
    else:
        spt = None
    if nxt is not None:
        if nxt.is_roundabout():
            for pt in nxt.ways[0].geom.coords:
                try:
                    ept = points.index(pt)
                    break
                except ValueError:
                    pass
            else:
                ept = None
        else:
            ept = _find_point(nxt.backward[0].first if isinstance(nxt, rt.SplitSegment) else nxt.first)
    else:
        ept = None

    if spt is None:
        spt = 0 if ept != 0 else int(len(points)/2)
    if ept is None:
        ept = int(len(points)/2)
        if ept == spt:
            ept = 0

    bwd_way = shapely.LineString(points[ept:spt + 1] if ept < spt else points[ept:] + points[1:spt + 1])
    assert bwd_way.length > 0

    fwd = rt.BaseWay(osm_id=seg.osm_id, tags=seg.tags,
                     length=int(round(seg.length*fwd_way.length/seg.geom.length)),
                     direction=1, geom=fwd_way, role=seg.role)
    bwd = rt.BaseWay(osm_id=seg.osm_id, tags=seg.tags,
                     length=int(round(seg.length*bwd_way.length/seg.geom.length)),
                     direction=-1, geom=bwd_way.reverse(), role=seg.role)

    segments[pos] = rt.SplitSegment(length=fwd.length,
                           forward=[rt.WaySegment(length=fwd.length, ways=[fwd])],
                           backward=[rt.WaySegment(length=bwd.length, ways=[bwd])],
                           first=fwd.first,
                           last=fwd.last)


def _make_circular(seg: rt.WaySegment, start_points, end_points) -> rt.SplitSegment | rt.WaySegment:
    """ Convert a cicular multi-way WaySegment into a split segment by
        cutting at the most conventient place.
    """
    if seg.first in start_points and end_points:
        for i, way in enumerate(seg.ways):
            if i > 0 and way.first in end_points:
                split_idx = i
                break
        else:
            mp = shapely.MultiPoint(end_points)
            dist, split_idx = min((shapely.distance(mp, shapely.Point(way.first)), i)
                                  for i, way in enumerate(seg.ways) if i > 0)
    elif seg.first in end_points and start_points:
        for i, way in enumerate(seg.ways):
            if i > 0 and way.first in start_points:
                split_idx = i
                break
        else:
            mp = shapely.MultiPoint(start_points)
            dist, split_idx = min((shapely.distance(mp, shapely.Point(way.first)), i)
                                  for i, way in enumerate(seg.ways) if i > 0)
    else:
        split_idx = int(len(seg.ways)/2)

    fwd, bwd = seg.split_way(split_idx)

    if seg.direction == 1:
        bwd.reverse()
    else:
        fwd.reverse()

    return rt.SplitSegment(length=fwd.length, forward=[fwd], backward=[bwd],
                           first=fwd.first, last=fwd.last)


def _make_simple_splitway(seg: rt.WaySegment, start_points, end_points) -> rt.SplitSegment | rt.WaySegment:
    """ Convert a one-way non-circular multi-way WaySegment into a split segment by
        cutting at the most conventient place.
    """
    seglen = len(seg.ways)
    if seglen <= 1:
        return seg

    front_connections = int(seg.first in start_points) + int(seg.last in start_points)
    if front_connections > 0:
        # Create a U-segment with the open ends towards start
        for i, way in enumerate(seg.ways):
            if i == seglen - 1:
                # linear connection between prev and next
                return seg
            if way.last in end_points:
                si = i + 1
                break
        else:
            # couldn't find the other end. If both ends are connected
            # just split the way in the middle, otherwise give up.
            if front_connections > 1:
                si = int(len(seg.ways)/2)
            else:
                return seg

        if seg.direction > 0:
            fwd, bwd = seg.split_way(si)
            bwd.reverse()
        else:
            bwd, fwd = seg.split_way(si)
            fwd.reverse()

        return rt.SplitSegment(length=fwd.length, forward=[fwd], backward=[bwd],
                               first=fwd.first, last=fwd.last)

    back_connections = int(seg.last in end_points) + int(seg.first in end_points)
    if back_connections > 0:
        for i, way in enumerate(seg.ways):
            if i == seglen - 1:
                # linear connection between prev and next
                return seg
            if way.last in start_points:
                si = i + 1
                break
        else:
            # couldn't find the other end. If both ends are connected
            # just split the way in the middle, otherwise give up.
            if back_connections > 1:
                si = int(len(seg.ways)/2)
            else:
                return seg

        if seg.direction > 0:
            bwd, fwd = seg.split_way(si)
            bwd.reverse()
        else:
            fwd, bwd = seg.split_way(si)
            fwd.reverse()

        return rt.SplitSegment(length=fwd.length, forward=[fwd], backward=[bwd],
                           first=fwd.first, last=fwd.last)

    # inconclusive, leave unchanged
    return seg

def _make_oneways_directional(segments: rt.BaseSegmentView, start_points, end_points,
                              out_segments: list[rt.AnySegment]):
    """ Build a split section from a list of segments arranged in direction
        of the route.

        This is the fallback implementation that also deals with holes in the
        route and badly ordered routes.
    """
    # determine starting point
    first_point = segments[0].first
    for seg in segments:
        if seg.first in start_points:
            first_point = seg.first
            break
        if seg.is_reversable() and seg.last in start_points:
            first_point = seg.last
            break
    else:
        # Nothing to determine the starting point,
        # look ahead from the first segment to get a hint on its direction.
        first_seg = None
        for seg in segments:
            if first_seg is None:
                first_seg is seg
                continue
            if first_seg.direction == -seg.direction:
                if first_seg.first == seg.first:
                    first_point = first_seg.first
                    break
                if seg.is_reversable() and first_seg.last == seg.last:
                    first_point = first_seg.last
                    break
            else:
                if first_seg.last == seg.first:
                    first_point = first_seg.last
                    break
                if seg.is_reversable() and first_seg.first == seg.last:
                    first_point = first_seg.first
                    break

    endpts = {1: first_point, -1: first_point}
    segs = {1: [], -1: []}  # indexed by direction

    for i, seg in enumerate(segments):
        if endpts[seg.direction] in end_points:
            if seg.is_reversable():
                seg.reverse()
        elif seg.first != endpts[seg.direction] and seg.is_reversable()\
           and not seg.last in end_points:
            if seg.last == endpts[-seg.direction] or seg.first in end_points:
                seg.reverse()
            else:
                # Look ahead if the next segment might give a hint on the direction.
                for ns in rt.BaseSegmentView(segments.base, segments.start + i + 1, segments.end):
                    if seg.direction == ns.direction:
                        if seg.last == ns.first:
                            break
                        if ns.is_reversable() and seg.first == ns.last:
                            seg.reverse()
                            break
                    else:
                        if seg.first == ns.first:
                            seg.reverse()
                            break
                        if ns.is_reversable() and seg.last == ns.last:
                            break

        segs[seg.direction].append(seg)
        endpts[seg.direction] = seg.last

        if endpts[1] == endpts[-1] and segs[1] and segs[-1]:
            out_segments.append(rt.SplitSegment(
                length=sum(s.length for s in segs[1]),
                forward=segs[1],
                backward=segs[-1],
                first=first_point, last=endpts[1]))

            segs = {1: [], -1: []}
            first_point = endpts[1]

    if segs[1]:
        if segs[-1]:
            out_segments.append(rt.SplitSegment(
                length=sum(s.length for s in segs[1]),
                forward=segs[1],
                backward=segs[-1],
                first=first_point,
                last=endpts[-1] if endpts[-1] in end_points else endpts[1]))
        else:
            out_segments.extend(segs[1])
    elif segs[-1]:
        out_segments.extend(segs[-1])

    return out_segments


def _add_appendix_to_route(route: rt.RouteSegment, segments: list[rt.BaseSegment]) -> None:
    """ Take a list of RouteSegments and WaySegments with the same role
        and create appendixes for the given route.
    """
    if len(segments) > 1:
        # flipping doesn't help here, we could try linearizing though
        pass #XXX

    # XXX no joining of segments and no joining to route yet
    for seg in segments:
        route.appendices.append(rt.AppendixSegment(length=seg.length, start=None, end=None,
                                                   main=[seg]))
