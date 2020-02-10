import asyncio
import time

import pytest

from pacro import BisyncOption, bisync, utils


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

    or write code with await keyword that can be converted to native sync code!
        from pacro import (bisync, BisyncOption)
        @bisync
        async def fn():
            await BisyncOption(
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


@bisync(namespace=[time])
async def bisleep():
    await BisyncOption(
        awaitable=asyncio.sleep(0),
        sync_fallback=time.sleep(0),
    )
    return "success"


def test_bisleep_sync():
    assert bisleep() == "success"


async def test_bisleep_async():
    ret = await bisleep()
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
