# SPDX-License-Identifier: BSD-2-Clause

# Copyright (c) 2026 Phil Thompson <phil@riverbankcomputing.com>


import pytest


cfg_package = 'extenders'


def test_core_callable(package, abi_package_version):
    # Older versions of the ABI do not support extending existing callables
    # with new overloads.
    if abi_package_version >= 14:
        twice_i = package.core_module.NameSpace.twice(5)

        assert isinstance(twice_i, int)
        assert twice_i == 10

def test_core_callable_docstrings(package, abi_package_version):
    # Older versions of the ABI do not support dynamic docstrings.
    if abi_package_version >= 14:
        assert len(package.core_module.NameSpace.twice.__doc__.split('\n')) == 2

def test_extended_overload(package):
    twice_f = package.core_module.NameSpace.twice(5.0)

    assert isinstance(twice_f, float)
    assert twice_f == 10.0

def test_extended_callable_or_overload(package, abi_package_version):
    # Older versions of the ABI do not support extending existing callables
    # with new overloads.
    if abi_package_version >= 14:
        thrice_i = package.core_module.NameSpace.thrice(5)

        assert isinstance(thrice_i, int)
        assert thrice_i == 15

        thrice_f = package.core_module.NameSpace.thrice(5.0)

        assert isinstance(thrice_f, float)
        assert thrice_f == 15.0

def test_extended_callable_or_overload_docstrings(package, abi_package_version):
    # Older versions of the ABI do not support dynamic docstrings.
    if abi_package_version >= 14:
        assert len(package.core_module.NameSpace.thrice.__doc__.split('\n')) == 2

def test_extended_attribute_get(package):
    assert package.core_module.NameSpace.in_extras1 == 33

def test_extended_attribute_set(package, abi_package_version):
    package.core_module.NameSpace.in_extras1 = 44
    assert package.core_module.NameSpace.in_extras1 == 44

    # For ABI v14 check the C++ value has changed and not the type dict.
    if abi_package_version >= 14:
        assert package.extras1_module.get_in_extras1() == 44

def test_extended_operator_overload(package):
    klass = package.core_module.Klass()
    klass.set_int_attr(10)

    assert klass + 2.0 == 12.0

def test_extended_operator(package, abi_package_version):
    # Older versions of the ABI do not support new slots in extensions.
    if abi_package_version >= 14:
        klass = package.core_module.Klass()
        klass.set_int_attr(10)

        assert klass * 2 == 20

def test_init_extender(package):
    cast = package.extras1_module.Cast(20)
    klass = package.core_module.Klass(cast)

    assert klass.get_int_attr() == 20

def test_init_extender_docstrings(package, abi_package_version):
    # Older versions of the ABI do not support dynamic docstrings.
    if abi_package_version >= 14:
        assert len(package.core_module.Klass.__doc__.split('\n')) == 3

def test_dir(package):
    assert 'thrice' in dir(package.core_module.NameSpace)


def test_wrapped_type_ids(package, abi_package_version):
    if abi_package_version < 14:
        pytest.skip("requires SIP ABI 14")

    type_id = package.sip._wrapped_type_id
    klass = package.core_module.Klass

    class Derived(klass):
        pass

    assert type_id(klass) == type_id(Derived)
    assert type_id(klass) != type_id(package.extras1_module.Cast)
    assert type_id(package.core_module.NameSpace.Kind) is not None
    assert type_id(package.core_module.NameSpace.Kind) != type_id(klass)
    assert type_id(int) is None
    with pytest.raises(TypeError):
        type_id(4)


@pytest.mark.parametrize("by_name", (False, True))
def test_imported_enum_scope(package, abi_package_version, by_name):
    if abi_package_version < 14:
        pytest.skip("requires SIP ABI 14")

    assert (package.extras1_module.scope_of_imported_enum(by_name)
            is package.core_module.NameSpace)


def test_python_subclass_event(package, abi_package_version):
    if abi_package_version < 14:
        pytest.skip("requires SIP ABI 14")

    klass = package.core_module.Klass
    assert not hasattr(klass, "_created_as_python_subclass")

    class Derived(klass):
        pass

    class DerivedAgain(Derived):
        pass

    assert Derived.__dict__["_created_as_python_subclass"] is True
    assert DerivedAgain.__dict__["_created_as_python_subclass"] is True


def test_optional_hook(package, abi_package_version, monkeypatch):
    if abi_package_version < 14:
        pytest.skip("requires SIP ABI 14")

    import builtins

    package.core_module.call_optional_hook()

    called = []
    monkeypatch.setattr(builtins, "_sip_test_optional_hook",
            lambda: called.append(True), raising=False)
    package.core_module.call_optional_hook()
    assert called == [True]

    def fail():
        raise RuntimeError("from the hook")

    monkeypatch.setattr(builtins, "_sip_test_optional_hook", fail)
    with pytest.raises(RuntimeError, match="from the hook"):
        package.core_module.call_optional_hook()


def test_handwritten_callable_preserves_exception(package, abi_package_version):
    if abi_package_version < 14:
        pytest.skip("requires SIP ABI 14")

    with pytest.raises(ValueError, match="handwritten error"):
        package.core_module.call_handwritten()
