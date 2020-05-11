import functools


def cases(cases, count={}):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args):
            for c in cases:
                new_args = args + (c,)
                try:
                    f(*new_args)
                except Exception as er:
                    count[f.__name__] = c.__repr__()
                    print('{}. function failure {}  at value {}'.format(len(count),
                                                                        f.__name__,
                                                                        count[f.__name__]))
                    raise er
        return wrapper
    return decorator


