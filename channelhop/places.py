from collections import namedtuple

_Location = namedtuple('Location', 'town, country')
class Location(_Location):
	"""A simple representation of a place/location."""
	__slots__ = ()
	def __repr__(self):
		return 'Location({!r}, {!r})'.format(self.town, self.country)
