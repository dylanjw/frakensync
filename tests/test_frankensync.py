import asyncio
import time

import pytest

from frankensync import AwaitOrNot, frankensync, utils


"""
TODO work out "macro templates" for async/sync functions
    TODO How? Using dumb classes? Type annotation? Functions? Special syntax?

    e.g.:

        @frankensync
        def fn():
            await_maybe(asyncio.sleep(), sleep())

    or

        @frankensync
        def fn():
            with frankensync.block(condition):
                '''execute code if condition is met'''

            # builds await syntax if necessary
            frankensync.assignment(symbol, val or expression)

            # builds await syntax if necessary
            frankensync.statement(val or expression)


    or an entirely new syntax

        @frankensync
        def fn():
            frankensync = '''

        ***special syntax for creating macros

            '''

    or write code with await keyword that can be converted to native sync code!
        from frankensync import (frankensync, AwaitOrNot)
        @frankensync
        async def fn():
            await AwaitOrNot(
                awaitable = asyncio.sleep(5),
                sync_fallback = sleep(5)
            )



TODO parse "macro templates" into coroutines or regular functions by rewriting ast.

"""


def function():
    time.sleep(5)


def is_sync_caller():
    if utils.is_async_caller():
        return False
    return True


async def is_async_caller_coro():
    if utils.is_async_caller():
        await asyncio.sleep(0)
        return True
    return False


@pytest.mark.asyncio
async def test_dual_sleep_coro():
    assert(await is_async_caller_coro())


def test_dual_sleep_not_coro():
    assert(is_sync_caller())


@frankensync(namespace=(time, asyncio))
async def frankensleep():
    await AwaitOrNot(
        awaitable=asyncio.sleep(0),
        sync_fallback=time.sleep(0),
    )
    return "success"


def test_frankensleep_sync():
    assert frankensleep() == "success"

@pytest.mark.asyncio
async def test_frankensleep_async():
    ret = await frankensleep()
    assert ret == "success"


def test_hasattr_recursive():
    class Bushel:
        amount = None

    class Apples:
        unit = Bushel

    class Cargo:
        fruit = Apples

    assert utils.hasattr_recursive(Cargo(), 'fruit', 'unit', 'amount')
    assert not utils.hasattr_recursive(Cargo(), 'unit', 'amount')
