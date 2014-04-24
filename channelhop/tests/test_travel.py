import unittest
from channelhop.travel import Waypoint, Link, Segment, SegmentMap
from channelhop.places import Location, LocationMap
from channelhop.exdata import FerryData
from channelhop.exdata import CarData
from channelhop.exdata import Parser
from channelhop.tests.test_exdata import FERRY_DATA
from channelhop.tests.test_exdata import CAR_DATA
from channelhop.timing import DateTime, Duration
from datetime import timedelta, datetime

class TestWaypoint(unittest.TestCase):
	def setUp(self):
		location = Location('A', 'Country')
		self.wp = Waypoint(location, datetime(2000, 1, 1, 9, 30))

	def test_waypoint(self):
		self.assertEqual(self.wp.location.town, 'A')
		self.assertEqual(self.wp.location.country, 'Country')
		self.assertEqual(str(self.wp), 'A, Country (Sat 01 Jan, 0930)')

	def test_merge_with_no_datetime(self):
		"""Test a merge with a waypoint lacking a datetime.
		
		Waypoint with a datetime remain unchanged.
		
		"""
		new_wp = Waypoint(self.wp.location, None)
		old_wp = self.wp
		old_wp.merge(new_wp)
		self.assertEqual(old_wp, self.wp)

	def test_merge_with_datetime(self):
		"""Test merge with a waypoint possessing a datetime.
		
		Waypoint is updated with the new datetime.
		
		"""
		old_wp = Waypoint(self.wp.location, None)
		new_wp = self.wp
		old_wp.merge(new_wp)
		self.assertEqual(old_wp, self.wp)

	def test_merge_nodatetimes(self):
		"""Test merge between two waypoints with no datetimes"""
		old_wp = Waypoint(self.wp.location, None)
		new_wp = Waypoint(self.wp.location, None)
		copy = old_wp
		old_wp.merge(new_wp)
		self.assertEqual(old_wp, copy)

	def test_merge_mismatched_location(self):
		"""Test merge between two waypoints with different locations.

		This is not valid and should raise an exception.

		"""
		wp1 = Waypoint(self.wp.location, None)
		wp2 = Waypoint(Location('B', 'Country'), None)
		self.assertRaises(ValueError, wp2.merge, wp1)

	def test_clash_merge(self):
		"""Test merge between two waypoints with different datetimes.

		Not enough information to deal with, raise exception.

		"""
		wp1 = Waypoint(self.wp.location, datetime(2000, 1, 2))
		wp2 = Waypoint(self.wp.location, datetime(2000, 1, 1))
		self.assertRaises(ValueError, wp2.merge, wp1)


class TestLink(unittest.TestCase):
	def setUp(self):
		duration = timedelta(hours=9, minutes=30)
		note = ''
		self.link = Link(duration, 95.30, note)

	def test_link(self):
		self.assertEqual(self.link.duration, timedelta(hours=9,
			minutes=30))
		self.assertEqual(self.link.note, '')
		self.assertEqual(self.link.cost, 95.30) 


class TestSegment(unittest.TestCase):
	def test_unanchored_route(self):
		start = Waypoint(Location('A', 'UK'), None)
		end = Waypoint(Location('B', 'UK'), None)
		link = Link(timedelta(hours=0, minutes=45), 5.50, '')
		seg = Segment(start, end, link)
		self.assertEqual(str(seg), 'A, UK --> B, UK : 0h45 £5.50')
	
	#def test_anchored_route(self):
	#	"""Tests a route with a fully qualified starting waypoint.

	#	Checks end waypoint is re-evaluated.

	#	"""
	#	start = Waypoint(Location('A', 'UK'), 
	#					 datetime(2000, 1, 1, 9, 30))
	#	end = Waypoint(Location('B', 'UK'), None)
	#	link = Link(timedelta(hours=0, minutes=45), 5.50, '')
	#	self.assertEqual(seg.end.datetime, 
	#					 datetime(2000, 1, 1, 10, 15))
	
	def test_double_anchored_route(self):
		start = Waypoint(Location('A', 'UK'), 
						 datetime(2000, 1, 1, 9, 30))
		end = Waypoint(Location('B', 'UK'),
					   datetime(2000, 1, 1, 10, 15))
		link = Link(timedelta(hours=0, minutes=45), 5.50, '')
		seg = Segment(start, end, link)
		self.assertEqual(str(seg),
						 'A, UK (Sat 01 Jan, 0930) --> '
						 'B, UK (Sat 01 Jan, 1015) : '
						 '0h45 \xc2\xa35.50')
	
	def test_over_constrained_route(self):
		"""An over-constrained segment should raise an exception."""
		start = Waypoint(Location('A', 'UK'), 
						 datetime(2000, 1, 1, 9, 30))
		end = Waypoint(Location('B', 'UK'),
					   datetime(2000, 1, 1, 10, 15))
		link = Link(timedelta(hours=0, minutes=50), 5.65, '')
		self.assertRaises(ValueError, Segment, start, end, link)

	def test_from_CarData(self):
		cd = CarData(Location('A', 'UK'),
					 Location('B', 'UK'),
					 65, 
					 timedelta(hours=1, minutes=30),
					 15,
					 'test note')
		seg = Segment.from_CarData(cd)
		self.assertEqual(seg.end.location.town, 'B')
		self.assertEqual(seg.link.duration.seconds, 5400)
		self.assertEqual(seg.link.cost, 15.0)


	def test_from_FerryData(self):
		record = FerryData(Location('A', 'UK'),
					   Location('B', 'FR'),
					   'Ferry Operator',
					   datetime(2000, 1, 1, 23, 00),
					   datetime(2000, 1, 2, 4, 00),
					   240,
					   'test note')
		seg = Segment.from_FerryData(record)
		self.assertEqual(seg.end.location.country, 'FR')
		self.assertEqual(seg.link.duration.seconds, 14400)
		self.assertEqual(seg.link.cost, 240)
		self.assertEqual(seg.link.note, 'Ferry Operator, test note') 
		expected_string = ('A, UK (Sat 01 Jan, 2300) --> '
						   'B, FR (Sun 02 Jan, 0400) : '
						   '4h0 £240.00. '
						   'Ferry Operator, test note'
						   )
		self.assertEqual(str(seg), expected_string)
			 

