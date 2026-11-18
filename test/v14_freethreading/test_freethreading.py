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
assert not sys._is_gil_enabled()
''', module.__file__], check=True, timeout=45)
