import asyncio
import time

import pytest

from frankensync import AwaitOrNot, frankensync, utils


def test_is_sync_caller_false():
    assert not utils.is_async_caller()


@pytest.mark.asyncio
async def test_is_async_caller_true():
    assert utils.is_async_caller()


@pytest.mark.asyncio
async def test_is_async_caller_true_with_stack_depth():
    def one():
        return utils.is_async_caller(stack_depth=1)
    def two():
        def inner():
            return utils.is_async_caller(stack_depth=2)
        return inner()

    assert one()
    assert two()

@pytest.mark.asyncio
async def test_is_async_caller_false_with_missing_stack_depth():
    def one():
        return utils.is_async_caller(stack_depth=0)
    def two():
        def inner():
            return utils.is_async_caller(stack_depth=0)
        return inner()

    assert not one()
    assert not two()

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
