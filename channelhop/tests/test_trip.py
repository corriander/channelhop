import unittest
from channelhop.trip import Person, Trip, TripDefError
from channelhop.vehicle import Car, FUELPRICE
from channelhop.money import Expense, Cost
from channelhop.quantities import units, Quantity


class TestPerson(unittest.TestCase):
	"""Exercises the Person class.

	People primarily exist here to be assigned a bill, representing
	their contributions and owed monies.
	"""
	# Init is so simple it's not worth testing. Go straight to
	# creating a test person.
	def setUp(self):
		self.person = Person('Bob')

	# Test methods
	def test_add_expense(self):
		"""Check an expense is assigned correctly.

		Expenses are represented as outgoings from the person, so they
		appear as negative values.
		"""
		self.person.add_expense('test expense', 10., 'GBP')
		# Check we have one expense/cost
		self.assertEqual(len(self.person._items), 1)
		# Check it's an expense
		item = self.person._items.pop()
		self.assertIsInstance(item, Expense)
		# Check the expense is associated with the person.
		self.assertIs(item.person, self.person)
		# Check the expense has a negative value.
		self.assertLess(item._quantity.magnitude, 0)

	def test_add_cost(self):
		"""Check a cost is assigned to the person correctly.

		Costs have a positive value as they represent IOUs (from that
		person) here.
		"""
		self.person.add_cost('test cost', 7., 'EUR')
		# Check we have one expense/cost
		self.assertEqual(len(self.person._items), 1)
		# Check it's a Cost
		item = self.person._items.pop()
		self.assertIsInstance(item, Cost)
		# Check it's positive value
		self.assertGreater(item._quantity.magnitude, 0)

	def test_balance(self):
		"""Calculate the balance of costs/expenses in 2	currencies.

		If this test passes, currency is being dealt with correctly.
		"""
		expense_1 = (10., 'EUR')
		expense_2 = (15., 'GBP')
		cost_1 = (10., 'GBP')
		cost_2 = (12., 'EUR')

		expected_balance = (
			Quantity(*cost_1) +
			Quantity(*cost_2) -
			Quantity(*expense_1) -
			Quantity(*expense_2)
		).to('GBP')

		self.person.add_expense('expense1', *expense_1)
		self.person.add_expense('expense2', *expense_2)
		self.person.add_cost('cost1', *cost_1)
		self.person.add_cost('cost2', *cost_2)

		# Check the balance is a Quantity (not a cost or expense)
		self.assertIsInstance(self.person.balance, Quantity)

		# Check it's as expected, calculated separately here.
		msg = "{} != {} (expected; EUR = {} GBP)".format(
				self.person.balance.to('GBP'),
				expected_balance,
				Quantity(1, 'EUR').to('GBP').magnitude
		)
		self.assertAlmostEqual(self.person.balance.to('GBP').magnitude,
							   expected_balance.magnitude,
							   places=2,
							   msg=msg)

	# bill is just a list of expenses, the import bit is the balance.


