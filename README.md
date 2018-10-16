# asyncio debugging patch

This patch enriches information printed for slow callbacks by asyncio in [debug mode](https://docs.python.org/3/library/asyncio-dev.html#debug-mode).  Output without patch:

```
Executing <Task pending coro=<bad() running at example.py:7> wait_for=<Future pending cb=[<TaskWakeupMethWrapper object at 0x7f8bd5abb828>()] created at /usr/lib/python3.6/asyncio/base_events.py:276> cb=[_run_until_complete_cb() at /usr/lib/python3.6/asyncio/base_events.py:177] created at /usr/lib/python3.6/asyncio/base_events.py:447> took 1.002 seconds
```

Output with patch:

```
Executing <Task pending coro=<bad() running at example.py:7> wait_for=<Future pending cb=[<TaskWakeupMethWrapper object at 0x7f8bd55684f8>()] created at /usr/lib/python3.6/asyncio/base_events.py:276> cb=[_run_until_complete_cb() at /usr/lib/python3.6/asyncio/base_events.py:177] created at /usr/lib/python3.6/asyncio/base_events.py:447>
  File "example.py", line 15, in <module>
    loop.run_until_complete(bad())
  File "/usr/lib/python3.6/asyncio/base_events.py", line 447, in run_until_complete
    future = tasks.ensure_future(future, loop=self)
  File "/usr/lib/python3.6/asyncio/tasks.py", line 519, in ensure_future
    task = loop.create_task(coro_or_future)
  File "/usr/lib/python3.6/asyncio/base_events.py", line 285, in create_task
    task = tasks.Task(coro, loop=self)
... coroutine example.py:5:bad stopped at line 7
... took 1.002 seconds
```

Additional information printed by the patch is:

* traceback pointing where the problematic coroutine was created at,
* the place where coroutine was suspended just after slow callback (first await after it or the end of coroutine).

## Installation

```
pip install git+https://github.com/ods/asyncio_debug.git
```

## Usage

To enable patch just import it:

```
import asyncio_debug_patch
```

The patch works for default asyncio event loop implementation.  In case you are using other implementation like `uvloop` switch to devault loop when debugging is enabled:

```
if asyncio.coroutines._is_debug_mode():
    import asyncio_debug_patch
    loop_policy = asyncio.DefaultEventLoopPolicy()
else:
    loop_policy = uvloop.EventLoopPolicy()
asyncio.set_event_loop_policy(loop_policy)
```