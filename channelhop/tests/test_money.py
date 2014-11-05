import unittest

from channelhop.money import Cost
from channelhop.quantities import units, Quantity


class TestCurrency(unittest.TestCase):
	# This is a bit tricky to test for without some static rates so
	# let's keep it stupid and simple.
	def test_eur_gbp(self):
		self.assertLess(1 * units.EUR, 1 * units.GBP)


class TestCost(unittest.TestCase):
	"""Exercise the Cost class."""
	sample = Cost('test123', 25., 'GBP')

	def test_init(self):
		"""Tests various combinations of init parameters."""
		# Check omitting the amount raises a type error
		self.assertRaises(TypeError, Cost, '')
		# Check omitting the description raises a type error
		self.assertRaises(TypeError, Cost, 25.)

		# Check with and without currency
		c = Cost('test', 10.)
		self.assertEqual(c.currency, 'GBP')
		c = Cost('test', 13., 'EUR')
		self.assertEqual(c.currency, 'EUR')

		# Check a Quantity can be passed directly. This should ignore
		# the currency argument.
		c = Cost('test', Quantity(13., 'EUR'))
		self.assertEqual(c._quantity.magnitude, 13.)
		c = Cost('test', Quantity(10., 'GBP'), 'EUR')
		self.assertEqual(c._quantity.magnitude, 10.)

	# Check attributes
	def test_description(self):
		"""Checks the description is retrievable."""
		self.assertEqual(self.sample.description, 'test123')

	def test_currency(self):
		"""Checks the currency is retrievable."""
		self.assertEqual(self.sample.currency, 'GBP')

	# Check methods.
	def test_assign(self):
		"""Check the cost can be assigned to people."""
		self.skipTest("People not implemented.")

	def test_str(self):
		"""Check the string representation is as expected."""
		self.assertEqual(str(self.sample), '25.0 GBP | test123')

	def test_repr(self):
		"""Check the programmatic representation is as expected."""
		self.assertEqual(repr(self.sample),
						 "<Cost('test123', 25.0, 'GBP')>")


class TestExpense(unittest.TestCase):
	"""Exercise the Expense class.

	Expenses represent actual transactions/costs incurred by a person.
	"""
	def test_init(self):
		self.skipTest("Person not implemented yet.")


if __name__ == '__main__':
	unittest.main()
