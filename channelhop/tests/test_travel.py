import unittest
from channelhop.travel import Waypoint, Link, Segment
from channelhop.places import Location
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
		self.assertEqual(str(seg),
			('A, UK / B, FR : Sat 01 Jan 2300-0400 (4h0) £240.00\n'
			 '\tFerry Operator, test note'))

if __name__ == '__main__':
	unittest.main()
