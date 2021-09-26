# Prevents certain properties from having to be recomputed each time they
# are referenced


def lazy(f):

	def wrapper(*args, **kwargs):

		o = args[0]

		if "_lazy" not in o.__dict__: o.__dict__["_lazy"] = {}

		if f.__name__ not in o.__dict__["_lazy"]: o.__dict__["_lazy"][f.__name__] = f(*args, **kwargs)

		return o.__dict__["_lazy"][f.__name__]

	wrapper.__name__ = f.__name__
	return wrapper
