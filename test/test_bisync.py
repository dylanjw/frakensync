import ast
import asyncio
import inspect

import pytest

"""
TODO work out "macro templates" for async/sync functions
    TODO How? Using dumb classes? Type annotation? Functions? Special syntax?

    e.g.:

        @bisync
        def fn():
            await_maybe(asyncio.sleep(), sleep())

    or

        @bisync
        def fn():
            with pacro.block(condition):
                '''execute code if condition is met'''

            # builds await syntax if necessary
            pacro.assignment(symbol, val or expression)

            # builds await syntax if necessary
            pacro.statement(val or expression)


    or an entirely new syntax

        @bisync
        def fn():
            pacro = '''

        ***special syntax for creating macros

            '''


TODO parse "macro templates" into coroutines or regular functions by rewriting ast.

"""

def bisync(fn):
    fn_src = inspect.getsource(fn)
    def wrapper(*args, **kwargs):
        fn_ast = ast.parse(fn_src)
        breakpoint()
    return wrapper


def get_caller():
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
    caller = get_caller()

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


@bisync
def is_sync_caller():
    if is_async_caller():
        return False
    return True


@bisync
async def is_async_caller_coro():
    if is_async_caller():
        await asyncio.sleep(0)
        return True
    return False


@pytest.mark.asyncio
async def test_dual_sleep_coro():
    assert(await is_async_caller_coro())


def test_dual_sleep_not_coro():
    assert(is_sync_caller())
