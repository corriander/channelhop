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

	The following attributes are available after instantiation:

		ports : dict containing ports
		origin : argument
		destination : argument
		endpoints : set(origin, destination)
		locations : set of ports and endpoints
		routes : dict containing list of routes (both out and rtn).

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
		self._find_routes()

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

	def _find_routes(self):
		# find all outward and return routes
		a, b = self.origin, self.destination
		d = {}
		d['OUT'] = filter(has_single_crossing, find_paths(self, a, b))
		d['RTN'] = filter(has_single_crossing, find_paths(self, b, a))
		self.routes = d


def find_paths(lmap, start, end, path=[]):
	"""Find all paths in a location map between two locations."""
	path = path + [start] # Add the start node to the current path
	if start == end:
		return [path]
	if not lmap.has_key(start):
		# invalid start node
		raise ValueError('Start location not in lmap')
	
	paths = [] # container for all paths
	for neighbour in filter(lambda l: l not in path, lmap[start]):
		# for each UNVISITED neighbour, find paths and store
		newpaths = find_paths(lmap, neighbour, end, path)
		for newpath in newpaths:
			paths.append(newpath)
	return paths

def has_single_crossing(path):
	"""Evaluate whether path has a single crossing."""
	result, crossings, last_node = True, 0, path[0]
	for node in path[1:]:
		if node.country is not last_node.country:
			crossings += 1
			last_node = node
	if crossings > 1: result = False
	return result

