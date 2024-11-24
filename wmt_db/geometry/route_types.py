# SPDX-License-Identifier: GPL-3.0-or-later
#
# This file is part of the Waymarked Trails Map Project
# Copyright (C) 2024 Sarah Hoffmann
""" Container for a simple OSM way.
"""
from dataclasses import dataclass

from osgende.common.tags import TagStore
from shapely import LineString

from ..common.json_writer import JsonWriter

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
    start: float | None = None
    """ Distance from beginning of route in meters.
    """

    @property
    def first(self) -> tuple[float, float]:
        return self.forward[0].first

    @property
    def last(self) -> tuple[float, float]:
        return self.forward[-1].last

    def is_reversable(self) -> bool:
        return True

    def reverse(self) -> None:
        new_backward = self.forward
        self.forward = self.backward
        self.backward = new_backward
        self.forward.reverse()
        for s in self.forward:
            s.reverse()
        self.backward.reverse()
        for s in self.backward:
            s.reverse()
        self.length = sum(s.length for s in self.forward)

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
class RouteSegment:
    """ A complete route or route leg with splits, alternatives,
        approaches and gaps.
    """
    length: int
    """ Length of the main route excluding gaps between segments. """
    main: 'list[AnySegment]'
    """ Linear sequence of segments constituting the main route.
    """
    appendices: 'list[WaySegment | RouteSegment]'
    """ List of excursions and approaches for the route. The role
        must contain the type of approach.
    """
    role: str | None = None
    """ Optional role of the way within the relation. """
    start: float | None = None
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



AnySegment = WaySegment | RouteSegment | SplitSegment
