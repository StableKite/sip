# SPDX-License-Identifier: BSD-2-Clause

from types import SimpleNamespace

import pytest

from sipbuild import buildable


@pytest.mark.parametrize('free_threaded, gil_disabled, version, limited, abi3t', [
    (False, False, (3, 8, 0), True, False),
    (True, False, (3, 8, 0), False, False),
    (True, False, (3, 15, 0), False, False),
    (True, True, (3, 14, 0), False, False),
    (True, True, (3, 15, 0), True, True),
])
def test_select_compatible_abi(tmp_path, monkeypatch, free_threaded,
                              gil_disabled, version, limited, abi3t):
    monkeypatch.setattr(buildable.sysconfig, 'get_config_var',
                        lambda name: free_threaded if name == 'Py_GIL_DISABLED' else None)
    project = SimpleNamespace(build_dir=tmp_path, sip_module='test.sip',
                              limited_abi_version=version)
    native = buildable.BuildableModule(
            project, 'fixture', 'test.fixture', uses_limited_api=True,
            gil_disabled=gil_disabled)
    assert native.uses_limited_api is limited
    assert any(m.startswith('Py_LIMITED_API=') for m in native.define_macros) is limited
    assert any(m.startswith('Py_TARGET_ABI3T=') for m in native.define_macros) is abi3t
