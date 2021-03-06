from channelhop.money import Cost

class Person(object):
	"""A trip participant.

	People:

	  - are present for some or all of the trip.
	  - are responsible for a share of costs incurred.
	  - may incur expenses (e.g. paying up front for fuel).
	  - start off with no costs/expenses assigned.
	"""
	def __init__(self, name):
		"""Instantiate a person with a unique name."""
		self.name = name
		self._bill = list()

	@property
	def bill(self):
		"""List of Cost instances."""
		return self._bill

	def prettify_bill(self):
		"""Return a human-readable, itemised bill as a string."""
		strings = [self.name] + map(str, self._bill)
		strings.append('            |')
		strings.append('{:>7.2f} | TOTAL'.format(self.balance()))
		return '\n'.join(strings)

	def add_expense(self, description, amount, currency='GBP'):
		"""Associate an incurred expense with the person.

		Stores a Cost instance in the `bill` attribute and returns it.
		Expenses, with respect to the person, are outgoings and
		therefore represented with negative values; positive values
		will be converted.

		Arguments
		---------

			description : descriptive string
			amount : numerical value in a base currency (float, int)
			currency : 3 letter string (optional, default: 'GBP')
		"""
		# Create the Cost object and return it.
		return Cost(description, -1*abs(amount), currency, self)

	def add_cost(self, description, amount, currency='GBP'):
		"""Associate a cost with the person.

		Stores a Cost instance in the `bill` attribute and returns it.
		Costs are projected, unincurred expenses and represented with
		positive values; negative values will be converted.

		Arguments
		---------

			description : descriptive string
			amount : numerical value in a base currency (float, int)
			currency : 3 letter string (optional, default: 'GBP')
		"""
		# Create the Cost object and return it.
		return Cost(description, abs(amount), currency, self)

	def balance(self):
		"""Balance of costs and expenses in GBP.

		Positive values represent underpayment, negative overpayment.
		"""
		# FIXME: Currency is hardcoded here.
		return sum(self.bill).to('GBP')
