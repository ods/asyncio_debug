import _asyncio
import asyncio.base_events
import asyncio.tasks
import ctypes
import inspect
import traceback


TaskWakeupMethWrapper = ctypes.cast(
    # The following doesn't work with dynamic symbols:
    # ctypes.pythonapi.TaskWakeupMethWrapper_Type,
    ctypes.pydll._dlltype(_asyncio.__file__).TaskWakeupMethWrapper_Type,
    ctypes.py_object
).value

PyObject_HEAD = [
    ('ob_refcnt', ctypes.c_size_t),
    ('ob_type', ctypes.c_void_p),
]

class TaskWakeupMethWrapper_Structure(ctypes.Structure):
    _fields_ = PyObject_HEAD + [
        ('ww_task', ctypes.py_object),
    ]


def unwrap_task_wakeup_method(wrapper: TaskWakeupMethWrapper):
    wrapper_p = ctypes.cast(
        ctypes.c_void_p(id(wrapper)),
        ctypes.POINTER(TaskWakeupMethWrapper_Structure),
    )
    return wrapper_p.contents.ww_task


def format_execution_point(coro):
    if asyncio.iscoroutine(coro):
        if inspect.iscoroutine(coro):
            t = 'coroutine'
            s = inspect.getcoroutinestate(coro)
            c = coro.cr_code
            f = coro.cr_frame
        else:
            t = 'generator'
            s = inspect.getgeneratorstate(coro)
            c = coro.gi_code
            f = coro.gi_frame
        ref = f'{c.co_filename}:{c.co_firstlineno}:{c.co_name}'
        if s.endswith('CLOSED'):
            return f'{t} {ref} just finished'
        elif s.endswith('SUSPENDED'):
            return f'{t} {ref} stopped at line {f.f_lineno}'
        else:
            assert False, f'Unexpected state {s} for {coro!r})'
    else:
        return f"(can't get execution point for {coro!r})"


def format_handle(handle):
    std_result = std_format_handle(handle)

    if handle._source_traceback is None:
        tb = '... (source traceback is not avalable)\n'
    else:
        tb = ''.join(traceback.format_list(handle._source_traceback))

    cb = handle._callback
    if isinstance(getattr(cb, '__self__', None), asyncio.tasks.Task):
        coro = cb.__self__._coro
    elif isinstance(cb, TaskWakeupMethWrapper):
        coro = unwrap_task_wakeup_method(cb)._coro
    else:
        coro = cb
    exe_point = format_execution_point(coro)

    return f'{std_result}\n{tb}... {exe_point}\n...'

std_format_handle = asyncio.base_events._format_handle
asyncio.base_events._format_handle = format_handle
