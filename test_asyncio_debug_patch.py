import asyncio
from collections import namedtuple
from inspect import currentframe, getframeinfo
import time

import pytest

import asyncio_debug_patch


SLOW_DURATION = 0.01


@pytest.fixture
def loop():
    loop = asyncio.new_event_loop()
    loop.set_debug(True)
    loop.slow_callback_duration = SLOW_DURATION
    yield loop
    loop.close()


ParsedLogRecord = namedtuple(
    'ParsedLogRecord',
    ['summary', 'traceback', 'exe_point', 'took'],
)

def parse_debug_message(record):
    lines = record.message.split('\n')
    assert len(lines) >= 4
    summary, *traceback, exe_point, took = lines

    assert summary.startswith('Executing ')

    if len(traceback) == 1:
        assert traceback[0] == '... (source traceback is not avalable)'
    else:
        assert not len(traceback) % 2
        it = iter(traceback)
        for ref, source in zip(it, it):
            assert ref.startswith('  File ')
            assert source.startswith('    ')

    assert exe_point.startswith('... ')
    assert took.startswith('... took')
    return ParsedLogRecord(summary, traceback, exe_point, took)


# --- Task samples ---

async def in_executor(loop):
    await loop.run_in_executor(None, time.sleep, SLOW_DURATION)

async def asyncdef_finished():
    time.sleep(SLOW_DURATION)

async def asyncdef_suspended():
    time.sleep(SLOW_DURATION)
    # Switch point is just before await
    lineno = getframeinfo(currentframe()).lineno; await asyncio.sleep(0)
    return lineno

@asyncio.coroutine
def generator_finished():
    yield
    time.sleep(SLOW_DURATION)

@asyncio.coroutine
def generator_suspended():
    time.sleep(SLOW_DURATION)
    # Switch point is just before yield
    lineno = getframeinfo(currentframe()).lineno; yield
    return lineno


# --- Tests ---

def test_no_source_traceback(loop, caplog):
    """Cases with no traceback are handled properly"""
    loop.slow_callback_duration = 0  # Force logging every callback
    loop.run_until_complete(in_executor(loop))  # Must not fail
    map(parse_debug_message, caplog.records)


@pytest.mark.parametrize(
    'coro_func', [asyncdef_finished, generator_finished],
)
def test_source_traceback(loop, caplog, coro_func):
    """Chack that source traceback contains line it was started from"""
    # Must be in one line to work properly
    loop.run_until_complete(coro_func()); fi = getframeinfo(currentframe())

    [record] = caplog.records
    pr = parse_debug_message(record)
    line = f'  File "{fi.filename}", line {fi.lineno}, in {fi.function}'
    assert line in pr.traceback


@pytest.mark.parametrize(
    'coro_func', [asyncdef_finished, generator_finished],
)
def test_finished_state(loop, caplog, coro_func):
    loop.run_until_complete(coro_func())
    [record] = caplog.records
    pr = parse_debug_message(record)
    assert coro_func.__name__ in pr.exe_point
    assert 'finished' in pr.exe_point


@pytest.mark.parametrize(
    'coro_func', [asyncdef_suspended, generator_suspended],
)
def test_suspended_state(loop, caplog, coro_func):
    lineno = loop.run_until_complete(coro_func())
    [record] = caplog.records
    pr = parse_debug_message(record)
    assert coro_func.__name__ in pr.exe_point
    assert f'stopped at line {lineno}' in pr.exe_point

if __name__ == '__main__':
    pytest.main()
