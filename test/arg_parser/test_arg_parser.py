# SPDX-License-Identifier: BSD-2-Clause

# Copyright (c) 2026 Phil Thompson <phil@riverbankcomputing.com>


import builtins

import pytest


def test_ctor_with_transfer_arg(module):
    owned = module.OwnedClass()
    assert module.ispyowned(owned)

    klass = module.Klass(owned)
    assert not module.ispyowned(owned)

def test_static_callable_from_type(module):
    module.Klass.set_static(10)
    assert module.Klass.get_static() == 10

def test_static_callable_from_instance(module):
    klass = module.Klass()

    klass.set_static(20)
    assert klass.get_static() == 20

def test_bound_callable(module):
    klass = module.Klass()

    klass.set_inst(10)
    assert klass.get_inst() == 10

def test_unbound_callable(module):
    klass = module.Klass()

    module.Klass.set_inst(klass, 20)
    assert module.Klass.get_inst(klass) == 20

def test_protected_bound_callable(module):
    klass = module.Klass()

    klass.set_prot_inst(10)
    assert klass.get_prot_inst() == 10

def test_protected_unbound_callable(module):
    klass = module.Klass()

    module.Klass.set_prot_inst(klass, 20)
    assert module.Klass.get_prot_inst(klass) == 20


def test_byte_array_length(module):
    assert module.sum_bytes(b"") == 0
    assert module.sum_bytes(bytes([0, 128, 255])) == 383


def test_signed_size(request, module):
    if request.config.getoption("sip_abi_version") < 14:
        pytest.skip("Py_ssize_t argument parsing requires ABI 14")
    assert module.echo_size(-57) == -57


def test_nonconsecutive_keyword_arguments(module):
    assert module.encode_options(1, units=7) == 127
    assert module.encode_options(units=7, base=1) == 127
    assert module.encode_options(1, units=7, tens=8) == 187
    with pytest.raises(TypeError):
        module.encode_options(units=7, tens=8)
    with pytest.raises(TypeError):
        module.encode_options(1, 2, tens=8)


def test_encoded_strings_and_characters(module):
    assert module.encoded_length("hello") == 5
    assert module.encoded_length(b"bytes") == 5
    assert module.encoded_length(None) == -1
    assert module.latin1_length("\u00e9") == 1
    assert module.utf8_length("\u00e9") == 2
    assert module.encoded_byte("A") == b"A"
    with pytest.raises(UnicodeEncodeError):
        module.encoded_length("\u00e9")


def test_optional_post_hook(module, monkeypatch):
    assert module.echo_size_with_hook(1) == 1
    calls = []
    monkeypatch.setattr(builtins, "_sip_test_optional_hook",
            lambda: calls.append(True), raising=False)
    assert module.echo_size_with_hook(2) == 2
    assert calls == [True]


def test_reflected_overloads(module):
    operand = module.Operand(6)
    assert 3 * operand == 18
    assert 0.5 * operand == 3


def test_global_matrix_multiply_alias(module):
    lhs, rhs = module.Operand(6), module.Operand(7)
    assert lhs * rhs == 42
    assert lhs @ rhs == 42


def test_argument_wrapper(module):
    owner = module.OwnedClass()
    assert module.get_argument_wrapper(owner) is owner


def test_wrap_factory_only_class(module):
    with pytest.raises(TypeError):
        module.FactoryOnly()

    wrapped = module.make_factory_only()
    assert isinstance(wrapped, module.FactoryOnly)
    assert wrapped.value() == 42
