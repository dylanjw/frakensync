import inspect

from toolz import complement, curry


def repeatedly(fn, val, repeat):
    if repeat == 0:
        return val
    val = fn(val)
    return repeatedly(fn , val, repeat - 1)


@curry
def lefthanded_getattr(name, obj):
    return getattr(obj, name)


def repeatedly_getattr(obj, attr, repeat=1):
    return repeatedly(
        lefthanded_getattr(attr),
        obj,
        repeat
    )


def _get_caller(stack_depth=0):
    """Figure out who's calling."""

    _stack_depth = stack_depth + 2  # get out of current frames
    # Get the calling frame

    frame = repeatedly_getattr(
        obj = inspect.currentframe(),
        attr = "f_back",
        repeat = _stack_depth)


    # Pull the function name from FrameInfo
    caller_name = inspect.getframeinfo(frame)[2]

    # Get the function object
    caller = frame.f_locals.get(
        caller_name,
        frame.f_globals.get(caller_name)
    )
    return caller


def is_async_caller(stack_depth=0):
    caller = _get_caller(stack_depth)

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


def unwrap_name_fn(name):
    def inner(object):
        return getattr(object, name)

    return inner


def is_frankensync_ast(ast_obj):
    if (hasattr_recursive(ast_obj, 'func', 'id') and
            ast_obj.func.id == 'frankensync'):
        return True
    return False


not_frankensync_ast = complement(is_frankensync_ast)
