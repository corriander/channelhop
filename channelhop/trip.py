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

	# ----------------------------------------------------------------
	# Properties
	# ----------------------------------------------------------------
	@property
	def distance(self):
		"""Total trip distance."""
		return sum(item.distance
				   for item in self._items
				   if isinstance(item, Link))

	@property
	def fuel_cost_estimate(self):
		"""Estimated overall fuel cost."""
		return sum(item.cost._quantity
				   for item in self._items
				   if isinstance(item, Link))

	@property
	def fuel_cost(self):
		"""Actual fuel cost."""
		return self._fuel_cost
	@fuel_cost.setter
	def fuel_cost(self, value):
		if not isinstance(value, Quantity):
			value = Quantity(value, 'GBP')
		self._fuel_cost = value

	@property
	def last_wp(self):
		"""Fetch the last waypoint defined."""
		for item in reversed(self._items):
			if isinstance(item, Waypoint):
				return item

	# ----------------------------------------------------------------
	# API methods
	# ----------------------------------------------------------------
	def add_person(self, person):
		"""Add a person to the trip."""
		self._people.add(person)

	def remove_person(self, person):
		"""Remove a person from the trip."""
		self._people.remove(person)

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

	def add_cost(self, description, amount, currency='GBP'):
		"""Assign a cost to the last waypoint.

		Costs are represented as positive values; negative values will
		be converted.

		Arguments
		---------

			description : descriptive string
			amount : +ve numerical value in specified currency
			currency : 3-char string (optional, default: 'GBP')
		"""
		last_wp = self.last_wp
		amount = abs(amount)
		n_people = len(last_wp.people)
		amount_pp = amount / n_people

		# Add cost to last waypoint
		last_wp.cost = Cost(description, amount, currency)

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
		n_people = len(last_element.people)

		# Make distance a Quantity, construct Cost instance.
		distance = Quantity(distance, units)
		description = 'Fuel; {}, {} people'.format(distance, n_people)
		cost = Cost(description, self._estimate_fuel_cost(distance))

		# Define the link and add it to the trip
		ln = Link(duration, cost)
		self._items.append(ln)

		# Monkey-patch some properties on to the link.
		# FIXME: Modify Link class to accept distance natively.
		ln.distance = distance
		ln.people = last_element.people

	def fuel_breakdown(self):
		"""Itemised breakdown of fuel costs over the journey.

		Returns a list of Cost items.
		"""
		breakdown = []
		replace = False

		try:
			overall_fuel_cost = self.fuel_cost
			replace = True
		except AttributeError:
			# fuel_cost undefined; simply return list of Link costs.
			pass

		for item in self._items:
			# only Link/travel items have fuel costs
			if not isinstance(item, Link):
				continue

			if replace:
				# save the estimate
				item.fuel_cost_estimate = item.cost
				# get ratio from Link and Trip fuel cost estimates
				ratio = (item.fuel_cost_estimate._quantity /
						 self.fuel_cost_estimate)

				item.cost = ratio * overall_fuel_cost

			breakdown.append(item.cost)

		return breakdown

	def pretty_fuel_breakdown(self):
		"""Human-readable fuel breakdown, returns a string."""
		return '\n'.join(map(str, self.fuel_breakdown()))

	def assign_fuel_costs(self, real_cost=0, currency='GBP'):
		"""Assign fuel costs to trip members proportionally.

		If a real cost is provided, the *proportions* of the estimated
		fuel costs are used, i.e. if you know you spent 45 on fuel,
		and the estimate is in fact 35, the 45 is split up based on
		the estimates for each bit of the journey.
		"""
		if real_cost > 0:
			fuel_cost = self.fuel_cost = Quantity(real_cost, currency)

		for item in self._items:
			if isinstance(item, Link):
				self._assign_cost(item, 'Fuel')

	# ----------------------------------------------------------------
	# Internal methods
	# ----------------------------------------------------------------
	# FIXME: Put this in the vehicle/Car class
	def _estimate_fuel_cost(self, distance):
		# Estimate fuel cost for a distance (type: [length] quantity)
		return self.vehicle.fuel_cost * distance

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