class TestSegmentMap(unittest.TestCase):
	"""Test Case for the SegmentMap class.

	SegmentMap is a dictionary/mapping of location pairs to itinerary
	segments generated from the externally-sourced datasets for
	ferries and road/car routes.

	"""
	def setUp(self):
		dataset = {'car' : CAR_DATA, 'ferry' : FERRY_DATA}
		lmap = LocationMap('A', 'B')
		cardata, ferrydata = Parser(lmap).parse(dataset)
		self.segmap = SegmentMap(cardata, ferrydata)

	def test_non_constrained_single_route(self):
		"""Tests for a simple bi-directional road route (no sched.)"""
		key = Location('A', 'UK'), Location('Portsmouth', 'UK')
		self.assertEqual(len(self.segmap[key]), 1)
		self.assertEqual(len(self.segmap[key[::-1]]), 1)

		# Check segment structure
		start = Waypoint(key[0], None)
		end = Waypoint(key[1], None)
		link = Link(duration=timedelta(minutes=45),
					cost=8.50,
					note='')

		# Test outward route is present and correct
		segment = Segment(start, end, link)
		self.assertEqual(self.segmap[key][0], segment)
		# Test inward route is present and correct
		segment = Segment(end, start, link)
		self.assertEqual(self.segmap[key[::-1]][0], segment)

	def test_constrained_single_route(self):
		"""Tests for a single-option ferry route.

		Checks that the sample ferry route (Portsmouth --> Cherbourg)
		is present and correct and is unique (it's directional so
		should not exist in the Cherbourg --> Portsmouth mapping.

		"""
		key = (Location('Portsmouth', 'UK'), 
			   Location('Cherbourg', 'FR'))
		self.assertEqual(len(self.segmap[key]), 1)

		# Check segment structure
		start = Waypoint(key[0], datetime(2000, 1, 2, 9, 30))
		end = Waypoint(key[1], datetime(2000, 1, 2, 13, 0))
		link = Link(duration=timedelta(hours=2, minutes=30),
					cost=170.0,
					note='Operator A')

		# Test outward route is present and correct
		segment = Segment(start, end, link)
		self.assertEqual(self.segmap[key][0], segment)
		# Test inward route is NOT the same
		self.assertNotEqual(self.segmap[key[::-1]][0], segment)

	def test_non_constrained_multiroute(self):
		"""Tests for a multi-option car/road route.

		Checks that all options are present and correct for both
		outward and return location-pairs.

		"""
		key = (Location('Le Havre', 'FR'), 
			   Location('B', 'FR'))

		# Check segment structure
		start = Waypoint(key[0], None)
		end = Waypoint(key[1], None)
		link_a = Link(duration=timedelta(hours=5, minutes=0),
					  cost=70.50,
					  note='')
		link_b = Link(duration=timedelta(hours=4, minutes=30),
					  cost=90.0,
					  note='tolls')

		# Test outward routes present and correct
		self.assertEqual(len(self.segmap[key]), 2)
		segment_a = Segment(start, end, link_a)
		segment_b = Segment(start, end, link_b)
		self.assertIn(segment_a, self.segmap[key])
		self.assertIn(segment_b, self.segmap[key])
		
		# Test inward routes also present and correct
		key = key[::-1]
		self.assertEqual(len(self.segmap[key]), 2)
		segment_a = Segment(end, start, link_a)
		segment_b = Segment(end, start, link_b)
		self.assertIn(segment_a, self.segmap[key])
		self.assertIn(segment_b, self.segmap[key])


class TestItinerary(unittest.TestCase):
	"""Test case for the Itinerary class"""
	def setUp(self):
		path = [Location('A', 'UK'),
				Location('Portsmouth', 'UK'),
				Location('Cherbourg', 'FR'),
				Location('B', 'FR')
				]

		car_wps = map(lambda l: Waypoint(l, None) for l in path)
		fer_wps = [Waypoint(path[1], datetime(2000, 1, 1, 9, 0)),
				   Waypoint(path[2], datetime(2000, 1, 1, 13, 0))]
		car = [Link(timedelta(minutes=45), 5.0, '')
			   Link(timedelta(minutes=90), 10.0, '')]
		ferry = Link(timedelta(minutes=180), 100.0, 'Ferry Operator')

		segments = [
				Segment(*car_wps[:2], link=car[0]),
				Segment(*fer_wps, link=ferry)
				Segment(*car_wps[2:], link=car[1]),
				]
		self.itin = Itinerary(segments)

	def test_cost(self):
		"""Test total cost for itinerary is calculated correctly."""
		self.assertEqual(self.itin.cost, 115.0)

	def test_arrival(self):
		"""Test the itinerary reports correct arrival time."""
		self.assertEqual(self.itin.arrival, 
						 datetime(2000, 1, 1, 14, 30))

	def test_departure(self):
		"""With test_arrival, this ensures schedule has been calced"""
		self.assertEqual(self.itin[0].datetime,
						 datetime(2000, 1, 1, 8, 15))


if __name__ == '__main__':
	unittest.main()
