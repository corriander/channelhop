import os
from datetime import date, timedelta
import urllib

from lxml.etree import ElementTree

from quantities import units, Quantity

# Constants
URI_ECB = 'http://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml'
URI_XML = 'channelhop/data/exchange_rates.xml' # FIXME: dynamic uri

# TODO: Build in some sort of fuel cost retrieval and move that out of
# the vehicle module.


class Expense(object):
	"""A one-off expense.

	Optionally associated with a person, with optional date,
	description and currency for detail purposes.
	"""
	def __init__(self, value, date=None, description=None, owner=None,
				 currency='GBP'):
		# TODO: Probably want some type-checking here.
		self.value = value
		self.description = description
		self.date = date
		self.owner = owner


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

units.define('pence = 100 * GBP = p')
units.define('cent = 100 * EUR = c')	# Overwrite speed of light...

