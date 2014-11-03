import unittest

import channelhop.vehicle as vehicle
from channelhop.vehicle import Car, FuelTank
from channelhop.quantities import units, Quantity

class TestFuelTank(unittest.TestCase):

	capacity_litres = 65
	tank = FuelTank(capacity_litres)
	vehicle.FUELPRICE = 100 * units.pence / units.litre

	def test_capacity(self):
		"""Check capacity is assigned correctly."""
		# Confirms the capacity is a quantity and in default units.

		self.assertEqual(self.capacity_litres * units.litre,
						 self.tank.capacity)

	def test_fill_cost(self):
		"""Check cost to fill up is estimated correctly."""
		# Confirms the attribute is a quantity and it's in default
		# units. Currency conversion is not easily testable.
		self.assertEqual(self.capacity_litres,
						 self.tank.fill_cost.magnitude)


class TestCar(unittest.TestCase):

	vehicle.FUELPRICE = 100 * units.pence / units.litre
	# Define a car with a 65 litre tank and 10 litres/100 km
	car = Car(fuel_tank_capacity=65, fuel_consumption=0.1)

	def test_fuel_consumption(self):
		"""The fuel consumption is fuel volume per unit distance."""
		self.assertEqual(0.1,
						 self.car.fuel_consumption.to('L/km').magnitude)

	def test_fuel_cost(self):
		"""Fuel cost is the cost per unit distance."""
		self.assertEqual(10, self.car.fuel_cost.to('p/km').magnitude)

	def test_mpg(self):
		"""mpg is a common representation of fuel efficiency."""
		self.assertAlmostEqual(23.52, self.car.mpg.magnitude,
							   places=2)

	def test_range(self):
		"""The range estimate is the distance for a full tank.

		This calculation depends on the fuel_consumption and
		fuel_tank.capacity attributes.
		"""
		self.assertEqual(650, self.car.range.to('km').magnitude)

	def test_unit_range(self):
		"""The unit range is the distance per unit cost."""
		self.assertEqual(10, self.car.unit_range.to('km/L').magnitude)


if __name__ == '__main__':
	unittest.main()
