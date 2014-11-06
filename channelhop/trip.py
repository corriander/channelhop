# TODO: It is really probably a better idea to abstract the costing
# from the trip definition rather than tying costs to particular parts
# of the trips. Instead, have them originate from parts of the trip
# but get dumped into a balance sheet type thing where they get
# associated with people either automagically based on who's on the
# journey, or explicitly based on some kind of argument.
from channelhop.money import Cost, Expense
from channelhop.travel import Waypoint, Link
from channelhop.quantities import Quantity


class TripDefError(Exception): pass

class Person(object):
	"""A trip participant.

	People:

	  - are present for some or all of the trip.
	  - are responsible for a share of costs incurred.
	  - may incur expenses (e.g. paying up front for fuel).
	  - start off with no costs/expenses assigned.
	"""
	def __init__(self, name):
		"""Instantiate a person with a unique name."""
		self.name = name
		self._items = set()	# container for cost-like items.

	def add_expense(self, *args, **kwargs):
		("""Associate a new Expense instance with a person.""" +
		 '\n\n' + Expense.__init__.__doc__)
		self._items.add(Expense(self, *args, **kwargs))

	def add_cost(self, *args, **kwargs):
		("""Associate a new Cost instance with a person.""" +
		 '\n\n' + Cost.__init__.__doc__)
		self._items.add(Cost(*args, **kwargs))

	@property
	def balance(self):
		"""Balance of costs and expenses.

		+ve value represents an IOU.
		"""
		return sum(x._quantity for x in self._items).to('GBP')

	def bill(self):
		"""Human-readable itemised bill."""
		strings = [self.name] + map(str, self._items)
		strings.append('	BALANCE: {}'.format(self.balance))
		return '\n'.join(strings)


class Trip(object):
	"""A trip involving multiple participants and a car.

	A trip is created from a series of (ordered) events.

	Example
	-------

	See tests/test_trip.py for a usage example.
	"""

	def __init__(self, description, vehicle):
		self.description = description
		self.vehicle = vehicle
		self._items = []
		self._people = set()

	def add_wp(self, *args, **kwargs):
		wp = Waypoint(*args, **kwargs)
		wp.people = set(self._people)
		self._items.append(wp)

	# Define the docstring
	add_wp.__doc__ = '\n'.join((
		'Add a waypoint to the trip.\n',
		Waypoint.__doc__,
		('A Waypoint is associated with the people currently present '
		 'on the trip. People must be added before adding a Waypoint '
		 'if they are to be associated (or removed before if not).')
	))

	def travel(self, distance, units='miles', duration=None):
		"""Travel a specified distance from the previous Waypoint.

		Travel is represented by a Link instance.

		Arguments

			distance : no. of kilometres travelled.
			units : optional, default: 'miles'

		Constraints

		  - travel must follow a waypoint.
		  - travel is associated with the same people as the previous
			waypoint; people can't magically appear or disappear
			en-route.
		  - travel is associated with an estimated fuel cost based on
			the vehicle properties.
		"""
		# TODO: intelligent (country-based) default units
		# FIXME: Allow tolls/costs

		# Fetch the last element as long as it's a waypoint.
		last_element = self._get_last_waypoint()

		# Change distance to a Quantity instance
		distance = Quantity(distance, units)

		# Define the link and add it to the trip
		ln = Link(duration,
				  Cost('Fuel', self._estimate_fuel_cost(distance)))
		self._items.append(ln)

		# Monkey-patch some properties on to the link.
		# FIXME: Modify Link class to accept distance natively.
		ln.distance = distance
		ln.people = last_element.people

	# FIXME: Put this in the vehicle/Car class
	def _estimate_fuel_cost(self, distance):
		# Estimate fuel cost for a distance (type: [length] quantity)
		return self.vehicle.fuel_cost * distance

	@staticmethod
	def _assign_cost(item, name):
		# Assign equal share of cost to all people present.
		n = len(item.people)
		for person in item.people:
			person.add_cost(name + ' / {:d} people'.format(n),
						    item.cost._quantity / n)

	def assign_fuel_costs(self, real_cost=0):
		"""Assign fuel costs to trip members proportionally.

		If a real cost is provided, the *proportions* of the estimated
		fuel costs are used, i.e. if you know you spent 45 on fuel,
		and the estimate is in fact 35, the 45 is split up based on
		the estimates for each bit of the journey.
		"""
		if real_cost > 0:
			raise NotImplementedError

		for item in self._items:
			if isinstance(item, Link):
				self._assign_cost(item, 'Fuel')

	def add_cost(self, *args, **kwargs):
		"""Assign a cost to the last Waypoint added."""
		last_element = self._get_last_waypoint()
		last_element.cost = Cost(*args, **kwargs)
		self._assign_cost(last_element, last_element.cost.description)

	# FIXME: This needs a re-think.
	def _get_last_waypoint(self):
		# Check the last trip element is a waypoint; if so, return it.

		try:
			last_element = self._items[-1]
		except IndexError:
			raise TripDefError("No Waypoints added.")

		if not isinstance(last_element, Waypoint):
			# FIXME: Real exception.
			raise TripDefError("Element prior to Link must be a Waypoint.")

		return last_element

	@property
	def last_wp(self):
		"""Fetch the last waypoint defined."""
		for item in reversed(self._items):
			if isinstance(item, Waypoint):
				return item

	def add_person(self, person):
		"""Add a person to the trip."""
		self._people.add(person)

	def remove_person(self, person):
		"""Remove a person from the trip."""
		self._people.remove(person)
