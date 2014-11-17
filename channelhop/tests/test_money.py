import unittest

from channelhop import Quantity
from channelhop.money import Cost
from channelhop.person import Person

class TestCurrency(unittest.TestCase):
	# This is a bit tricky to test for without some static rates so
	# let's keep it stupid and simple.
	def test_eur_gbp(self):
		self.assertLess(Quantity(1, 'EUR'), Quantity(1 * 'GBP'))


class TestCost(unittest.TestCase):
	"""Exercise the Cost class."""
	sample = Cost('test123', 25., 'GBP')

	# Test initialisation
	def test_init_default_currency(self):
		"""Omitting the currency should default to 'GBP'."""
		c = Cost('', 1.)
		self.assertEqual(c.currency, 'GBP')

	def test_init_with_currency(self):
		"""Specifying a currency should override the default."""
		c = Cost('', 1., 'EUR')
		self.assertEqual(c.currency, 'EUR')

	def test_init_with_person(self):
		"""Specifying a person should relate the Cost to them."""
		p = Person('human')
		c = Cost('test', 25., person=p)
		self.assertIs(c.person, p)
		self.assertIn(c, p.bill)

	# Nothing fancy in the attributes. Add tests if they get extended.

	# ----------------------------------------------------------------
	# Test own methods.
	# ----------------------------------------------------------------
	def test_assign(self):
		"""Check the cost can be assigned to people."""
		people = Person('A'), Person('B')
		self.sample.assign(people)

		self.assertEqual(people[0].balance(), Quantity(25, 'GBP'))
		self.assertItemsEqual((self.sample,), people[0].bill)
		self.assertEqual(people[1].balance(), Quantity(25, 'GBP'))
		self.assertItemsEqual((self.sample,), people[1].bill)

	def test_split_assign_single_person(self):
		"""Splits the cost into equal parts and assigns to people."""
		people = (Person('A'),)
		self.sample.split_assign(people)

		self.assertEqual(people[0].balance().magnitude,
						 Quantity(25., 'GBP').magnitude)

	def test_split_assign_two_people(self):
		"""Splits cost between two people."""
		people = Person('A'), Person('B')
		self.sample.split_assign(people)

		self.assertEqual(people[0].balance().magnitude,
						 Quantity(12.5, 'GBP').magnitude)
		self.assertEqual(people[1].balance().magnitude,
						 Quantity(12.5, 'GBP').magnitude)

	def test_quantify(self):
		"""Converts the Cost instance into a plain Quantity."""
		quantified = self.sample._quantify()
		self.assertIsInstance(quantified, Quantity)
		self.assertNotIsInstance(quantified, Cost)
		self.assertEqual(quantified, Quantity(25., 'GBP'))

	def test_str(self):
		"""Check the string representation is as expected."""
		self.assertEqual(str(self.sample), '  25.00 GBP | test123')

	def test_repr(self):
		"""Check the programmatic representation is as expected."""
		self.assertEqual(repr(self.sample),
						 "<Cost('test123', 25.0, 'GBP')>")

	# ----------------------------------------------------------------
	# Test Quantity methods.
	# ----------------------------------------------------------------
	def test_to(self):
		"""Test currency conversion.

		This method replaces the Quantity method.
		"""
		expected = Quantity(1., 'GBP').to('EUR')
		cost = Cost('test', 1., 'GBP')

		self.assertEqual(cost.to('EUR').magnitude, expected.magnitude)
		self.assertEqual(cost.to('EUR').currency, 'EUR')

	# ----------------------------------------------------------------
	# Test arithmetic operators.
	# ----------------------------------------------------------------
	def test_div_by_int(self):
		quantity = self.sample / 2
		self.assertEqual(quantity, Quantity(12.50, 'GBP'))

	def test_div_by_quantity(self):
		quantity = self.sample / Quantity(10., 'm')
		self.assertEqual(quantity, Quantity(2.5, 'GBP/m'))

	def test_add_to_cost(self):
		quantity = self.sample + self.sample
		self.assertEqual(quantity, Quantity(50.00, 'GBP'))

	def test_add_to_zero(self):
		cost = self.sample + 0
		self.assertEqual(cost, self.sample)

	def test_add_to_quantity(self):
		quantity = self.sample + Quantity(5., 'GBP')
		self.assertEqual(quantity, Quantity(30., 'GBP'))

	def test_sum(self):
		costs = [self.sample, self.sample, self.sample]
		self.assertEqual(sum(costs), Quantity(75., 'GBP'))


if __name__ == '__main__':
	unittest.main()
