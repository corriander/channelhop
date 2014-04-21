from channelhop.places import Location, LocationMap, FERRY_ROUTES
import unittest

sample_locations = {} 

class TestLocation(unittest.TestCase):
	def test___init__(self):
		sample_locations['origin'] = test = Location('A', 'UK')
		self.assertEqual(test, ('A', 'UK'))
		sample_locations['destination'] = test = Location('B', 'FR')
		self.assertEqual(Location('B', 'FR'), ('B', 'FR'))


class TestLocationMap(unittest.TestCase):
	def setUp(self):
		self.orig = 'A'
		self.dest = 'B'
		self.lmap = LocationMap(self.orig, self.dest)
		self.orig = self.lmap.origin
		self.dest = self.lmap.destination
		fr = FERRY_ROUTES
		self.expected_paths = [[self.orig, r[0], r[1], self.dest] 
							   for r in FERRY_ROUTES
							   ]
		self.expected_returns = [path[::-1]
								 for path in self.expected_paths]
		

	def test_find_right_number_of_paths(self):
		self.assertEqual(len(self.lmap.paths['OUT']), 6)
	
	def test_correct_out_paths(self):
		self.assertItemsEqual(self.lmap.paths['OUT'], 
							  self.expected_paths)
	
	def test_correct_rtn_paths(self):
		self.assertItemsEqual(self.lmap.paths['RTN'],
							  self.expected_returns)


if __name__ == '__main__':
	unittest.main()

