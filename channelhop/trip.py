from channelhop.money import Cost
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
		self._travel_components = []

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
		total = sum(component.cost
				    for component in self._travel_components)

		return Cost('Total fuel cost (estimated)', total.magnitude,
					'GBP')

	@property
	def fuel_cost(self):
		"""Actual fuel cost."""
		return self._fuel_cost

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

	def rm_person(self, person):
		"""Remove a person from the trip."""
		self._people.remove(person)

	def add_wp(self, location):
		"""Add a waypoint to the trip.

		A waypoint is associated with the people currently present on
		the trip. People must be added before adding a waypoint if
		they are to be associated (or removed if not).

		Arguments
		---------

			location : string (e.g. 'London' or '38 Some Place')
		"""
		if not self._people:
			raise TripDefError("People must be present on the trip.")

		wp = Waypoint(location)
		wp.people = set(self._people)
		self._items.append(wp)

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

		# Add cost to last waypoint
		last_wp.cost = Cost(description, amount, currency)

		# Assign cost to people
		last_wp.cost.split_assign(last_wp.people)

	def travel(self, distance, units='miles'):
		"""Travel a specified distance from the previous Waypoint.

		Travel is represented by a Link instance.

		Arguments
		---------

			distance : no. of kilometres travelled.
			units : optional, default: 'miles'

		Constraints
		-----------

		  - travel must follow a waypoint.
		  - travel is associated with the same people as the previous
			waypoint; people can't magically appear or disappear
			en-route.
		  - travel is associated with an estimated fuel cost based on
			the vehicle properties.
		"""
		# TODO: intelligent (country-based) default units
		# FIXME: Allow tolls/costs

		# Check the last element is a Waypoint.
		last_wp = self.last_wp
		if len(self._items) == 0 or last_wp is not self._items[-1]:
			raise TripDefError("Travel must follow a waypoint.")

		# Make distance a Quantity, construct Cost instance.
		distance = Quantity(distance, units)
		cost = self.vehicle.estimate_fuel_cost(distance).to('GBP')

		# Define the link and add it to the trip
		ln = Link(duration=None, cost=cost)
		self._items.append(ln)
		self._travel_components.append(ln)

		# Monkey-patch some properties on to the link.
		# FIXME: Modify Link class to accept distance natively.
		ln.distance = distance
		ln.people = last_wp.people

	def fuel_breakdown(self):
		"""Itemised breakdown of fuel costs over the journey.

		Returns a list of Cost items. If the trip.fuel_cost is set,
		this value is used to calculated (constant) proportional costs
		for each travel component. Otherwise, the estimated costs for
		each travel component are returned
		"""
		# TODO: Indicate type of result somehow (maybe in cost desc.)
		if hasattr(self, '_fuel_cost'):
			return self._fuel_breakdown_actual()
		else:
			return self._fuel_breakdown_estimate()

	def pretty_fuel_breakdown(self):
		"""Human-readable fuel breakdown, returns a string."""
		return '\n'.join(map(str, self.fuel_breakdown()))

	def assign_fuel_costs(self, real_amount=0, currency='GBP'):
		"""Assign fuel costs to trip participants.

		This method adds equally divided, proportionally determined
		fuel costs for each trip component to the relevant
		participants via the `fuel_breakdown` method.

		Arguments
		---------

			real_amount : numeric value representing actual fuel value
						  consumed.
			currency : units of the real_amount
		"""
		if real_amount > 0:
			self._fuel_cost = Cost('Total fuel cost',
								   real_amount,
								   currency)

		for cost, component in zip(self.fuel_breakdown(),
								   self._travel_components):
			cost.split_assign(component.people)

	# ----------------------------------------------------------------
	# Internal methods
	# ----------------------------------------------------------------
	def _fuel_breakdown_estimate(self):
		# Return list of Cost objects derived from estimated fuel cost
		return [obj.cost
				for obj in self._items
				if isinstance(obj, Link)]

	def _fuel_breakdown_actual(self):
		# Return list of Cost objects derived from actual fuel cost
		# KISS: it's arguably better not to assume constant fuel
		# consumption but it's a rather pervasive assumption here.
		# Take a constant ratio and apply it to the breakdown estimate
		# NOTE: This is a workaround because Pint's handling of
		# dimensionless quantities is, er, bad. Very bad. It just
		# takes a case about which way the ratio comes out rather than
		# it being based on the expression. Debugging this took a
		# while.
		ratio = (self.fuel_cost_estimate.to('GBP').magnitude /
			     self.fuel_cost.to('GBP').magnitude)

		breakdown = []
		for cost in self._fuel_breakdown_estimate():
			adjusted_cost = (cost / ratio).to('GBP') # Quantity inst.
			breakdown.append(
				Cost(cost.description, adjusted_cost.magnitude, 'GBP')
			)

		return breakdown
