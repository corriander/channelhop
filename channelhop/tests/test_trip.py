import unittest

from channelhop.person import Person
from channelhop.vehicle import Car, FUELPRICE
from channelhop.money import Expense, Cost
from channelhop.quantities import units, Quantity
from channelhop.trip import Trip, TripDefError

class TestTrip(unittest.TestCase):
	"""Exercise Trip class."""
	def setUp(self):
		"""Define a trip in a car with a 60 L tank and 0.1 L/km."""
		self.trip = Trip('test trip', Car(60, 0.1))
		self.trip.add_person(Person('A'))

	# ----------------------------------------------------------------
	# Check attributes/properties
	# ----------------------------------------------------------------
	def test_distance(self):
		"""Overall trip distance."""
		trip = self.trip

		trip.add_wp('A')
		trip.travel(50, 'km')
		trip.add_wp('B')
		trip.travel(100, 'km')
		trip.add_wp('C')

		self.assertEqual(trip.distance.to('km'), Quantity(150, 'km'))

	def test_fuel_cost(self):
		"""Should return the actual fuel cost assigned manually."""
		trip = self.trip

		# Fuel cost is unassigned initially
		self.assertRaises(AttributeError, lambda : trip.fuel_cost)

		# REMOVEME
		## Define the trip fuel cost in default currency
		#trip._fuel_cost = 100.
		#self.assertEqual(trip.fuel_cost.to('GBP'),
		#				 Quantity(100, 'GBP'))

		## Define a fuel cost in a different currency
		#trip._fuel_cost = Quantity(125, 'EUR')
		#self.assertEqual(trip.fuel_cost.to('EUR'),
		#				 Quantity(125, 'EUR'))

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
					trip.vehicle.unit_fuel_cost.to('GBP/km'))

		self.assertEqual(trip.fuel_cost_estimate.to('GBP'), expected)

	def test_last_wp_single_waypoint(self):
		"""Check the last_wp attribute returns the only waypoint."""
		trip = self.trip

		trip.add_wp('A')
		self.assertEqual(trip.last_wp.location, 'A')

	def test_last_wp_multiple_waypoints(self):
		"""Check the last_wp attribute returns the latest waypoint."""
		trip = self.trip

		trip.add_wp('A')
		trip.add_wp('B')
		self.assertEqual(trip.last_wp.location, 'B')

	def test_last_wp_where_last_item_is_link(self):
		"""For a waypoint + link, last_wp should return the wp."""
		trip = self.trip

		trip.add_wp('A')
		trip.travel(50, 'km')
		self.assertEqual(trip.last_wp.location, 'A')

	# ----------------------------------------------------------------
	# Check methods
	# ----------------------------------------------------------------
	def test_add_wp(self):
		"""Waypoint are addable with at least one person."""
		trip = self.trip

		trip.add_wp('A')
		self.assertEqual(trip._people, trip._items[-1].people)

	def test_add_wp_multiple_people(self):
		"""The waypoint is associated with all people on the trip."""
		trip = self.trip

		trip.add_person(Person('B'))
		trip.add_wp('A')
		self.assertEqual(trip._people, trip._items[-1].people)

	def test_add_wp_no_people(self):
		"""Adding a waypoint before adding people isn't possible."""
		trip = Trip('test', Car(1,1))
		self.assertRaises(TripDefError, lambda : trip.add_wp('A'))

	def test_travel_no_origin(self):
		"""No origin/waypoint & travel should raise an exception."""
		trip = self.trip
		self.assertRaises(TripDefError,
						  lambda : trip.travel(50, 'km'))

	def test_travel_with_origin(self):
		"""Origin/waypoint & travel should succeed.

		The waypoint and the link should both be associated with all
		people on the trip.
		"""
		trip = self.trip

		trip.add_wp('A')
		trip.travel(50, 'km')

		# Check that the trip elements so far are as expected.
		self.assertEqual(len(trip._items), 2)
		self.assertEqual(trip._items[0].location, 'A')
		self.assertEqual(trip._items[1].distance.magnitude, 50)

		# Check the travel segment inherited the people from the last
		# waypoint.
		self.assertIs(trip._items[1].people,
					  trip._items[0].people)

	def test_add_cost(self):
		"""Assigns a Cost instance to the last waypoint.

		This test checks the cost is assigned to the waypoint
		successfully.
		"""
		trip = self.trip

		trip.add_wp('A')
		trip.add_cost('test', 1.)

		self.assertIsInstance(trip.last_wp.cost, Cost)
		cost = trip.last_wp.cost.to('GBP')

		self.assertEqual(trip.last_wp.cost.to('GBP').magnitude, 1.)

	def test_add_cost_with_currency(self):
		"""Costs can be assigned to WPs in different currencies."""
		trip = self.trip

		trip.add_wp('A')
		trip.add_cost('test', 1., 'EUR')

		self.assertEqual(trip.last_wp.cost.currency, 'EUR')


	def test_add_cost_reassign(self):
		"""Only a single cost can be assigned to a waypoint at a time.

		Subsequent invocation of the add_cost method replaces the
		previous cost. This test checks that happens.
		"""
		trip = self.trip
		trip.add_wp('A')

		# Add a cost, check it, then add another and check that the
		# old cost is overwritten.
		trip.add_cost('test', 1.)
		self.assertEqual(trip.last_wp.cost.to('GBP').magnitude, 1.)
		trip.add_cost('test', 2.)
		self.assertEqual(trip.last_wp.cost.to('GBP').magnitude, 2.)

	def test_add_second_person(self):
		"""Additional people shouldn't be associated with all WPs."""
		trip = self.trip

		person = Person('B')

		trip.add_wp('A')
		trip.add_person(person)
		self.assertNotIn(person, trip.last_wp.people)

		trip.add_wp('B')
		self.assertIn(person, trip.last_wp.people)

	def test_rm_second_person(self):
		"""Removed people shouldn't be associated with all WPs."""
		trip = self.trip

		person = Person('B')

		trip.add_person(person)
		trip.add_wp('A')
		self.assertIn(person, trip.last_wp.people)

		trip.rm_person(person)
		trip.add_wp('B')
		self.assertNotIn(person, trip.last_wp.people)

	def test_fuel_breakdown_estimated(self):
		"""Returns list of Cost instances based on estimated fuel."""
		trip = self.trip

		# define trip
		trip.add_wp('A')
		trip.travel(50, 'km')
		trip.add_wp('B')
		trip.travel(100, 'km')
		trip.add_wp('C')

		# Expected
		eta = trip.vehicle.unit_fuel_cost.to('GBP/km')
		expected_amounts = [
				(eta * Quantity(50, 'km')).magnitude,
				(eta * Quantity(100, 'km')).magnitude
		]
		actual_amounts = [
				c.magnitude for c in trip.fuel_breakdown()
		]
		pairs = zip((c.magnitude for c in trip.fuel_breakdown()),
					expected_amounts)

		for amount, expected in pairs:
			self.assertAlmostEqual(amount, expected, places=2)

	def test_fuel_breakdown_actual(self):
		"""Returns a list of Cost instances based on actual fuel cost.

		The test takes the magnitude of the Cost instances and
		compares them against expected magnitudes, based on a constant
		fuel consumption.

		This type of calculation is performed if the trip.fuel_cost is
		set.
		"""
		trip = self.trip

		# define trip
		trip.add_wp('A')
		trip.travel(50, 'km')
		trip.add_wp('B')
		trip.travel(100, 'km')
		trip.add_wp('C')

		# Explicitly set actual fuel cost in GBP
		trip._fuel_cost = Quantity(45, 'GBP')

		actual_amounts = []
		for cost in trip.fuel_breakdown():
			self.assertIsInstance(cost, Cost)
			actual_amounts.append(cost.magnitude)

		expected_amounts = (15., 30.)

		for amount, expected in zip(actual_amounts, expected_amounts):
			self.assertAlmostEqual(amount, expected)

	def test_fuel_breakdown_actual_lower_than_estimate(self):
		"""Returns a list of Cost instances based on actual fuel cost.

		The test takes the magnitude of the Cost instances and
		compares them against expected magnitudes, based on a constant
		fuel consumption.

		This type of calculation is performed if the trip.fuel_cost is
		set.

		NOTE: This test is here because of a pecularity in Pint's
		handling of dimensionless ratios (or maybe, handling of this
		in Cost).
		"""
		trip = self.trip

		# define trip
		trip.add_wp('A')
		trip.travel(50, 'km')
		trip.add_wp('B')
		trip.travel(100, 'km')
		trip.add_wp('C')

		# Explicitly set actual fuel cost in GBP
		trip._fuel_cost = Quantity(6, 'GBP')

		actual_amounts = []
		for cost in trip.fuel_breakdown():
			self.assertIsInstance(cost, Cost)
			actual_amounts.append(cost.magnitude)

		expected_amounts = (2., 4.)

		for amount, expected in zip(actual_amounts, expected_amounts):
			self.assertAlmostEqual(amount, expected)

	def test_assign_fuel_costs_single_person_and_link(self):
		"""Fuel costs assigned to a single person, single Link."""
		trip = self.trip

		p = list(trip._people)[0]

		# define the trip
		trip.add_wp('A')
		trip.travel(50, 'km')

		trip.assign_fuel_costs()

		expected = Quantity(50, 'km') * trip.vehicle.unit_fuel_cost
		self.assertEqual(p.balance(), expected.to('GBP'))

	def test_assign_fuel_costs_single_link_and_two_people(self):
		"""Fuel costs assigned to two people over a single Link."""
		trip = self.trip

		people = list(trip._people)[0], Person('B')

		# define the trip
		trip.add_person(people[1])
		trip.add_wp('A')
		trip.travel(50, 'km')

		trip.assign_fuel_costs()

		expected = Quantity(25, 'km') * trip.vehicle.unit_fuel_cost
		self.assertEqual(people[0].balance(), expected.to('GBP'))
		self.assertEqual(people[1].balance(), expected.to('GBP'))

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

		expected = Quantity(150, 'km') * trip.vehicle.unit_fuel_cost
		self.assertEqual(p.balance(), expected.to('GBP'))

	def test_assign_fuel_costs_add_person_mid_route(self):
		"""Fuel cost assignment for additional person mid-route."""
		trip = self.trip

		people = list(trip._people)[0], Person('B')

		# define the trip
		trip.add_wp('A')
		trip.travel(50, 'km')

		trip.add_person(people[1])
		trip.add_wp('B')
		trip.travel(100, 'km')
		trip.add_wp('C')

		trip.assign_fuel_costs()

		# Check each person has expected number of bill items.
		self.assertEqual(len(people[0].bill), 2)
		self.assertEqual(len(people[1].bill), 1)

		# Check each balance()
		eta = trip.vehicle.unit_fuel_cost
		self.assertEqual(people[0].balance(),
						 Quantity(100, 'km') * eta)
		self.assertEqual(people[1].balance(),
						 Quantity(50, 'km') * eta)

	# ----------------------------------------------------------------
	# Use-case tests - These are not really unit tests!
	# ----------------------------------------------------------------
	def test_trip_A(self):
		"""Trip with 2 waypoints and a new passenger at second.

			- Depart with a parking cost
			- Arrive, park and pick up new passenger (responsible for
			  parking share)
		"""
		trip = self.trip

		people = list(trip._people)[0], Person('B')
		trip.add_wp('A')
		trip.add_cost('ParkingA', 5)
		trip.travel(50, 'km')

		trip.add_person(people[1])
		trip.add_wp('B')
		trip.add_cost('ParkingB', 10)

		# Sanity checks to make sure they are actually present for the
		# right parts of the trip.
		self.assertNotIn(people[1], trip._items[0].people)
		self.assertNotIn(people[1], trip._items[1].people)
		self.assertIn(people[1], trip._items[2].people)

		# Persons A and B should both have costs associated with them
		# here. As B has been removed before the second waypoint, the
		# system assumes they don't incur this cost.
		self.assertEqual(people[0].balance(), Quantity(10.0, 'GBP'))
		self.assertEqual(people[1].balance(), Quantity(5.0, 'GBP'))

		# Calculate fuel shares and re-check the balance.
		trip.assign_fuel_costs()
		fuel_cost = (Quantity(50, 'km') * trip.vehicle.unit_fuel_cost)
		self.assertEqual(people[0].balance(),
						 Quantity(10.0, 'GBP') + fuel_cost)
		self.assertEqual(people[1].balance(), Quantity(5.0, 'GBP'))

	def test_trip_B(self):
		"""Trip with 4 waypoints, multiple currencies and varying ppl.

			- Depart with two people
			- Park at second waypoint, pick up third person, drop off
			  second.
			- Cross border (distance units and currency change)
			- Drive to destination.

		In this case, the real fuel cost differs from the estimate due
		to bad traffic.
		"""
		trip = self.trip
		people = list(trip._people)[0], Person('B'), Person('C')

		# These will be used in input and validation.
		a2b, b2c, c2d = (100, 'miles'), (10, 'miles'), (234, 'km')
		fuel_payment = (30, 'GBP')

		trip.add_person(people[1])	# 'B' is also departing
		trip.add_wp('A')			# origin
		trip.travel(*a2b)	# to pick up 'C' and drop off 'B'
		trip.add_person(people[2])	# 'C' joins
		trip.rm_person(people[1])	# 'B' leaves
		trip.add_wp('B')
		trip.add_cost('ParkingB', 2.5, 'GBP')	# Park to get 'B'
		trip.travel(*b2c)						# Travel to border
		trip.add_wp('C')
		trip.travel(*c2d)						# Travel from border
		trip.add_wp('D')
		trip.add_cost('ParkingD', 12., 'EUR')	# Park at destination

		trip.assign_fuel_costs(*fuel_payment)	# Calculate bills

		# Check everyone is present at the right points
		self.assertItemsEqual(trip._items[0].people, people[:2])
		self.assertItemsEqual(trip._items[1].people, people[:2])
		self.assertItemsEqual(trip._items[2].people,
							  (people[0], people[2]))
		self.assertItemsEqual(trip._items[3].people,
							  (people[0], people[2]))
		self.assertItemsEqual(trip._items[4].people,
							  (people[0], people[2]))

		# Check each person has the expected number of bill elements
		self.assertEqual(len(people[0].bill), 5)
		self.assertEqual(len(people[1].bill), 1)
		self.assertEqual(len(people[2].bill), 4)

		# Person A incurs half of all the fuel costs and parking costs
		fuel_cost = 15. # GBP
		parking = 1.25 + (6. * Quantity(1, 'EUR').to('GBP').magnitude)
		total = fuel_cost + parking # GBP
		self.assertAlmostEqual(people[0].balance().magnitude,
							   total,
							   places=2)

		# Persons B and C cover the other half.
		self.assertAlmostEqual((people[1].balance().magnitude +
								people[2].balance().magnitude),
								total,
								places=2)

		# Person B only incurs half of the fuel cost for the initial
		# 100 mile drive (which, by virtue of the above, means C is
		# correct).
		ratio = Quantity(50, 'miles') / trip.distance.to('miles')
		fuel_cost = 30. * ratio	# GBP
		self.assertAlmostEqual(people[1].balance().magnitude,
							   fuel_cost,
							   places=2)


if __name__ == '__main__':
	unittest.main()
