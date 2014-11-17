import os
from datetime import date, timedelta
import urllib

from lxml.etree import ElementTree

from . import units, Quantity

# Constants
URI_ECB = 'http://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml'
URI_XML = 'channelhop/data/exchange_rates.xml' # FIXME: dynamic uri

# TODO: Build in some sort of fuel cost retrieval and move that out of
# the vehicle module.


class Cost(Quantity):
	"""A one-off cost, e.g. hotel bill, fuel cost.

	Costs are abstract, they don't represent any actual transaction.
	Example applications include estimated fuel cost, or a hotel bill
	yet to be paid.

	Costs are a crude wrapper around the Quantity class adding
	descriptions.
	"""
	def __new__(cls, description, amount, currency='GBP',
				person=None):
		"""Create a new cost instance.

		Arguments
		---------

			description : string describing the transaction.
			amount : either numerical value or Quantity.
			currency : currency to represent the cost.
		"""
		inst = Quantity.__new__(cls, amount, currency)

		# Add metadata to instance and, if necessary, associate.
		inst.description = description
		inst.person = person
		if person is not None:
			inst.assign((person,))
		inst.currency = currency

		return inst

	def assign(self, people):
		"""Assign cost to a number of people.

		Arguments

			people : sequence of Person instances.
		"""
		for person in people:
			person._bill.append(self)

	def split_assign(self, people):
		"""Divide cost equally and assign to a number of people.

		Arguments

			people : sequence of Person instances.
		"""
		n_people = len(people)
		cost = self / n_people
		cost.description = ', '.join((self.description,
									  '/ {} people'.format(n_people)))
		for person in people:
			person._bill.append(cost)

	def to(self, currency):
		"""Convert cost to a different currency."""
		# TODO: Build in currency validation.
		q = Quantity(self.magnitude, self.units).to(currency)
		return self.__class__(self.description,
							  q.magnitude,
							  q.units,
				   			  self.person)

	def __div__(self, other):
		if isinstance(other, (int, float, Quantity)):
			q_self = Quantity(self.magnitude, self.units)
			return q_self / other
		else:
			fmtstr = "Division of {} by {} unsupported."
			msg = fmtstr.format(self.__class__, type(other))
			raise TypeError(msg)
	__rdiv__ = __div__

	def __add__(self, other):
		if isinstance(other, Cost):
			return self._quantify() + other._quantify()
		elif isinstance(other, Quantity):
			return self._quantify() + other
		elif other == 0:
			return self
		else:
			fmtstr = "Addition of {} to {} unsupported."
			msg = fmtstr.format(self.__class__, type(other))
			raise TypeError(msg)
	__radd__ = __add__

	def _quantify(self):
		# Return Cost instance as a plain quantity.
		return Quantity(self.magnitude, self.units)

	def __str__(self):
		# Append description to Quantity string.
		return '{} | {}'.format(Quantity.__str__(self),
								self.description)

	def __repr__(self):
		# Return a programmatic representation
		return '<{}({!r}, {!r}, {!r})>'.format(self.__class__.__name__,
											   self.description,
											   self.magnitude,
											   self.currency)


class Expense(Cost):
	"""A one-off expense incurred by a person, e.g. a fuel bill.

	Expenses represent actual transactions.
	"""
	def __init__(self, person, description, amount, currency='GBP'):
		"""Arguments

			person : trip.Person Instance
			description : string describing the transaction.
			amount : either numerical value or Quantity.
			currency : currency to represent the cost.
		"""
		# Enforce expenses as a negative value (outgoings from the
		# person).
		amount = -1 * abs(amount)
		Cost.__init__(self, description, amount, currency)
		self.person = person


# Functions
def get_exchange_rates():
	"""Get exchange rates from the European Central Bank daily feed.

	Returns a dictionary mapping currency to the exchange rate
	relative to the Euro.

	Note that exchange rates are updated based on file modification
	time. The local copy may become a little out of date depending on
	when the last fetch occurred (e.g. over a weekend).
	"""
	# if local copy ECB exchange rates xml is older than a day,
	# re-fetch

	fetch = False
	try:
		xml_age = date.fromtimestamp(os.path.getmtime(URI_XML))
		if (date.today() > xml_age):
			fetch = True
	except IOError:
		fetch = True

	if fetch: urllib.urlretrieve(URI_ECB, URI_XML)

	tree = ElementTree(file=URI_XML)
	root = tree.getroot()

	# Map the exchange rates to a dictionary and return it. Rates are
	# in 'Cube' elements with currency (and rate) attributes under the
	# default namespace.
	return {
		element.attrib['currency'] : element.attrib['rate']
		for element in tree.findall('.//ns:Cube[@currency]',
									{'ns' : root.nsmap[None]})
	}

# Data
exchange_rates = get_exchange_rates()
supported_currencies = exchange_rates.keys()

# Configure units to represent currency (in a bit of a hacky, but
# valid, manner).
# TODO: Build in shortcuts (euro symbol, gbp symbol, etc.)
units.define('EUR = [currency]')	# Base unit.
for exr in exchange_rates.items():
	units.define('{} = EUR / {}'.format(*exr))

units.define('pence = 0.01 * GBP = p')
units.define('cent = 0.01 * EUR = c')	# Overwrite speed of light...

