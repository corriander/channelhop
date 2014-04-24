# coding: utf-8 
from collections import defaultdict
from datetime import timedelta

class Waypoint(object):
	"""A waypoint is a node in an itinerary.
	
	Waypoints have location and an optional date/time. Where the
	latter is not specified, it makes the waypoint suitable for
	merging with another at the same location and specified date/time.

		location : places.Location instance
		datetime : datetime.datetime instance (optional)
	
	"""
	daymap = {1 : 'Mon', 2 : 'Tue', 3 : 'Wed', 4 : 'Thu', 5 : 'Fri',
			  6 : 'Sat', 7 : 'Sun'}

	monthmap = {1 : 'Jan', 2 : 'Feb', 3 : 'Mar', 4 : 'Apr', 5 : 'May',
				6 : 'Jun', 7 : 'Jul', 8 : 'Aug', 9 : 'Sep', 10: 'Oct',
				11: 'Nov', 12: 'Dec'}

	def __init__(self, location, datetime=None):
		self.location = location
		self.datetime = datetime

	def merge(self, other):
		"""Merge waypoint with another.
		
		Waypoints must be at the same location. If this waypoint has
		no datetime value, the other's is used.
		
		"""
		if self.location != other.location:
			raise ValueError("Waypoint locations different.")
		elif self.datetime is None:
			self.datetime = other.datetime
		elif other.datetime and self.datetime != other.datetime:
			raise ValueError("Waypoint datetimes differ.")

	def __str__(self):
		return '{}, {} ({})'.format(self.location.town,
							 	    self.location.country,
							 		self._format_dt())

	def _format_dt(self):
		# String-format datetime 
		dt = self.datetime
		if not dt:
			return ''
		else:
			string = '{} {:02d} {}, {:02d}{:02d}'
			weekday = self.daymap[dt.isoweekday()]
			month = self.monthmap[dt.month]
			return string.format(weekday, dt.day, month, dt.hour, 
								 dt.minute)

	def __eq__(self, other):
		if (self.location == other.location and
		    self.datetime == other.datetime):
			return True
		else:
			return False


class Link(object):
	"""A link is a transition between waypoints.

	Links have a duration, a cost and a note. Both duration and cost
	are required; the duration may be used to calculate undefined
	waypoint datetime attributes.

		duration : datetime.timedelta instance
		cost : financial cost of journey (fuel, fares, tolls, etc.)
		note : journey description for disambig./clarity

	"""
	def __init__(self, duration, cost, note=''):
		self.duration = duration
		self.cost = cost
		self.note = note

	def __str__(self):
		h, s = divmod(int(self.duration.total_seconds()), 3600)
		m, __ = divmod(s, 60)
		note = self.note
		if note:
			note = '. {}'.format(note)
		string =  '{}h{} \xc2\xa3{:.2f}{}'.format(h, 
											      m,
											      self.cost,
											      note)
		return string

	def __eq__(self, other):
		return self.__dict__ == other.__dict__

class Segment(object):
	"""An itinerary segment.

	A segment consists of two waypoints and a link.

		start, end : Waypoint instances
		link : Link instance

	"""
	def __init__(self, start, end, link):
		self._validate_input(start, end, link)
		self.start = start
		self.end = end
		self.link = link
		# TODO: Add switch and methods for deriving WP date/time

	@classmethod
	def from_CarData(cls, car_data):
		"""Create a segment from car data."""
		start = Waypoint(car_data.source, None)
		end = Waypoint(car_data.destination, None)
		link = Link(car_data.duration, car_data.cost, car_data.note)
		return cls(start, end, link)

	@classmethod
	def from_FerryData(cls, ferry_data):
		"""Create a segment from ferry data."""
		start = Waypoint(ferry_data.source, ferry_data.dep)
		end = Waypoint(ferry_data.destination, ferry_data.arr)
		duration = cls._calculate_border_duration(start, end)
		note = ferry_data.operator
		if ferry_data.note:
			note = '{}, {}'.format(note, ferry_data.note)
		link = Link(duration, ferry_data.cost, note)
		return cls(start, end, link)

	@staticmethod
	def _calculate_border_duration(start, end):
		# Crude timezone handling for border crossing.
		duration = end.datetime - start.datetime
		countries = start.location.country, end.location.country
		if countries == ('UK', 'FR'):
			duration -= timedelta(hours=1)
		elif countries == ('FR', 'UK'):
			duration += timedelta(hours=1)
		return duration

	@staticmethod
	def _validate_input(start, end, link):
		if all((start.datetime, end.datetime, link.duration)):

			switch = {
					('UK', 'FR') : start.datetime + timedelta(hours=1),
					('FR', 'UK') : start.datetime - timedelta(hours=1)
					}
			key = start.location.country, end.location.country
			start_eff = switch.get(key, start.datetime) 
			if link.duration != end.datetime - start_eff:
				raise ValueError("Over-constrained Segment.")

	def __str__(self):
		# shortcuts to attributes
		string =  '{} --> {} : {}'.format(self.start, 
										  self.end, 
										  self.link)
		return string.replace('() ', '')

	def __eq__(self, other):
		return self.__dict__ == other.__dict__


class SegmentMap(defaultdict):
	def __init__(self, list_car_data, list_ferry_data):
		defaultdict.__init__(self, list)
		for route in list_car_data:
			self[route[:2]].append(Segment.from_CarData(route))
		for route in list_ferry_data:
			self[route[:2]].append(Segment.from_FerryData(route))
