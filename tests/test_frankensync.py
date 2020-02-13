import asyncio
import time

import pytest

from frankensync import AwaitOrNot, frankensync, utils


@frankensync
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


@frankensync
async def await_on_frankensleep():
    await frankensleep()
    return True


@pytest.mark.asyncio
async def test_chaining_frankensync_defs_async_context():
    assert await await_on_frankensleep()


def test_chaining_frankensync_defs_sync_context():
    assert await_on_frankensleep()
