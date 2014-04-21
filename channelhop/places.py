from collections import namedtuple
from collections import defaultdict

_Location = namedtuple('Location', 'town, country')
class Location(_Location):
	"""A simple representation of a place/location."""
	__slots__ = ()
	def __repr__(self):
		return 'Location({!r}, {!r})'.format(self.town, self.country)


FERRY_ROUTES = [
		(Location('Portsmouth', 'UK'), Location('Le Havre', 'FR')),
		(Location('Portsmouth', 'UK'), Location('St. Malo', 'FR')),
		(Location('Portsmouth', 'UK'), Location('Cherbourg', 'FR')),
		(Location('Portsmouth', 'UK'), Location('Caen', 'FR')),
		(Location('Poole', 'UK'),      Location('Cherbourg', 'FR')),
		(Location('Newhaven', 'UK'),   Location('Dieppe', 'FR'))
		]

class LocationMap(defaultdict):
	"""Represent a simple route network.

	This is a network map from a domestic origin, A, and international
	destination, B represented as a simple undirected graph.

		>>> lmap = LocationMap('MyHouse', 'HolidayDest')

	"""

	ports = {}
	ports['UK'] = set(route[0] for route in FERRY_ROUTES)
	ports['FR'] = set(route[1] for route in FERRY_ROUTES)
	ports['ALL'] = ports['UK'].union(ports['FR'])

	def __init__(self, origin, destination):
		defaultdict.__init__(self, set)
		self.origin = Location(origin, 'UK')
		self.destination = Location(destination, 'FR')
		self.endpoints = set([self.origin, self.destination])
		self.locations = self.ports['ALL'].union(self.endpoints)
		self._connect_ports()
		self._connect_endpoints()

	def _connect_ports(self):
		# evaluate neighbours based on ferry routes
		for route in FERRY_ROUTES:
			for diroute in (route, route[::-1]):
				port, port2 = diroute
				if port.country is self.origin.country:
					self[port].add(self.origin)
				else:
					self[port].add(self.destination)
				self[port].add(port2)    # add paired port

	def _connect_endpoints(self):
		# evaluate neighbours of origin and destination
		for location in self.endpoints:
			self[location].update(self.ports[location.country])
