import asyncio
import pytest
import time

import asyncio_debug_patch


@pytest.fixture
def loop():
    loop = asyncio.new_event_loop()
    loop.set_debug(True)
    yield loop
    loop.close()

async def in_executor(loop):
    await loop.run_in_executor(None, time.sleep, 0.1)


def test_no_traceback(loop, caplog):
    """Cases with no traceback are handled properly"""
    loop.slow_callback_duration = 0  # Force logging every callback
    loop.run_until_complete(in_executor(loop))  # Must not fail


if __name__ == '__main__':
    pytest.main()
