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
		have negative values. This test checks positive and negative
		parameter values in different currencies.
		"""
		p = self.person
		p.add_expense('test cost', -1., 'EUR')
		p.add_expense('test cost', 1., 'GBP')
		p.add_expense('test cost', -1.)

		# Check we have three items in the bill.
		self.assertEqual(len(p.bill), 3)

		# Check Cost instances, -ve values, and correct currency.
		for item, currency in zip(p.bill, ('EUR', 'GBP', 'GBP')):
			self.assertIsInstance(item, Cost)
			self.assertLess(item.magnitude, 0)
			self.assertEqual(item.currency, currency)

	def test_add_cost(self):
		"""Check a cost is assigned to the person correctly.

		Costs have a positive value as they represent IOUs (from that
		person) here. This test checks positive and negative
		parameter values in different currencies.
		"""
		p = self.person
		p.add_cost('test cost', -1., 'EUR')
		p.add_cost('test cost', 1., 'GBP')
		p.add_cost('test cost', 1.)

		# Check we have three items in the bill.
		self.assertEqual(len(p.bill), 3)

		# Check Cost instances, +ve values, and correct currency.
		for item, currency in zip(p.bill, ('EUR', 'GBP', 'GBP')):
			self.assertIsInstance(item, Cost)
			self.assertGreater(item.magnitude, 0)
			self.assertEqual(item.currency, currency)

	def test_balance(self):
		"""Calculate the balance of costs/expenses in 2	currencies.

		If this test passes, currency is being dealt with correctly.
		"""
		p = self.person

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

		p.add_expense('expense1', *expense_1)
		p.add_expense('expense2', *expense_2)
		p.add_cost('cost1', *cost_1)
		p.add_cost('cost2', *cost_2)

		# Check the balance is a Quantity (not a cost or expense)
		self.assertIsInstance(p.balance(), Quantity)

		# Check it's as expected, calculated separately here.
		msg = "{} != {} (expected; EUR = {} GBP)".format(
				p.balance().to('GBP'),
				expected_balance,
				Quantity(1, 'EUR').to('GBP').magnitude
		)
		self.assertAlmostEqual(p.balance().to('GBP').magnitude,
							   expected_balance.magnitude,
							   places=2,
							   msg=msg)


if __name__ == '__main__':
	unittest.main()
