# SPDX-License-Identifier: GPL-3.0-or-later
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2024 Sarah Hoffmann
""" Container for a simple OSM way.
"""
import math
from dataclasses import dataclass

from osgende.common.tags import TagStore
from shapely import LineString

from ..common.json_writer import JsonWriter

def _dist(p0, p1) -> int:
    """ Appoximation of distance between two points in Mercator.
        Euclidean distance is good enough here to estimate size of holes.
    """
    x = p0[0] - p1[0]
    y = p0[1] - p1[1]
    return int(math.sqrt(x * x + y * y))


def _adjust_start_segment_list(start, start_pt, segments):
    for s in segments:
        if start_pt != s.first:
            start += _dist(start_pt, s.first)
        start = s.adjust_start_point(start)
        start_pt = s.last

    return start


@dataclass
class BaseWay:
    """ Container for a single OSM way.
    """
    osm_id: int
    """ OSM Way ID for the segment. """
    tags: TagStore
    """ Full set of OSM tags for the way. """
    length: int
    """ Length in meters. """
    direction: int
    """ Use only Forward: 1, Use only Backward: -1, Bi-directional: 0 """
    geom: LineString
    """ Geometry of the way. Must go forward relative to the primary direction
        of the route."""
    role: str | None = None
    """ Optional role of the way within the relation. """
    start: int | None = None
    """ Distance from beginning of route.
        (Either in meter or in number of members in the relation.)
    """

    @property
    def is_closed(self) -> bool:
        return self.geom.is_closed

    @property
    def first(self) -> tuple[float, float]:
        return self.geom.coords[0]

    @property
    def last(self) -> tuple[float, float]:
        return self.geom.coords[-1]

    def reverse(self) -> None:
        """ Reverse the direction of the way.

            If the way is directional, then the direction will be
            reversed as well.
        """
        self.geom = self.geom.reverse()
        self.direction = -self.direction

    def adjust_start_point(self, start: int) -> None:
        """ Set own start point to the given value and recursively
            adjust the start points of all child segments.
        """
        self.start = start
        return start + self.length

    def to_json(self) -> str:
        return JsonWriter().start_object()\
                .keyval('route_type', 'base')\
                .keyval('start', self.start)\
                .keyval('id', self.osm_id)\
                .keyval('tags', self.tags)\
                .keyval('length', self.length)\
                .keyval('direction', self.direction)\
                .keyval('role', self.role or '')\
                .key('geometry').start_object()\
                    .keyval('type', 'LineString')\
                    .keyval('coordinates', list(self.geom.coords))\
                    .end_object().next()\
                .end_object()()


@dataclass
class WaySegment:
    """ A segment containing only BaseWays that create a linear section
        of way. The BaseWays must have compatible attributes in terms of
        direction and role.
    """
    length: int
    """ Length in meters. """
    ways: list[BaseWay]
    start: int | None = None
    """ Distance from beginning of route.
    """

    @property
    def role(self) -> str:
        assert self.ways
        return self.ways[0].role

    @property
    def direction(self) -> int:
        assert self.ways
        return self.ways[0].direction

    @property
    def is_closed(self) -> bool:
        return self.first == self.last

    @property
    def first(self) -> tuple[float, float]:
        assert self.ways
        return self.ways[0].first

    @property
    def last(self) -> tuple[float, float]:
        assert self.ways
        return self.ways[-1].last

    def is_reversable(self) -> bool:
        return len(self.ways) == 1 and self.first != self.last

    def reverse(self) -> None:
        self.ways.reverse()
        for w in self.ways:
            w.reverse()

    def adjust_start_point(self, start: int) -> None:
        """ Set own start point to the given value and recursively
            adjust the start points of all child segments.
        """
        self.start = start
        return _adjust_start_segment_list(start, self.first, self.ways)

    def append_way(self, way: BaseWay) -> bool:
        """ Try to append the given way at the end of the segment.
            Return true, if that was possible.
        """
        if self.is_closed or way.is_closed \
           or self.role != way.role \
           or (self.direction == 0) != (way.direction == 0):
            return False

        if self._can_add_directional(way):
            self.ways.append(way)
            self.length += way.length
            return True

        return False

    def _can_add_directional(self, way: BaseWay) -> bool:
        if way.first == self.last:
            return self.direction == way.direction

        if way.last == self.last:
            if self.direction == -way.direction:
                way.reverse()
                return True
        elif len(self.ways) == 1:
            if way.first == self.first:
                if self.direction == -way.direction:
                    self.ways[0].reverse()
                    return True
            elif way.last == self.first:
                if self.direction == way.direction:
                    self.ways[0].reverse()
                    way.reverse()
                    return True

        return False

    def to_json(self) -> str:
        out = JsonWriter().start_object()\
                .keyval('route_type', 'linear')\
                .keyval('start', self.start)\
                .keyval('length', self.length)\
                .key('ways').start_array()

        for seg in self.ways:
            out.raw(seg.to_json()).next()

        out.end_array().next().end_object()

        return out()



