# coding: utf-8 
import copy
from collections import defaultdict, namedtuple
from datetime import timedelta
from places import LocationMap

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


class Itinerary(list):
	"""A sequence of joined segments (merged end/start waypoints)."""
	def __init__(self, segments):
		"""Instantiated with a list of Segment instances."""
		list.__init__(self)
		self._collapse(segments)
		self._propagate_schedule()

	def _collapse(self, segments):
		# Collapse segments. Joins segments together sensibly. Init
		# helper method.
		self.append(segments[0].start) # initial waypoint
		for i in xrange(len(segments)):
			seg = segments[i]
			self.append(seg.link)
			try:
				next_ = segments[i+1]
				seg.end.merge(next_.start)
			except IndexError:
				pass
			self.append(seg.end)

	def _propagate_schedule(self):
		# Propagates date/time information through the itinerary.
		wps, links = self[::2], self[1::2]
		for i in xrange(len(links)):
			wp_a, wp_b = wps[i], wps[i+1]
			link = links[i]
			if wp_a.datetime and wp_b.datetime is None:
				wp_b.datetime = wp_a.datetime + link.duration

		wps, links = self[::-2], self[-2::-2]
		for i in xrange(len(links)):
			wp_a, wp_b = wps[i], wps[i+1]
			link = links[i]
			if wp_a.datetime and wp_b.datetime is None:
				wp_b.datetime = wp_a.datetime - link.duration

	@property
	def cost(self):
		"""Total cost for the route."""
		total = []
		for element in self:
			# This is very lazy...
			try:
				total.append(element.cost)
			except AttributeError:
				pass
		return sum(total)

	@property
	def arrival(self):
		"""Destination arrival date/time."""
		return self[-1].datetime 
	
	def __str__(self):
		string = []
		for i, element in enumerate(self):
			string.append('{}.\t{}'.format(i, element))
		return '\n'.join(string)


class Route(list):
	"""A route a set of itineraries corresponding to a path.
	
	The path is a list of Location instances. The itineraries are
	calculated permutations of location-pair Segments along the path
	(provided by a SegmentMap instance).
	
	"""
	# TODO: Tighten this up. Initially the recursive permutation
	# algorithm was intended to generate itineraries directly rather
	# than sequences of segments. The method ran into early issues
	# with prematurely mutated waypoints (causing problems in future
	# itinerary-creation using the same references). This is the
	# result of a "workaround" which turned out to be a little naive
	# as, although it exposed the real cause of the issue (mutable
	# waypoints, not the recursion per se), it has the same problems
	# albeit with a more complex dataflow. _generate_permutations()
	# could just become _generate_itineraries, and rather than
	# instantiating itineraries with a sequence of segments, they
	# could be appended in-place. As long as the itinerary creates
	# deepcopies of waypoints when calculating datetimes, there
	# shouldn't be an issue with mutability.

	def __init__(self, path, segmap):
		self.path = path
		self.segmap = segmap
		list.__init__(self)
		self._generate_itineraries()

	def _generate_itineraries(self):
		# Create itineraries from Segment-sequence permutations.
		permutations = self._generate_permutations(self.path)
		for segment_sequence in permutations:
			self.append(Itinerary(copy.deepcopy(segment_sequence)))

	def _generate_permutations(self, path, history=[]):
		# Generate permutations of segments along the path.
		if len(path) == 1: return [history] # end of path
		histories = []
		for segment in self.segmap[tuple(path[:2])]:
			new_history = history + [segment]
			futures = self._generate_permutations(path[1:], 
												  new_history)
			for future in futures:
				histories.append(future)
		return histories

	@property
	def cost(self):
		"""Min/max cost for route."""
		cost_list = [itin.cost for itin in self]
		return (min(cost_list), max(cost_list))


OptionBase = namedtuple('Option', 'out, rtn, cost, arrival_time')

class Option(OptionBase):
	__slots__ = ()
	def __str__(self):
		string = ['OPTION\n---------------------------------------\n']
		string.append('COST: \xc2\xa3{:.2f}'.format(self.cost))
		string.append('ARRIVAL: {}'.format(self.arrival_time))
		string.append(str(self.out))
		string.append('')
		string.append(str(self.rtn))
		string.append('')
		return '\n'.join(string)

class Trip(object):
	"""A <-> B, potentially aysmmetrical trip via channel ferries.
	
	This provides a range of potential combinations with metadata for
	decision-making assistance purposes.
	
	"""
	def __init__(self, origin, destination, ferries, car_routes):
		self.segmap = SegmentMap(car_routes, ferries)
		self.lmap = LocationMap(origin, destination)
		itineraries = self._itineraries()
		self.out = itineraries['OUT']
		self.rtn = itineraries['RTN']
		self.origin = self.lmap.origin
		self.destination = self.lmap.destination
		self.options = self._generate_options() 

	def _itineraries(self):
		# generate itineraries for all routes
		d = {}
		for direction in ('OUT', 'RTN'):
			route_list = [Route(path, self.segmap)
						  for path in self.lmap.paths[direction]]
			route_list = filter(None, route_list)
			d[direction] = [itinerary
							for route in route_list
							for itinerary in route]
		return d

	def _generate_options(self):
		return [Option(itinerary_1, 
					   itinerary_2, 
					   (itinerary_1.cost + itinerary_2.cost)/4,
					   itinerary_1[-1].datetime)
				for itinerary_1 in self.out
				for itinerary_2 in self.rtn]
