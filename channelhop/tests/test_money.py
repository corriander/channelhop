import unittest

import channelhop.money as money
from channelhop.quantities import units


class TestCurrency(unittest.TestCase):
	# This is a bit tricky to test for without some static rates so
	# let's keep it stupid and simple.
	def test_eur_gbp(self):
		self.assertLess(1 * units.EUR, 1 * units.GBP)


if __name__ == '__main__':
	unittest.main()
