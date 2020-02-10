import inspect


def _get_caller():
    """Figure out who's calling."""
    # Get the calling frame
    frame = inspect.currentframe().f_back.f_back

    # Pull the function name from FrameInfo
    caller_name = inspect.getframeinfo(frame)[2]

    # Get the function object
    caller = frame.f_locals.get(
        caller_name,
        frame.f_globals.get(caller_name)
    )
    return caller


def is_async_caller():
    caller = _get_caller()

    # If there's any indication that the function object is a
    # coroutine, return True. inspect.iscoroutinefunction() should
    # be all we need, the rest are here to illustrate.
    if any([inspect.iscoroutinefunction(caller),
            inspect.isgeneratorfunction(caller),
            inspect.iscoroutine(caller), inspect.isawaitable(caller),
            inspect.isasyncgenfunction(caller), inspect.isasyncgen(caller)]):
        return True
    else:
        return False


def hasattr_recursive(obj, *names):
    if not hasattr(obj, names[0]):
        return False
    elif len(names) > 1:
        return hasattr_recursive(getattr(obj, names[0]), *names[1:])

    return True
