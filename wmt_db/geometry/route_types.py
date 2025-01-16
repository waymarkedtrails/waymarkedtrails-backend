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
from shapely.geometry import shape

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
    ROUTE_TYPE = 'base'

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
        writer = JsonWriter().start_object()\
                .keyval('route_type', self.ROUTE_TYPE)\
                .keyval('start', self.start)\
                .keyval('id', self.osm_id)\
                .keyval('tags', self.tags)\
                .keyval('length', self.length)\
                .keyval('direction', self.direction)\
                .keyval('role', self.role or '')\
                .key('geometry').start_object()\
                    .keyval('type', 'LineString')\
                    .key('coordinates').start_array()

        for c in self.geom.coords:
            writer.start_array()\
                .float(c[0], 2).next()\
                .float(c[1], 2).end_array()\
                .next()

        writer.end_array().next().end_object().next()\
                .end_object()

        return writer()

    @staticmethod
    def from_json_dict(obj) -> 'BaseWay':
        return BaseWay(osm_id=obj['id'], tags=TagStore(obj['tags']),
                       length=obj['length'], direction=obj['direction'],
                       geom=shape(obj['geometry']),
                       role=obj['role'], start=obj['start'])


@dataclass
class WaySegment:
    """ A segment containing only BaseWays that create a linear section
        of way. The BaseWays must have compatible attributes in terms of
        direction and role.
    """
    ROUTE_TYPE = 'linear'
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
        return JsonWriter().start_object()\
                .keyval('route_type', self.ROUTE_TYPE)\
                .keyval('start', self.start)\
                .keyval('length', self.length)\
                .key('ways').object_array(self.ways).next()\
                .end_object()()

    @staticmethod
    def from_json_dict(obj) -> 'WaySegment':
        return WaySegment(length=obj['length'], start=obj['start'],
                          ways=obj['ways'])



@dataclass
class SplitSegment:
    """ A segment with different routes for forward and backward.
    """
    ROUTE_TYPE = 'split'

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

    @property
    def direction(self) -> int:
        return 0

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
        return JsonWriter().start_object()\
                .keyval('route_type', self.ROUTE_TYPE)\
                .keyval('start', self.start)\
                .keyval('length', self.length)\
                .key('first').start_array()\
                    .float(self.first[0], 2).next()\
                    .float(self.first[1], 2).end_array().next()\
                .key('last').start_array()\
                    .float(self.last[0], 2).next()\
                    .float(self.last[1], 2).end_array().next()\
                .key('forward').object_array(self.forward).next()\
                .key('backward').object_array(self.backward).next()\
                .end_object()()

    @staticmethod
    def from_json_dict(obj) -> 'SplitSegment':
        return SplitSegment(length=obj['length'], start=obj['start'],
                            first=tuple(obj['first']), last=tuple(obj['last']),
                            forward=obj['forward'], backward=obj['backward'])


@dataclass
class AppendixSegment:
    """ A linear section that does not belong to the main route. May contain gaps.
    """
    ROUTE_TYPE = 'appendix'

    length: int
    """ Length of the main route excluding gaps between segments. """
    main: 'list[WaySegment | RouteSegment]'
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

    def adjust_start_point(self, start: int) -> int:
        """ Set own start point to the given value and recursively
            adjust the start points of all child segments.

            Returns the start point for the next segment.
        """
        return _adjust_start_segment_list(start, self.first, self.main)

    def to_json(self) -> str:
        return JsonWriter().start_object()\
                .keyval('route_type', self.ROUTE_TYPE)\
                .keyval('role', self.role)\
                .keyval_not_none('start', self.start)\
                .keyval_not_none('end', self.end)\
                .keyval('length', self.length)\
                .key('main').object_array(self.main).next()\
                .end_object()()

    @staticmethod
    def from_json_dict(obj) -> 'AppendixSegment':
        return AppendixSegment(start=obj.get('start'), end=obj.get('end'),
                               length=obj['length'], main=obj['main'])


@dataclass
class RouteSegment:
    """ A complete route or route leg with splits, alternatives,
        approaches and gaps.
    """
    ROUTE_TYPE = 'route'

    length: int
    """ Length of the main route excluding gaps between segments. """
    main: 'list[WaySegment | RouteSegment | SplitSegment]'
    """ Linear sequence of segments constituting the main route.
    """
    appendices: 'list[AppendixSegment]'
    """ List of excursions, approaches and alternatives for the route. The role
        must contain the type of approach.
    """
    direction: int = 0
    """ Direction of the route within a larger route.
    """
    role: str | None = None
    """ Optional role of the way within the relation. """
    start: int | None = None
    """ Distance from beginning of route.
        (Either in meter or in number of members in the relation.)
    """
    id: int | None = None
    """ OSM ID of the relation holding the route.
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
        self.direction = -self.direction
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
                if s.start is not None:
                    s.adjust_start_point(s.start + rel_adjustment)

        self.start = start
        return end

    def to_json(self) -> str:
        return JsonWriter().start_object()\
                .keyval('route_type', self.ROUTE_TYPE)\
                .keyval('length', self.length)\
                .keyval('start', self.start)\
                .keyval_not_none('role', self.role)\
                .keyval_not_none('id', self.id)\
                .key('main').object_array(self.main).next()\
                .key('appendices').object_array(self.appendices).next()\
                .end_object()()

    @staticmethod
    def from_json_dict(obj) -> 'RouteSegment':
        return RouteSegment(start=obj['start'], length=obj['length'],
                            role=obj.get('role'), id=obj.get('id'), main=obj['main'],
                            appendices=obj['appendices'])


BaseSegment = WaySegment | RouteSegment
AnySegment = WaySegment | RouteSegment | SplitSegment

ROUTE_TYPE_TO_CLASS = {c.ROUTE_TYPE: c for c in (BaseWay, WaySegment, SplitSegment,
                                                 AppendixSegment, RouteSegment)}

def json_decoder_hook(obj):
    """ object_hook for `json.load()` which creates route objects.
    """
    oclass = ROUTE_TYPE_TO_CLASS.get(obj.get('route_type'))
    if oclass is not None:
        return oclass.from_json_dict(obj)
    return obj
