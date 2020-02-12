import asyncio
import time

import pytest

from frankensync import AwaitOrNot, frankensync, utils


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
