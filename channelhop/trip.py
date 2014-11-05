from channelhop.money import Cost, Expense

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
		self._items = set()	# container for cost-like items.

	def add_expense(self, *args, **kwargs):
		("""Associate a new Expense instance with a person.""" +
		 '\n\n' + Expense.__init__.__doc__)
		self._items.add(Expense(self, *args, **kwargs))

	def add_cost(self, *args, **kwargs):
		("""Associate a new Cost instance with a person.""" +
		 '\n\n' + Cost.__init__.__doc__)
		self._items.add(Cost(*args, **kwargs))

	@property
	def balance(self):
		"""Balance of costs and expenses.

		+ve value represents an IOU.
		"""
		return sum(x._quantity for x in self._items)

	def bill(self):
		"""Human-readable itemised bill."""
		strings = [self.name] + map(str, self._items)
		strings.append('    BALANCE: {}'.format(self.balance))
		return '\n'.join(strings)
