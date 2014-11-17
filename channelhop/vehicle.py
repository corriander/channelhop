"""Module for vehicle representation."""
# TODO: Class (and supporting) for Car, providing fuel efficiency,
# etc.
from money import Cost
from quantities import units, Quantity

# Define mpg
units.define('mpg = miles per gallon')

# Constants
FUELPRICE = Quantity(127, 'p/L')

# Classes
class FuelTank(object):
	"""Model of a vehicle fuel tank.

	Fuel tanks have capacity and associated filling cost.
	"""
	def __init__(self, capacity):
		"""Arguments:

			capacity - numeric [litres]
		"""
		self._capacity = Quantity(capacity, 'L')

	@property
	def capacity(self):
		"""Capacity of the fuel tank."""
		return self._capacity

	@property
	def fill_cost(self):
		"""Estimated cost of a full tank."""
		return self._capacity * FUELPRICE.to('GBP/L')


class Car(object):
	"""Model of a car.

	Cars have fuel tanks of a specified capacity and fuel consumption.
	"""
	def __init__(self, fuel_tank_capacity, fuel_consumption):
		"""Arguments:

			fuel_tank_capacity - numeric [litres]
			fuel_consumption - numeric [litres/km]
		"""
		self._fuel_tank = FuelTank(fuel_tank_capacity)
		self._fuel_consumption = Quantity(fuel_consumption, 'L/km')

	@property
	def fuel_tank(self):
		"""FuelTank component."""
		return self._fuel_tank

	@property
	def fuel_consumption(self):
		"""Average fuel consumption."""
		return self._fuel_consumption

	@property
	def range(self):
		"""Estimated range with a full tank."""
		return self.fuel_tank.capacity / self.fuel_consumption

	@property
	def unit_range(self):
		"""Reciprocal of fuel consumption."""
		return 1 / self.fuel_consumption

	@property
	def unit_fuel_cost(self):
		"""Cost per unit distance."""
		return FUELPRICE / self.unit_range

	@property
	def mpg(self):
		"""Alias for unit_range in miles per gallon."""
		return self.unit_range.to('mpg')

	def estimate_fuel_cost(self, distance, units='miles'):
		"""Estimate fuel cost for a distance.

		Arguments
		---------

			distance : numerical value or Quantity instance
			units : string (optional, default: 'miles')

		If the distance is a Quantity instance, the units argument is
		ignored.
		"""
		if not isinstance(distance, Quantity):
			distance = Quantity(magnitude, units)

		desc = "Fuel ({})".format(distance)
		quantity = (self.unit_fuel_cost * distance)
		return Cost(desc, quantity.magnitude, quantity.units)
