import unittest
from datetime import datetime, timedelta
import channelhop.exdata as exdata
from channelhop.places import LocationMap

FERRY_DATA = """
Portsmouth,Cherbourg,Operator A,2000-01-02,09:30,2000-01-02,13:00,170,0,
Portsmouth,Le Havre,Operator B,2000-01-01,23:00,2000-01-02,08:00,75,85.5,
Portsmouth,Le Havre,Operator B,2000-01-02,23:00,2000-01-03,08:00,106.5,110,
Poole,Cherbourg,Operator C,2000-01-02,08:30,2000-01-02,13:00,160,0,
Cherbourg,Portsmouth,Operator A,2000-01-04,17:00,2000-01-04,19:00,170,0,
Cherbourg,Poole,Operator C,2000-01-04,18:30,2000-01-04,21:00,185,0,
Le Havre,Portsmouth,Operator B,2000-01-04,17:00,2000-01-04,21:00,85.5,0,
""".strip().split('\n')

CAR_DATA = """
A,Portsmouth,40,00:45,8.5,
A,Poole,60,01:30,10,
Le Havre,B,250,04:30,90,tolls
Le Havre,B,300,05:00,70.5,
Cherbourg,B,200,03:45,50,
""".strip().split('\n')


class TestParser(unittest.TestCase):
	def setUp(self):
		self.lmap = LocationMap('A', 'B')
		self.parser = exdata.Parser(self.lmap)
		raw_data = {'ferry' : FERRY_DATA, 'car' : CAR_DATA}
		self.cardata, self.ferrydata = self.parser.parse(raw_data)
		self.locations = {loc.town:loc for loc in self.lmap.locations}

	def test_car_data_records(self):
		"""Check the right number of car route records are retrieved.

		Each car route is duplicated (assumed bi-directional).
		
		"""
		self.assertEqual(len(self.cardata), 10)

	def test_initial_car_data(self):
		"""Test complete initial record is retrieved."""
		route = self.cardata[0]
		self.assertIsInstance(route, exdata.CarData)
		self.assertEqual(route.source, self.locations['A'])
		self.assertEqual(route.distance, 40)
		self.assertEqual(route.duration, timedelta(minutes=45))
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
		self.assertEqual(route.duration, timedelta(minutes=225))
		self.assertEqual(route.cost, 50)

	def test_toll_variant(self):
		"""Test that the tolls note for a route variant is present."""
		route = self.cardata[4]
		self.assertIsInstance(route, exdata.CarData)
		self.assertEqual(route.destination, self.locations['B'])
		self.assertEqual(route.duration, timedelta(minutes=270))
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
		self.assertEqual(route.source, self.locations['Portsmouth'])
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
		self.assertEqual(route.note, 'Cabin')

		# Check that the non-accomodation variant has correct cost
		route = self.ferrydata[1]
		self.assertEqual(route.cost, 75)
		self.assertEqual(route.note, '')

if __name__ == '__main__':
	unittest.main()
