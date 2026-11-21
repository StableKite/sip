import subprocess
import sys
import sysconfig

import pytest


cfg_enabled_for = (14,)


@pytest.mark.skipif(not sysconfig.get_config_var('Py_GIL_DISABLED'),
        reason='a free-threaded Python build is required')
def test_concurrent_wrapped_user_metadata(module):
    subprocess.run([sys.executable, '-I', '-S', '-c', '''
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys
from threading import Barrier

sys.path.insert(0, str(Path(sys.argv[1]).parent))
assert not sys._is_gil_enabled()
import user_metadata_module as wrapped
assert not sys._is_gil_enabled()
create = Barrier(8)

def wrap_value(index):
    create.wait(timeout=10)
    return wrapped.make_value(index)

with ThreadPoolExecutor(max_workers=8) as executor:
    values = list(executor.map(wrap_value, range(8)))
assert all(type(value) is wrapped.FactoryValue for value in values)
assert [value.value for value in values] == list(range(8))

instance = wrapped.Wrapper()
assert instance.data() is None
assert wrapped.type_data() is None
start = Barrier(8)

def exercise(owner):
    start.wait(timeout=10)
    for index in range(5000):
        instance.replace_data((owner, index))
        wrapped.replace_type_data((owner, index))
        for thread, counter in (instance.data(), wrapped.type_data()):
            assert 0 <= thread < 8
            assert 0 <= counter < 5000

with ThreadPoolExecutor(max_workers=8) as executor:
    list(executor.map(exercise, range(8)))
assert not sys._is_gil_enabled()
''', module.__file__], check=True, timeout=45)
