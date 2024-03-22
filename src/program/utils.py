import functools

__all__ = ["first"]

first = functools.partial(next, default=None)
