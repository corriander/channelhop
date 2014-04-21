import unittest
import exdata
from places import LocationMap

class TestLoader(unittest.TestCase):
	def setUp(self):
		self.loader = exdata.Loader()
		dirname = os.path.dirname(__file__)
		datad = os.path.join(dirname, 'data')
		load = self.loader.load
		self.cardata = load(os.path.join(datad, 'car_routes.csv'))
		self.ferrydata = load(
				os.path.join(datad,	'ferry_crossings.csv'))
		self.lmap = LocationMap('A', 'B')
		self.locations = self.lmap.locations

	def test_car_data_records(self):
		"""Check the right number of car route records are retrieved.

		Each car route is duplicated (assumed bi-directional).
		
		"""
		self.assertEqual(len(self.cardata), 10)

	def test_initial_car_data(self):
		"""Test complete initial record is retrieved."""
		route = self.cardata[0]
		self.assertIsInstance(route, exdata.CarData)
		self.assertEqual(route.origin, self.locations['A'])
		self.assertEqual(route.distance, 40)
		self.assertEqual(route.duration, timedelta(0, 45, 0))
		self.assertEqual(route.cost, 8.5)
	
	def test_final_car_data(self):
		"""Test complete final record is retrieved. 
		
		This will be a reversed route and, in conjunction with
		test_initial_car_data should ensure all records are
		retrieved.
		
		"""
		route = self.cardata[-1]
		self.assertIsInstance(route, exdata.CarData)
		self.assertEqual(route.destination,
						 self.locations['Cherbourg'])
		self.assertEqual(route.duration, timedelta(3, 45, 0))
		self.assertEqual(route.cost, 50)

	def test_toll_variant(self):
		"""Test that the tolls note for a route variant is present."""
		route = self.cardata[4]
		self.assertIsInstance(route, exdata.CarData)
		self.assertEqual(route.destination, self.locations['B'])
		self.assertEqual(route.duration, timedelta(4, 30, 0))
		self.assertEqual(route.cost, 90)
		self.assertEqual(route.note, 'tolls')

	def test_car_data_records(self):
		"""Check retrieved  number of ferry crossing records.

		Ferry crossings with accomodation costs produce two variants
		(with/without accomodation). Otherwise ferry crossings are
		directional.
		
		"""
		self.assertEqual(len(self.ferrydata), 9)

	def test_initial_ferry_record(self):
		"""Test first ferry crossing record is retrieved."""
		route = self.ferrydata[0]
		self.assertEqual(route.origin, self.locations['Portsmouth'])
		self.assertEqual(route.operator, 'Operator A')
		self.assertEqual(route.dep, datetime(2000, 1, 2, 9, 30, 0))
		self.assertEqual(route.cost, 170)

	def test_final_ferry_record(self):
		"""Test final ferry crossing record.
		
		With test_initial_ferry_record this has a complete field
		coverage.
		
		"""
		route = self.ferrydata[-1]
		self.assertEqual(route.destination,
						 self.locations['Portsmouth'])
		self.assertEqual(route.operator, 'Operator B')
		self.assertEqual(route.arr, datetime(2000, 1, 4, 21, 0, 0))
		self.assertEqual(route.cost, 85.5)

	def test_accomodation_variant(self):
		"""Test accomodation variant.
		
		Accomodation variants are generated from a record with accom. 
		costs.

		"""
		route = self.ferrydata[2]
		self.assertEqual(route.cost, 75+85.5)
		self.assertEqual(route.note, '4-berth Cabin')

		# Check that the non-accomodation variant has correct cost
		route = self.ferrydata[1]
		self.assertEqual(route.cost, 75)
		self.assertEqual(route.note, '')
