import os
import csv
from collections import namedtuple, defaultdict
from datetime import timedelta, datetime
from places import LocationMap

FerryData = namedtuple('FerryData', 
					   ['source',
						'destination',
						'operator',
						'dep',
						'arr',
						'cost',
						'note'])

CarData = namedtuple('CarData',
					 ['source',
					  'destination',
					  'distance',
					  'duration',
					  'cost',
					  'note'])

class Parser(object):
	def __init__(self, lmap, tests=False):

		if tests:
			rel_path = ('tests', 'data')
		else:
			rel_path = ('data')
		self.path = os.path.join(os.path.dirname(__file__), *rel_path)
		self.lmap = lmap
		self.location = {loc.town:loc for loc in lmap.locations}

	def parse(self, records):
		"""Parse a dictionary of externally source route options.
		
		Dictionary should be keyed with ('car', 'ferry') with
		a list of CSV records in each.
		
		"""
		to_cardata = self.to_cardata
		to_ferrydata = self.to_ferrydata
		cd = list()
		for record in records['car']:
			record = record.split(',')
			route_pair = to_cardata(record)
			for route in route_pair:
				cd.append(route)
		fd = list()
		for record in records['ferry']:
			record = record.split(',')
			variants = to_ferrydata(record)
			for variant in variants:
				fd.append(variant)
		return cd, fd
	
	def to_cardata(self, row):
		"""Parse an external data record into two CarData."""
		source, destination = map(self.location.get, row[:2])
		distance = float(row[2])
		duration = map(int, row[3].split(':'))
		duration = timedelta(duration[0] * 3600 + duration[1] * 60)
		cost = float(row[4])
		note = row[5]
		cd = [CarData(source, destination, distance, duration, cost,
					  note),
			  CarData(destination, source, distance, duration, cost,
				  	  note)]
		return cd

	def to_ferrydata(self, row):
		"""Parse an external data record in 1-2 FerryData."""
		source, destination = map(self.location.get, row[:2])
		operator = row[2]
		dep_date = map(int, row[3].split('-'))
		dep_time = map(int, row[4].split(':'))
		dep_datetime = dep_date + dep_time
		dep = datetime(*dep_datetime)
		arr_date = map(int, row[5].split('-'))
		arr_time = map(int, row[6].split(':'))
		arr_datetime = arr_date + arr_time
		arr = datetime(*arr_datetime)
		cost, accom_cost, note = row[7:]
		cost, accom_cost = map(float, (cost, accom_cost))
		fd = [FerryData(source, destination, operator, dep, arr, cost,
						'')]
		if accom_cost > 0:
			cost += accom_cost
			fd.append(FerryData(source, destination, operator, dep,
								arr, cost, note))
		return fd
