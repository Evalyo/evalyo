from django_jinja.library import render_with

global_functions = {}
tests = {}
filters = {}
extensions = []

__all__ = ["render_with", "function", "jinja_filter", "test", "extension"]


def _store_function(store, func, name=None):
    if name is None:
        name = func.__name__
    store[name] = func


def _register_function(store, name, func):
    if name is None and func is None:

        def decorator(func):
            _store_function(store, func)
            return func

        return decorator
    if name is not None and func is None:
        if callable(name):
            _store_function(store, name)
            return name

        def decorator(func):
            _store_function(store, func, name)
            return func

        return decorator
    _store_function(store, func, name)
    return func


def jinja_filter(name=None, func=None):
    return _register_function(filters, name, func)


def function(name=None, func=None):
    return _register_function(global_functions, name, func)


def test(name=None, func=None):
    return _register_function(tests, name, func)


def extension(cls):
    extensions.append(cls)
    return cls