class TestTrip(unittest.TestCase):
	"""Exercise Trip class."""
	def setUp(self):
		"""Define a trip in a car with a 60 L tank and 0.1 L/km."""
		self.trip = Trip('test trip', Car(60, 0.1))
		self.trip.add_person(Person('A'))

	def test_add_wp_no_people(self):
		"""Adding a waypoint before adding people shouldn't work."""
		trip = Trip('test', Car(1,1))
		self.assertRaises(TripDefError, trip.add_wp('A'))

	def test_add_wp(self):
		"""Adding a waypoint with at least one person should work.

		The waypoint should be associated with all people on the trip.
		"""
		self.trip.add_wp('A')
		self.assertEqual(self.trip._people,
						 self.trip._items[-1].people)

	def test_last_wp_single_item(self):
		"""Check the last_wp attribute returns the only waypoint."""
		self.trip.add_wp('A')
		self.assertEqual(self.trip.last_wp, self.trip._items[0])

	def test_link_no_wp(self):
		"""A link/travel shouldn't be addable without a waypoint."""
		self.assertRaises(TripDefError, self.trip.travel(50, 'km'))

	def test_add_wp_and_link(self):
		"""Adding a waypoint and a link should work.

		The waypoint and the link should both be associated with all
		people on the trip.
		"""
		self.trip.add_wp('A')
		self.trip.travel(50, 'km')

		# Check that the trip elements so far are as expected.
		self.assertEqual(len(self.trip._items), 2)
		self.assertEqual(self.trip._items[0].location, 'A')
		self.assertEqual(self.trip._items[1].distance.magnitude, 50)

		# Check the travel segment inherited the people from the last
		# waypoint.
		self.assertIs(self.trip._items[1].people,
					  self.trip._items[0].people)

	def test_last_wp_where_last_item_is_link(self):
		"""For a waypoint + link, last_wp should return the wp."""
		self.trip.add_wp('A')
		self.trip.travel(50, 'km')
		self.assertEqual(self.trip.last_wp.location, 'A')

	def test_add_cost(self):
		"""Adding a cost to the last waypoint should work."""
		self.trip.add_wp('A')
		self.trip.add_cost('Parking', 5., 'GBP')

		self.assertEqual(self.trip.last_wp.cost._quantity,
						 Quantity(5., 'GBP'))

	def test__assign_cost_single_wp_single_person(self):
		"""Distributes cost of a Trip item to its people."""
		self.trip.add_wp('A')

		# Circumvent the add_cost method here as it calls _assign_cost
		self.trip.last_wp.cost = Cost('Parking', 5., 'GBP')
		self.trip._assign_cost(self.trip.last_wp, 'Parking')

		self.assertEqual(self.trip.last_wp.people.pop().balance,
						 Quantity(5., 'GBP'))

	def test__assign_cost_single_wp_two_people(self):
		people = list(self.trip._people)[0], Person('B')
		self.trip.add_person(people[1])
		self.trip.add_wp('A')
		self.trip.last_wp.cost = Cost('Parking', 5., 'GBP')
		self.trip._assign_cost(self.trip.last_wp, 'Parking')

		self.assertEqual(people[0].balance, Quantity(2.50, 'GBP'))
		self.assertEqual(people[1].balance, Quantity(2.50, 'GBP'))

	def test_add_person_mid_route(self):
		"""Check a person is successfully added.

		Primarily, this is to ensure the person doesn't incur costs
		from trip elements prior to their joining.
		"""
		pA = list(self.trip._people)[0]
		self.trip.add_wp('A')
		self.trip.add_cost('ParkingA', 5)
		self.trip.travel(50, 'km')
		p = Person('B')
		self.trip.add_person(p)
		self.trip.add_wp('B')
		self.trip.add_cost('ParkingB', 10)

		# Sanity checks to make sure they are actually present for the
		# right parts of the trip.
		self.assertNotIn(p, self.trip._items[0].people)
		self.assertNotIn(p, self.trip._items[1].people)
		self.assertIn(p, self.trip._items[2].people)

		# Persons A and B should both have costs associated with them
		# here. As B has been removed before the second waypoint, the
		# system assumes they don't incur this cost.
		self.assertEqual(p.balance, Quantity(5.0, 'GBP'))
		self.assertEqual(pA.balance, Quantity(10.0, 'GBP'))

	def test_remove_person_mid_route(self):
		"""Check a person is successfully removed.

		Primarily, this is to ensure the person doesn't incur costs
		from the elements following their removal.
		"""
		p = Person('B')
		self.trip.add_person(p)
		self.trip.add_wp('A')
		self.trip.add_cost('ParkingA', 5)
		self.trip.travel(50, 'km')
		self.trip.remove_person(p)
		self.trip.add_wp('B')
		self.trip.add_cost('ParkingB', 10)

		# Sanity checks to make sure they are actually present for the
		# right parts of the trip.
		self.assertIn(p, self.trip._items[0].people)
		self.assertIn(p, self.trip._items[1].people)
		self.assertNotIn(p, self.trip._items[2].people)

		# Persons A and B should both have costs associated with them
		# here. As B has been removed before the second waypoint, the
		# system assumes they don't incur this cost.
		self.assertEqual(p.balance, Quantity(2.50, 'GBP'))
		self.assertEqual(self.trip._people.pop().balance,
						 Quantity(12.50, 'GBP'))

	def test_assign_fuel_costs_single_person_and_link(self):
		"""Fuel costs assigned to a single person, single Link."""
		trip = self.trip

		p = list(trip._people)[0]

		# define the trip
		trip.add_wp('A')
		trip.travel(50, 'km')

		trip.assign_fuel_costs()

		expected = Quantity(50, 'km') * trip.vehicle.fuel_cost
		self.assertEqual(p.balance, expected)

	def test_assign_fuel_costs_single_link_and_two_people(self):
		"""Fuel costs assigned to two people over a single Link."""
		trip = self.trip

		people = list(trip._people)[0], Person('B')

		# define the trip
		trip.add_person(people[1])
		trip.add_wp('A')
		trip.travel(50, 'km')

		trip.assign_fuel_costs()

		expected = Quantity(25, 'km') * trip.vehicle.fuel_cost
		self.assertEqual(people[0].balance, expected)
		self.assertEqual(people[1].balance, expected)

	def test_assign_fuel_costs_single_person_two_links(self):
		"""Fuel cost assignment for an individual, 2 part journey."""
		trip = self.trip

		p = list(trip._people)[0]

		# define the trip
		trip.add_wp('A')
		trip.travel(50, 'km')
		trip.add_wp('B')
		trip.travel(100, 'km')
		trip.add_wp('C')

		trip.assign_fuel_costs()

		expected = Quantity(150, 'km') * trip.vehicle.fuel_cost
		self.assertEqual(p.balance, expected)

	def test_fuel_cost_estimate(self):
		"""Calculates the overall estimated fuel cost.

		This doesn't rely on people, i.e. it doesn't actually assign
		costs.
		"""
		trip = self.trip

		# Define the trip
		trip.add_wp('A')
		trip.travel(50, 'km')
		trip.add_wp('B')
		trip.travel(100, 'km')
		trip.add_wp('C')

		# Expected fuel cost
		expected = (Quantity(150, 'km') *
					trip.vehicle.fuel_cost.to('GBP/km'))

		self.assertEqual(trip.fuel_cost_estimate.to('GBP'), expected)

	def test_fuel_cost(self):
		"""Should return the actual fuel cost assigned manually."""

		trip = self.trip

		# Define the trip fuel cost in default currency
		trip.fuel_cost = 100.
		self.assertEqual(trip.fuel_cost.to('GBP'),
						 Quantity(100, 'GBP'))

		# Define a fuel cost in a different currency
		trip.fuel_cost = Quantity(125, 'EUR')
		self.assertEqual(trip.fuel_cost.to('EUR'),
						 Quantity(125, 'EUR'))

	def test_distance(self):
		"""Overall trip distance."""

		trip = self.trip

		# define
		trip.add_wp('A')
		trip.travel(50, 'km')
		trip.add_wp('B')
		trip.travel(100, 'km')
		trip.add_wp('C')

		self.assertEqual(trip.distance.to('km'), Quantity(150, 'km'))

	def test_fuel_breakdown_estimated(self):
		"""Returns a list of tuples containing fuel info.

		Where a fuel cost hasn't been assigned, estimates are used.
		"""

		trip = self.trip

		# define trip
		trip.add_wp('A')
		trip.travel(50, 'km')
		trip.add_wp('B')
		trip.travel(100, 'km')
		trip.add_wp('C')

		# Expected
		eta_cost = trip.vehicle.fuel_cost.to('GBP/km')
		eta_fuel = trip.vehicle.fuel_consumption.to('L/km')
		expected = [(q, q * eta_cost)
					for q in (Quantity(50, 'km'), Quantity(100, 'km'))]

		self.assertItemsEqual(trip.fuel_breakdown(), expected)

	def test_fuel_breakdown_actual(self):
		"""Returns a list of tuples containing fuel info."""

		trip = self.trip

		# define trip
		trip.add_wp('A')
		trip.travel(50, 'km')
		trip.add_wp('B')
		trip.travel(100, 'km')
		trip.add_wp('C')
		trip.fuel_cost = Quantity(45, 'GBP')

		# Expected
		expected = [(Quantity(50, 'km'), Quantity(15., 'GBP')),
					(Quantity(100, 'km'), Quantity(30., 'GBP'))]

		self.assertItemsEqual(trip.fuel_breakdown(), expected)

	def test_calculate_fuel_costs_no_arg(self):
		"""Fuel costs assigned to people based on estimates."""

		pA = list(self.trip._people)[0]
		# Define the trip
		self.trip.add_wp('A')
		self.trip.travel(50, 'km')
		pB = Person('B')
		self.trip.add_person(pB)
		self.trip.add_wp('B')
		self.trip.travel(100, 'km')
		self.trip.add_wp('C')

		# Calculate fuel costs.
		self.trip.assign_fuel_costs()

		# Expected costs per person.
		eta = self.trip.vehicle.fuel_cost.to('GBP/km')
		expected_A = Quantity(100, 'km') * eta
		expected_B = Quantity(50, 'km') * eta

		# Person A should have 2 cost estimates, Person B 1.
		self.assertAlmostEqual(pA.balance.magnitude,
							   expected_A.magnitude,
							   places=2)
		self.assertAlmostEqual(pB.balance.magnitude,
							   expected_B.magnitude,
							   places=2)

	def test_calculate_fuel_costs_with_override(self):
		"""Fuel costs assigned to people based on a real cost.

		The estimates here are used to evaluate the proportional cost
		of each travel component.
		"""

		pA = list(self.trip._people)[0]
		# Define the trip
		self.trip.add_wp('A')
		self.trip.travel(50, 'km')
		pB = Person('B')
		self.trip.add_person(pB)
		self.trip.add_wp('B')
		self.trip.travel(100, 'km')
		self.trip.add_wp('C')

		# Calculate fuel costs.
		self.trip.assign_fuel_costs(100, currency='GBP')

		# Expected costs per person.
		# Here person A should be paying 2/3 of the costs based on the
		# mileage breakdown. Person B, 1/3 of the costs.
		expected_A = 2./3. * 100 * units.GBP
		expected_B = 1./3. * 100 * units.GBP

		# Person A should have 2 cost estimates, Person B 1.
		self.assertAlmostEqual(pA.balance.magnitude,
							   expected_A.magnitude,
							   places=2)
		self.assertAlmostEqual(pB.balance.magnitude,
							   expected_B.magnitude,
							   places=2)


if __name__ == '__main__':
	unittest.main()
