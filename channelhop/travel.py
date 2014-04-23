# coding: utf-8 

class Waypoint(object):
	"""A waypoint is a node in an itinerary.
	
	Waypoints have location and an optional date/time. Where the
	latter is not specified, it makes the waypoint suitable for
	merging with another at the same location and specified date/time.

		location : places.Location instance
		datetime : datetime.datetime instance (optional)
	
	"""
	def __init__(self, location, datetime=None):
		self.location = location
		self.datetime = datetime

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

class Segment(object):
	"""An itinerary segment.

	A segment consists of two waypoints and a link.

		start, end : Waypoint instances
		link : Link instance

	"""
	def __init__(self, start, end, link):
		self.start = start
		self.end = end
		self.link = link
		# TODO: Add switch and methods for deriving WP date/time
