import unittest

from channelhop import Quantity
from channelhop.money import Cost
from channelhop.person import Person


class TestPerson(unittest.TestCase):
	"""Exercises the Person class.

	People primarily exist here to be assigned a bill, representing
	their contributions and owed monies.
	"""
	# Init is so simple it's not worth testing. Go straight to
	# creating a test person.
	def setUp(self):
		self.person = Person('Bob')

	# check attributes.
	def test_bill(self):
		"""Check the bill attribute is as expected on init."""
		p = self.person

		self.assertIsInstance(p.bill, list)
		self.assertEqual(len(p.bill), 0)

	# Test methods
	def test_add_expense(self):
		"""Check an expense is assigned correctly.

		Expenses are represented as outgoings from the person, so they
		have negative values.
		"""
		p = self.person
		p.add_expense('test expense', 10., 'GBP')

		# Check we have one Cost item.
		item = p.bill[0]

		self.assertEqual(len(p.bill), 1)
		self.assertIsInstance(item, Cost)
		# Check the cost is associated with the person.
		self.assertIs(item.person, p)
		# Check the cost has a negative value.
		self.assertLess(item, 0)

	def test_add_cost(self):
		"""Check a cost is assigned to the person correctly.

		Costs have a positive value as they represent IOUs (from that
		person) here.
		"""
		p = self.person
		p.add_cost('test cost', 7., 'EUR')

		# Check we have one expense/cost
		self.assertEqual(len(p.bill), 1)

		# Check it's a Cost instance and its value is positive.
		item = p.bill[0]
		self.assertIsInstance(item, Cost)
		self.assertGreater(item.magnitude, 0)

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

	# bill is just a list of expenses, the important bit is the balance.


if __name__ == '__main__':
	unittest.main()