@dataclass
class SplitSegment:
    """ A segment with different routes for forward and backward.
    """
    length: int
    """ Length of forward route.
    """
    forward: 'list[AnySegment]'
    """ Route for going from the beginning of the segment to the end.
        All directional segments must have direction 1.
    """
    backward: 'list[AnySegment]'
    """ Route to follow when going in the reverse direction of the route.
        Segments are still ordered in the primary section of the route.
        All directional segments must have direction -1.
    """
    first: tuple[float, float]
    """ Coordinate of the beginning of the route.
        Needs to be explicit because forward or backward may have gaps at
        the beginning.
    """
    last: tuple[float, float]
    """ Coordinate of the end of the route.
        Needs to be explicit because forward or backward may have gaps
        at the end.
    """
    start: float | None = None
    """ Distance from beginning of route in meters.
    """

    def is_reversable(self) -> bool:
        return True

    def reverse(self) -> None:
        self.forward, self.backward = self.backward, self.forward
        self.first, self.last = self.last, self.first
        self.forward.reverse()
        for s in self.forward:
            s.reverse()
        self.backward.reverse()
        for s in self.backward:
            s.reverse()
        self.length = sum(s.length for s in self.forward)

    def adjust_start_point(self, start: int) -> None:
        """ Set own start point to the given value and recursively
            adjust the start points of all child segments.
        """
        self.start = start
        return max(_adjust_start_segment_list(start, self.first, s) + _dist(self.last, s[-1].last)
                   for s in (self.backward, self.forward))

    def to_json(self) -> str:
        out = JsonWriter().start_object()\
                .keyval('route_type', 'split')\
                .keyval('start', self.start)\
                .keyval('length', self.length)\
                .key('forward').start_array()

        for seg in self.forward:
            out.raw(seg.to_json()).next()

        out.end_array().next()\
           .key('backward')

        for seg in self.backward:
            out.raw(seg.to_json()).next()

        out.end_array().next().end_object()

        return out()


@dataclass
class AppendixSegment:
    """ A linear section that does not belong to the main route. May contain gaps.
    """
    length: int
    """ Length of the main route excluding gaps between segments. """
    main: 'list[WaySegment | RouteSegment | SplitSegment]'
    """ Linear sequence of segments constituting the appendix.
    """
    start: int | None
    """ Distance in meters from beginning of route where the appendix begins.
        When None, then the appendix is not connected to the route at all.
    """
    end: int | None
    """ Distance in meters from beginning of route where the appendix rejoins
        the route. When None, then the appendix is of an approach type.
        When set, then it is guaranteed to be larger than start,
        i.e. the segment is guaranteed to go along the direction of the route.
    """

    @property
    def role(self) -> str:
        return self.main[0].role

    @property
    def first(self) -> tuple[float, float]:
        return self.main[0].first

    @property
    def last(self) -> tuple[float, float]:
        return self.main[-1].last


@dataclass
class RouteSegment:
    """ A complete route or route leg with splits, alternatives,
        approaches and gaps.
    """
    length: int
    """ Length of the main route excluding gaps between segments. """
    main: 'list[WaySegment | RouteSegment | SplitSegment]'
    """ Linear sequence of segments constituting the main route.
    """
    appendices: 'list[AppendixSegment]'
    """ List of excursions, approaches and alternatives for the route. The role
        must contain the type of approach.
    """
    role: str | None = None
    """ Optional role of the way within the relation. """
    start: int | None = None
    """ Distance from beginning of route.
        (Either in meter or in number of members in the relation.)
    """

    @property
    def first(self) -> tuple[float, float]:
        return self.main[0].first

    @property
    def last(self) -> tuple[float, float]:
        return self.main[-1].last

    def is_reversable(self) -> bool:
        return True  # XXX only without appendices?

    def reverse(self) -> None:
        self.main.reverse()
        for s in self.main:
            s.reverse()
        # XXX effect on appendices?

    def adjust_start_point(self, start: int) -> int:
        """ Set own start point to the given value and recursively
            adjust the start points of all child segments.

            Returns the start point for the next segment.
        """
        end = _adjust_start_segment_list(start, self.first, self.main)

        if self.start is not None:
            rel_adjustment = start - self.start
            # XXX is that right?
            for s in self.appendices:
                s.adjust_start_point(s.start + rel_adjustment)

        self.start = start
        return end

    def to_json(self) -> str:
        out = JsonWriter().start_object()\
                .keyval('route_type', 'route')\
                .keyval('length', self.length)\
                .keyval('start', self.start)\
                .keyval('role', self.role or '')\
                .key('main').start_array()

        for seg in self.main:
            out.raw(seg.to_json()).next()

        out.end_array().next()

        out.key('appendices').start_array()

        for seg in self.appendices:
            out.raw(seg.to_json()).next()

        out.end_array().next().end_object()

        return out()


BaseSegment = WaySegment | RouteSegment
AnySegment = WaySegment | RouteSegment | SplitSegment
