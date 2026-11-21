"""Exercise a generated ABI v14 binding in a fresh free-threaded interpreter."""

import subprocess
import sys
import sysconfig

import pytest


cfg_enabled_for = (14,)


@pytest.mark.skipif(not sysconfig.get_config_var('Py_GIL_DISABLED'),
        reason='requires free-threaded Python')
def test_concurrent_wrapper_calls(module):
    subprocess.run([sys.executable, '-I', '-S', '-c', '''
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys
from threading import Barrier

path = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(path.parent))
assert sys.flags.gil is None and not sys._is_gil_enabled()
import threading_module
assert Path(threading_module.__file__).resolve() == path
assert not sys._is_gil_enabled()

first_call = Barrier(8)

def create_value(index):
    first_call.wait(timeout=10)
    return threading_module.make_value(index)

with ThreadPoolExecutor(max_workers=8) as executor:
    wrappers = list(executor.map(create_value, range(8)))
assert all(type(wrapper) is threading_module.FactoryValue for wrapper in wrappers)
assert [wrapper.value() for wrapper in wrappers] == list(range(8))

shared = threading_module.Counter()
barrier = Barrier(8)

def exercise(_):
    own = threading_module.Counter()
    barrier.wait(timeout=10)
    results = []
    for expected in range(1000):
        assert own.next() == expected
        results.append(shared.next())
    return results

with ThreadPoolExecutor(max_workers=8) as executor:
    values = [value for group in executor.map(exercise, range(8)) for value in group]
assert sorted(values) == list(range(8000))

assert threading_module.get_counter_type_data() is None
threading_module.set_counter_type_data((0, 0))
barrier = Barrier(8)

def exercise_type_data(worker):
    barrier.wait(timeout=10)
    for index in range(5000):
        threading_module.set_counter_type_data((worker, index))
        owner, counter = threading_module.get_counter_type_data()
        assert 0 <= owner < 8
        assert 0 <= counter < 5000

with ThreadPoolExecutor(max_workers=8) as executor:
    list(executor.map(exercise_type_data, range(8)))
threading_module.set_counter_type_data(None)
assert threading_module.get_counter_type_data() is None
assert not sys._is_gil_enabled()
''', module.__file__], check=True, timeout=45)


def test_signed_python_size(module):
    class Indexable:
        def __index__(self):
            return -5

    for size in (-sys.maxsize - 1, -1, 0, sys.maxsize):
        assert module.identity_size(size) == size

    assert module.identity_size(Indexable()) == -5
    with pytest.raises(OverflowError):
        module.identity_size(sys.maxsize + 1)


def test_buffer_array_arguments(module):
    data = bytearray(b'ab\x00c')
    assert module.count_bytes(data) == 4
    info = module.ByteArrayInfo(data)
    assert (info.size(), info.last()) == (4, ord('c'))
    data.extend(b'd')
    with memoryview(data) as view:
        assert module.count_bytes(view) == 5

    assert module.count_bytes(None) == 0
    with pytest.raises(TypeError):
        module.count_bytes('not bytes')


def test_constructor_transfers_ownership_to_parent(module):
    parent = module.OwnershipProbe()
    child = module.OwnershipProbe(parent)
    assert module.ispyowned(parent)
    try:
        assert not module.ispyowned(child)
    finally:
        module.transferback(child)
