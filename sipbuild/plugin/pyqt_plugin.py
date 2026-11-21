# SPDX-License-Identifier: BSD-2-Clause

# Copyright (c) 2026 Phil Thompson <phil@riverbankcomputing.com>


from enum import auto, Enum

from .annotations import AnnotationContext, AnnotationType
from .plugin import Plugin


class PyQtPlugin(Plugin):
    """ This implements the PyQt plugin.  It is a stepping stone for removing
    all of SIP's PyQt-specific support.  It will be moved to PyQt-Builder in
    SIP v7.
    """

    # The string that uniquely identifies the plugin.
    sip_key = 'pyqt'

    def __init__(self, pyqt_major_version=0):
        """ Initialise the plugin. """

        super().__init__()

        # When this is moved to PyQt-builder v2 the version number will always
        # be explicitly passed and won't need a default value.
        self.pyqt_major_version = pyqt_major_version

    def get_class_flags(self, klass):
        """ Return the /PyQtFlags/ (PyQt5 only) of a class. """

        return klass.get_plugin_attribute(self, 'flags', 0)

    def get_class_flags_enums(self, klass):
        """ Return the /PyQtFlagsEnums/ (PyQt5 only) of a class. """

        return klass.get_plugin_attribute(self, 'flags_enums')

    def get_interface(self, klass):
        """ Return the /PyQtInterface/ of a class. """

        return klass.get_plugin_attribute(self, 'interface')

    def get_mapped_type_flags(self, mapped_type):
        """ Return the /PyQtFlags/ (PyQt6 only) of a mapped type. """

        return mapped_type.get_plugin_attribute(self, 'flags', 0)

    def get_no_qmetaobject(self, klass):
        """ Return the /PyQtNoQMetaObject/ of a class. """

        return klass.get_plugin_attribute(self, 'no_qmetaobject', False)

    def get_scopes_stripped(self, arg):
        """ Return the /ScopesStripped/ of an argument. """

        return arg.get_plugin_attribute(self, 'scopes_stripped', 0)

    def is_qobject(self, klass):
        """ Return True if a class is or inherits QObject. """

        return klass.get_plugin_attribute(self, 'is_qobject', False)

    def is_signal(self, overload):
        """ Return True if a function is a Qt signal. """

        return overload.get_plugin_attribute(self, 'method_type', None) is PyQtMethodType.SIGNAL

    def is_slot(self, overload):
        """ Return True if a function is a Qt slot. """

        return overload.get_plugin_attribute(self, 'method_type', None) is PyQtMethodType.SLOT

    def sip_class_generate_derived_class_decl(self, writer, spec, klass):
        """ Generate code to be included in the declaration of a class's
        derived class.  By default this will be placed in a private section.
        """

        # This test can go when we are moved to PyQt-builder.
        if self.pyqt_major_version == 0:
            return

        if not self.is_qobject(klass):
            return

        writer.write(
'''
public:
    int qt_metacall(QMetaObject::Call, int, void **) SIP_OVERRIDE;
    void *qt_metacast(const char *) SIP_OVERRIDE;
''')

        if not self.get_no_qmetaobject(klass):
            writer.write('    const QMetaObject *metaObject() const SIP_OVERRIDE;\n')

    def sip_class_generate_derived_class_impl(self, writer, spec, klass):
        """ Generate code to be included in the implementation of a class's
        derived class.
        """

        # This test can go when we are moved to PyQt-builder.
        if self.pyqt_major_version == 0:
            return

        if not self.is_qobject(klass):
            return

        module_name = spec.module_name
        klass_name = klass.cpp_name
        klass_name_as_word = klass.cpp_name_as_word
        type_spec = spec.get_type_specification(klass)

        if spec.abi_major_version >= 14 and self.pyqt_major_version == 6:
            self._g_abi14_qobject_impl(writer, klass, type_spec)
            return

        if not self.get_no_qmetaobject(klass):
            writer.write(
f'''
const QMetaObject *sip{klass_name_as_word}::metaObject() const
{{
    if (sipGetInterpreter())
        return QObject::d_ptr->metaObject ? QObject::d_ptr->dynamicMetaObject() : sip_{module_name}_qt_metaobject(sipPySelf, {type_spec});

    return {klass_name}::metaObject();
}}
''')

        writer.write(
f'''
int sip{klass_name_as_word}::qt_metacall(QMetaObject::Call _c, int _id, void **_a)
{{
    _id = {klass_name}::qt_metacall(_c, _id, _a);

    if (_id >= 0)
    {{
        SIP_BLOCK_THREADS
        _id = sip_{module_name}_qt_metacall(sipPySelf, {type_spec}, _c, _id, _a);
        SIP_UNBLOCK_THREADS
    }}

    return _id;
}}

void *sip{klass_name_as_word}::qt_metacast(const char *_clname)
{{
    void *sipCpp;

    return (sip_{module_name}_qt_metacast(sipPySelf, {type_spec}, _clname, &sipCpp) ? sipCpp : {klass_name}::qt_metacast(_clname));
}}
''')

    def _g_abi14_qobject_impl(self, writer, klass, type_spec):
        name = klass.cpp_name_as_word
        cpp = klass.cpp_name

        if not self.get_no_qmetaobject(klass):
            writer.write(
f"""
const QMetaObject *sip{name}::metaObject() const
{{
    const QMetaObject *native = {cpp}::metaObject();
    if (native != &{cpp}::staticMetaObject)
        return native;

    sipQtCallback callback(sipMS,
            const_cast<{cpp} *>(static_cast<const {cpp} *>(this)), {type_spec});
    if (auto *wrapper = callback.wrapper())
        if (auto handler = reinterpret_cast<sip_qt_metaobject_func>(
                sipImportSymbol("qtcore_qt_metaobject")))
            if (const QMetaObject *meta = handler(sipMS, wrapper, {type_spec}))
                return meta;

    return native;
}}
""")

        writer.write(
f"""
int sip{name}::qt_metacall(QMetaObject::Call call, int id, void **args)
{{
    id = {cpp}::qt_metacall(call, id, args);
    if (id >= 0)
    {{
        sipQtCallback callback(sipMS, static_cast<{cpp} *>(this), {type_spec});
        if (auto *wrapper = callback.wrapper())
            if (auto handler = reinterpret_cast<sip_qt_metacall_func>(
                    sipImportSymbol("qtcore_qt_metacall")))
                id = handler(sipMS, wrapper, {type_spec}, call, id, args);
    }}

    return id;
}}

void *sip{name}::qt_metacast(const char *name)
{{
    {{
        sipQtCallback callback(sipMS, static_cast<{cpp} *>(this), {type_spec});
        if (auto *wrapper = callback.wrapper())
            if (auto handler = reinterpret_cast<sip_qt_metacast_func>(
                    sipImportSymbol("qtcore_qt_metacast")))
            {{
                void *cpp = nullptr;
                if (handler(sipMS, wrapper, {type_spec}, name, &cpp))
                    return cpp;
            }}
    }}

    return {cpp}::qt_metacast(name);
}}
""")

    def sip_class_generate_impl(self, writer, spec, klass):
        """ Generate code that implements support for a class, usually in the
        form of a type-specific data structure.  The name of the data structure
        should be returned.
        """

        # This test can go when we are moved to PyQt-builder.
        if self.pyqt_major_version == 0:
            return None

        is_qobject = self.is_qobject(klass)

        if is_qobject:
            is_signals = self._g_signals_table(writer, spec, klass)
            is_qmetaobject = not self.get_no_qmetaobject(klass)
        else:
            is_signals = is_qmetaobject = False

        interface = self.get_interface(klass)

        # The PyQt6 support code doesn't assume the structure is generated.
        if self.pyqt_major_version == 6:
            generated = is_signals or is_qmetaobject or interface is not None
            if not generated:
                return None

        klass_name = klass.cpp_name
        klass_name_as_word = klass.cpp_name_as_word
        plugin_name = 'plugin_' + klass_name_as_word

        const = 'const ' if spec.abi_major_version >= 14 else ''
        writer.write(f'\n\nstatic {const}pyqt{self.pyqt_major_version}ClassPluginDef {plugin_name} = {{\n')

        mo_ref = f'&{klass_name}::staticMetaObject' if is_qmetaobject else 'SIP_NULLPTR'
        writer.write(f'    {mo_ref},\n')

        if self.pyqt_major_version == 5:
            pyqt5_flags = self.get_class_flags(klass)
            writer.write(f'    {pyqt5_flags},\n')

        signals_ref = f'signals_{klass_name_as_word}' if is_signals else 'SIP_NULLPTR'
        writer.write(f'    {signals_ref},\n')

        interface_ref = f'"{interface}"' if interface is not None else 'SIP_NULLPTR'
        writer.write(f'    {interface_ref}\n')

        writer.write('};\n')

        return plugin_name

    def sip_class_generate_release_code(self, writer, spec, klass):
        """ Generate the body of a class's release function.  True is returned
        if the plugin generated something to replace the default
        implementation.
        """

        # This test can go when we are moved to PyQt-builder.
        if self.pyqt_major_version == 0:
            return False

        if not self.is_qobject(klass) or not klass.dtor_is_public:
            return False

        # QObjects should only be deleted in the threads that they belong to.
        writer.write(
'''    if (QThread::currentThread() == sipCpp->thread())
        delete sipCpp;
    else
        sipCpp->deleteLater();
''')

        return True

    @staticmethod
    def sip_class_get_access_specifiers(spec):
        """ Return a sequence of non-standard strings that can appear in a
        plugin-specific access specifier.
        """

        return ('signals', 'slots', 'Q_SIGNALS', 'Q_SLOTS')

    def sip_class_parsed(self, spec, scope, klass):
        """ Invoked when a class has been parsed. """

        # Mark any QObject class.  This flag will ripple through all
        # sub-classes when the hierarchy is set.
        if klass.unscoped_cpp_name == 'QObject':
            self._set_qobject(klass)

    def sip_class_superclass_set(self, spec, klass, superclass):
        """ Invoked when a class's superclass has been set. """

        if self.is_qobject(superclass):
            self._set_qobject(klass)

    def sip_handle_access_specifier(self, spec, klass, primary, secondary):
        """ Parse a primary and optional secondary class access specifier.  If
        it was parsed return the C++ standard access specifier (ie. 'public',
        'protected' or 'private') to use, otherwise return None.
        """

        # This test can go when we are moved to PyQt-builder.
        if self.pyqt_major_version == 0:
            return None

        if primary in ('signals', 'Q_SIGNALS') and secondary is None:
            method_type = PyQtMethodType.SIGNAL
            primary = 'public'
        elif primary in ('public', 'protected', 'private') and secondary in ('slots', 'Q_SLOTS'):
            method_type = PyQtMethodType.SLOT
        else:
            method_type = None
            primary = None

        klass.set_plugin_attribute(self, 'method_type', method_type)

        return primary

    def sip_handle_annotations(self, spec, item, annotations,
            annotation_context):
        """ Handle any context-specific annotations. """

        # This test can go when we are moved to PyQt-builder.
        if self.pyqt_major_version == 0:
            return

        if annotation_context is AnnotationContext.ARGUMENT:
            # Note that this should have a 'PyQt' prefix.
            scopes_stripped = spec.parse_annotation(annotations,
                    'ScopesStripped', AnnotationType.INTEGER)

            if scopes_stripped is not None:
                if scopes_stripped > 0:
                    item.set_plugin_attribute(self, 'scopes_stripped',
                            scopes_stripped)
                else:
                    spec.error("/ScopesStripped/ must be greater than 0",
                            annotation='ScopesStripped')

        elif annotation_context is AnnotationContext.CLASS:
            if self.pyqt_major_version == 5:
                flags = spec.parse_annotation(annotations, 'PyQtFlags',
                        AnnotationType.INTEGER)

                if flags is not None:
                    item.set_plugin_attribute(self, 'flags', flags)

                flags_enums = spec.parse_annotation(annotations,
                        'PyQtFlagsEnums', AnnotationType.STRING_LIST)

                if flags_enums is not None:
                    item.set_plugin_attribute(self, 'flags_enums', flags_enums)
                    item.set_plugin_attribute(self, 'flags', 1)

            item.set_plugin_attribute(self, 'interface',
                    spec.parse_annotation(annotations, 'PyQtInterface',
                            AnnotationType.STRING))

            item.set_plugin_attribute(self, 'no_qmetaobject',
                    spec.parse_annotation(annotations, 'PyQtNoQMetaObject',
                            AnnotationType.BOOLEAN))

        elif annotation_context is AnnotationContext.MAPPED_TYPE:
            if self.pyqt_major_version == 6:
                flags = spec.parse_annotation(annotations, 'PyQtFlags',
                        AnnotationType.INTEGER)

                if flags is not None:
                    item.set_plugin_attribute(self, 'flags', flags)

    def sip_handle_overload_prefix(self, spec, scope, overload, prefix):
        """ Invoked to handle a class function prefix.  Return True if the
        prefix was handled.
        """

        # This test can go when we are moved to PyQt-builder.
        if self.pyqt_major_version == 0:
            return False

        if prefix == 'Q_SIGNAL':
            overload.set_plugin_attribute(self, 'pyqt_method_type',
                    PyQtMethodType.SIGNAL)
        elif prefix == 'Q_SLOT':
            overload.set_plugin_attribute(self, 'pyqt_method_type',
                    PyQtMethodType.SLOT)
        else:
            return False

        if not spec.is_class(scope):
            spec.error(context, f"'{prefix}' may only be specified in a class")
            return False

        return True

    def sip_handle_directive(self, spec, name, args):
        """ Invoked to handle a directive.  Return True if the directive was
        handled.
        """

        # Handle the %Plugin directive.
        if name != 'Plugin':
            return False

        nr_args = len(args)

        if nr_args != 1:
            spec.error(f"%Plugin takes 1 argument but {nr_args} given")

        plugin_name = args[0]

        if plugin_name == 'PyQt6':
            self.pyqt_major_version = 6
        elif plugin_name == 'PyQt5':
            self.pyqt_major_version = 5
        else:
            spec.error(f"%Plugin given unknown plugin name '{plugin_name}'")

        return True

    def sip_instantiated_class_resolved(self, spec, klass, template_class,
            template_arguments):
        """ Invoked when a class created by instantiating a template with
        arguments has been resolved.
        """

        pyqt5_flags_enums = self.get_class_flags_enums(template_class)

        if pyqt5_flags_enums is not None:
            self._set_class_flags_enums(klass, [
                    spec.apply_template_arguments(s, template_arguments)
                    for s in pyqt5_flags_enums])

    def sip_instantiated_mapped_type_resolved(self, spec, mapped_type,
            template_mapped_type, template_arguments):
        """ Invoked when a mapped type created by instantiating a template with
        arguments has been resolved.
        """

        pyqt6_flags = self.get_mapped_type_flags(template_mapped_type)

        if pyqt6_flags is not None:
            self._set_mapped_type_flags(mapped_type, pyqt6_flags)

    def sip_mapped_type_generate_impl(self, writer, spec, mapped_type):
        """ Generate code that implements support for a mapped type. """

        # This test can go when we are moved to PyQt-builder.
        if self.pyqt_major_version == 0:
            return None

        pyqt6_flags = self.get_mapped_type_flags(mapped_type)

        if pyqt6_flags == 0:
            return None

        name = 'plugin_' + mapped_type.cpp_name_as_word

        const = 'const ' if spec.abi_major_version >= 14 else ''
        writer.write(f'\n\nstatic {const}pyqt6MappedTypePluginDef {name} = {{{pyqt6_flags}}};\n')

        return name

    def sip_module_generate_code(self, writer, spec):
        """ Generate code to declare and/or initialise any module-specific
        data.
        """

        # This test can go when we are moved to PyQt-builder.
        if self.pyqt_major_version == 0:
            return

        if spec.abi_major_version >= 14 and self.pyqt_major_version == 6:
            return

        module_name = spec.module_name

        writer.write(
f'''/* The Qt support. */
sip_qt_metaobject_func sip_{module_name}_qt_metaobject;
sip_qt_metacall_func sip_{module_name}_qt_metacall;
sip_qt_metacast_func sip_{module_name}_qt_metacast;

''')

    def sip_module_generate_header_code(self, writer, spec):
        """ Generate code to be included in the internal module API .h file.
        """

        # This test can go when we are moved to PyQt-builder.
        if self.pyqt_major_version == 0:
            return

        if spec.abi_major_version >= 14 and self.pyqt_major_version == 6:
            writer.write(_ABI14_PYQT6_HEADER)
            return

        module_name = spec.module_name
        type_spec_type = 'sipTypeID' if spec.abi_major_version >= 14 else 'const sipTypeDef *'

        writer.write(
f'''
#include <QMetaType>
#include <QThread>

typedef const QMetaObject *(*sip_qt_metaobject_func)(sipSimpleWrapper *, {type_spec_type});
extern sip_qt_metaobject_func sip_{module_name}_qt_metaobject;

typedef int (*sip_qt_metacall_func)(sipSimpleWrapper *, {type_spec_type}, QMetaObject::Call, int, void **);
extern sip_qt_metacall_func sip_{module_name}_qt_metacall;

typedef bool (*sip_qt_metacast_func)(sipSimpleWrapper *, {type_spec_type}, const char *, void **);
extern sip_qt_metacast_func sip_{module_name}_qt_metacast;
''')

    def sip_module_generate_initialisation_code(self, writer, spec):
        """ Generate code included in the module initialisation code. """

        # This test can go when we are moved to PyQt-builder.
        if self.pyqt_major_version == 0:
            return

        if spec.abi_major_version < 14 or self.pyqt_major_version != 6:
            module_name = spec.module_name

            writer.write(
f'''

    sip_{module_name}_qt_metaobject = (sip_qt_metaobject_func)sipImportSymbol("qtcore_qt_metaobject");
    sip_{module_name}_qt_metacall = (sip_qt_metacall_func)sipImportSymbol("qtcore_qt_metacall");
    sip_{module_name}_qt_metacast = (sip_qt_metacast_func)sipImportSymbol("qtcore_qt_metacast");

    if (!sip_{module_name}_qt_metacast)
        Py_FatalError("Unable to import qtcore_qt_metacast");
''')

        if self.pyqt_major_version == 6:
            # Generate the enum meta-type registrations for PyQt6.
            for enum in self._get_all_named_public_class_enums(spec):
                writer.write(f'    qMetaTypeId<{enum.cpp_name}>();\n')

            # Generate the QFlag meta-type registrations for PyQt6.
            for mapped_type in spec.all_mapped_types:
                if self.get_mapped_type_flags(mapped_type) != 0:
                    writer.write(f'    qMetaTypeId<{mapped_type.cpp_name}>();\n')

    def sip_overload_resolved(self, spec, scope, overload):
        """ Invoked when an overload has been resolved. """

        if self.is_signal(overload):
            if overload.is_static:
                spec.error("signal cannot be static", overload=overload)

            # We will generate code in the derived class of the class for
            # public signals.
            if overload.is_public:
                scope.needs_derived_class = True

    @staticmethod
    def sip_overload_get_prefixes(spec):
        """ Return a sequence of non-standard strings that can appear in a
        plugin-specific overload prefix.
        """

        return ('Q_SIGNAL', 'Q_SLOT')

    def sip_overload_get_typing(self, spec, overload):
        """ Return a 2-tuple of the typing entry for an overload to be included
        in the module's '.pyi' file and a flag that is True if other overloads
        of the same function should be ignored.  If None is returned then a
        default is used.
        """

        # Signals can have the same name as ordinary methods however
        # 'typing.overload' cannot be used with ClassVar.  We choose to
        # generate a type hint for the signal rather than any method as that is
        # by far the most common case.

        if not self.is_signal(overload):
            return None, False

        scope = '' if spec.module_name == 'QtCore' else 'QtCore.'
        typing = f'{overload.py_name}: typing.ClassVar[{scope}pyqtSignal]'

        return typing, True

    def sip_overload_parsed(self, spec, scope, overload):
        """ Invoked when an overload has been parsed. """

        if not spec.is_class(scope):
            return

        # Set the PyQt method type from any access specifier if it hasn't
        # already been set.
        method_type = overload.get_plugin_attribute(self, 'method_type')

        if method_type is None:
            method_type = scope.get_plugin_attribute(self, 'method_type')

            if method_type is not None:
                overload.set_plugin_attribute(self, 'method_type', method_type)

                if method_type is PyQtMethodType.SIGNAL:
                    overload.is_callable = False

    def sip_specification_resolved(self, spec):
        """ Invoked when a specification has been resolved. """

        # For PyQt6 mark all enum interface files as being used.
        if self.pyqt_major_version == 6:
            for enum in self._get_all_named_public_class_enums(spec):
                if enum.scope is not None:
                    spec.add_declaration(enum.scope)

    def sip_xml_class_add_attributes(self, attributes, klass):
        """ Add any class related attributes. """

        pyqt5_flags_enums = self.get_class_flags_enums(klass)
        if pyqt5_flags_enums is not None:
            attributes['flagsenums'] = ' '.join(pyqt5_flags_enums)

    def sip_xml_overload_add_attributes(self, attributes, overload):
        """ Add any overload related attributes. """

        if self.is_slot(overload):
            attributes['slot'] = '1'

    def _g_signals_table(self, writer, spec, klass):
        """ Generate the PyQt signals table and return True if anything was
        generated.
        """

        is_any_signals = False

        # The signals must be grouped by name.
        for function in klass.functions:
            signals = []
            is_non_signal = False

            for overload in function.overloads:
                if self.is_signal(overload):
                    signals.append(overload)
                else:
                    is_non_signal = True

            if signals:
                if not is_any_signals:
                    is_any_signals = True

                    _g_pyqt_emitters(writer, spec, klass, self)

                    klass_name_as_word = klass.cpp_name_as_word

                    writer.write(
f'''

/* Define this type's signals. */
static const pyqt{self.pyqt_major_version}QtSignal signals_{klass_name_as_word}[] = {{
''')

                # We enable a hack that supplies any missing optional
                # arguments.  We only include the version with all arguments
                # and provide an emitter function which handles the optional
                # arguments.
                function_impl = function.impl_reference if is_non_signal else 'SIP_NULLPTR'

                for signal in signals:
                    _g_signal_table_entry(writer, spec, klass, signal,
                            function_impl, self)

        if is_any_signals:
            writer.write('    {SIP_NULLPTR, SIP_NULLPTR, SIP_NULLPTR, SIP_NULLPTR}\n};\n')

        return is_any_signals

    def _get_all_named_public_class_enums(self, spec):
        """ Return an iterator over all named public class enums. """

        for enum in spec.all_enums:
            if enum.cpp_name is None or not enum.is_public:
                continue

            scope = enum.scope

            if scope is None:
                yield enum
            elif spec.is_class(scope) or spec.is_namespace(scope):
                if not self.get_no_qmetaobject(scope):
                    yield enum

    def _set_class_flags_enums(self, klass, flags_enums):
        """ Set the /PyQtFlagsEnums/ (PyQt5 only) of a class. """

        klass.set_plugin_attribute(self, 'flags_enums', flags_enums)

    def _set_mapped_type_flags(self, mapped_type, flags):
        """ Set the /PyQtFlags/ (PyQt6 only) of a mapped type. """

        mapped_type.set_plugin_attribute(self, 'flags', flags)

    def _set_qobject(self, klass):
        """ Marks a class as being or inherits QObject. """

        klass.set_plugin_attribute(self, 'is_qobject', True)


class PyQtMethodType(Enum):
    """ The PyQt-specific method type. """

    # A signal.
    SIGNAL = auto()

    # A slot.
    SLOT = auto()


_ABI14_PYQT6_HEADER = """
#include <QMetaType>
#include <QThread>

using sip_qt_metaobject_func = const QMetaObject *(*)(sipModuleState *,
        sipSimpleWrapper *, sipTypeID);
using sip_qt_metacall_func = int (*)(sipModuleState *, sipSimpleWrapper *,
        sipTypeID, QMetaObject::Call, int, void **);
using sip_qt_metacast_func = bool (*)(sipModuleState *, sipSimpleWrapper *,
        sipTypeID, const char *, void **);

using pyqt6EmitFunc = int (*)(sipModuleState *, void *, PyObject *);

struct pyqt6QtSignal
{
    const char *signature;
    const char *docstring;
    sipCallableImplFunc non_signals;
    pyqt6EmitFunc emitter;
};

struct pyqt6ClassPluginDef
{
    const QMetaObject *static_metaobject;
    const pyqt6QtSignal *qt_signals;
    const char *qt_interface;
};

struct pyqt6MappedTypePluginDef
{
    unsigned flags;
};

// A Qt callback may run on a native thread. Keep the wrapper alive while
// executing the callback in the interpreter that created it.
namespace
{
class sipQtCallback
{
public:
    sipQtCallback(sipModuleState *sipMS, void *cpp, sipTypeID type)
    {
        if (sipMS)
        {
            _thread = PyThreadState_EnsureFromView(sipGetInterpreterView());
            if (_thread)
            {
                _previous_error = PyErr_GetRaisedException();
                _wrapper = sipGetPyObjectRef(cpp, type);
            }
        }
    }

    ~sipQtCallback()
    {
        if (_thread)
        {
            if (PyErr_Occurred())
                PyErr_WriteUnraisable(_wrapper ? _wrapper : Py_None);
            Py_XDECREF(_wrapper);
            PyErr_SetRaisedException(_previous_error);
            PyThreadState_Release(_thread);
        }
    }

    sipSimpleWrapper *wrapper() const
    {
        return reinterpret_cast<sipSimpleWrapper *>(_wrapper);
    }

    sipQtCallback(const sipQtCallback &) = delete;
    sipQtCallback &operator=(const sipQtCallback &) = delete;

private:
    PyThreadStateToken *_thread = nullptr;
    PyObject *_wrapper = nullptr;
    PyObject *_previous_error = nullptr;
};
}

"""


def _g_pyqt_emitters(writer, spec, klass, plugin):
    """ Generate the PyQt emitters for a class. """
    abi14 = spec.abi_major_version >= 14 and plugin.pyqt_major_version == 6

    for function in klass.functions:
        overloads = [overload for overload in function.overloads
                if plugin.is_signal(overload) and _has_optional_args(overload)]
        if not overloads:
            continue

        signal_name = overloads[0].unscoped_cpp_name
        name = f'emit_{klass.cpp_name_as_word}_{signal_name}'
        context = 'sipModuleState *sipMS, ' if abi14 else ''
        context_decl = 'sipModuleState *, ' if abi14 else ''

        writer.write('\n\n')
        if not spec.c_bindings:
            writer.write(f'extern "C" {{static int {name}({context_decl}void *, PyObject *);}}\n\n')

        args_name = 'args' if abi14 else 'sipArgs'
        writer.write(
f"""
static int {name}({context}void *sipCppV, PyObject *{args_name})
{{
    auto *sipCpp = static_cast<{klass.cpp_name} *>(sipCppV);
""")

        if abi14:
            max_args = max(len(overload.cpp_signature.arguments)
                    for overload in overloads)
            writer.write(
f"""    Py_ssize_t sipNrArgs = PyTuple_Size(args);
    if (sipNrArgs < 0)
        return -1;

    if (sipNrArgs > {max_args})
    {{
        PyErr_SetString(PyExc_TypeError, "arguments do not match Qt signal {signal_name}");
        return -1;
    }}

    // The caller holds the immutable argument tuple throughout emission.
    PyObject *sipArgs[{max_args}];
    for (Py_ssize_t i = 0; i < sipNrArgs; ++i)
        sipArgs[i] = PyTuple_GetItem(args, i);

    PyObject *sipPState = nullptr;
    PyObject **sipPStateP = &sipPState;
    PyObject *sipKwdNames = nullptr;
    PyObject *sipSelf = nullptr;
""")
        else:
            writer.write('    PyObject *sipParseErr = SIP_NULLPTR;\n')

        for overload_nr, overload in enumerate(overloads):
            writer.write('\n    {\n')
            overload.generate_signature_parser(writer, overload_nr=overload_nr,
                    simple_call=True)

            writer.write(
f"""        {{
            Py_BEGIN_ALLOW_THREADS
            sipCpp->{signal_name}(""")
            overload.generate_call_arguments(writer)
            writer.write(');\n            Py_END_ALLOW_THREADS\n\n')

            overload.generate_signature_parser_tidy_up(writer)
            if abi14:
                writer.write('            Py_XDECREF(sipPState);\n')

            writer.write(
"""            return 0;
        }
    }
""")

        if abi14:
            writer.write(
f"""
    Py_XDECREF(sipPState);
    if (!PyErr_Occurred())
        PyErr_SetString(PyExc_TypeError, "arguments do not match Qt signal {signal_name}");
""")
        else:
            writer.write(
f"""
    sipNoMethod(sipParseErr, {klass.py_name_as_str}, {function.py_name_as_str}, SIP_NULLPTR);
""")

        writer.write('\n    return -1;\n}\n')


def _g_signal_table_entry(writer, spec, klass, signal, function_impl, plugin):
    """ Generate an entry in the signal table. """

    stripped = False
    signature_state = {}

    args = []

    for arg in signal.cpp_signature.arguments:
        # Do some signal argument normalisation so that Qt doesn't have to.
        if arg.is_const and (arg.is_reference or arg.nr_of_dereferences == 0):
            signature_state[arg] = arg.is_reference

            arg.is_const = False
            arg.is_reference = False

        strip = plugin.get_scopes_stripped(arg)

        if strip != 0:
            stripped = True
        else:
            strip = None

        args.append(arg.get_declaration(nr_of_scopes_stripped=strip))

    # Note the lack of a separating space.
    args = ','.join(args)

    writer.write(f'    {{"{signal.unscoped_cpp_name}({args})')

    # If a scope was stripped then append an unstripped version which can be
    # parsed by PyQt.
    if stripped:
        args = []

        for arg in signal.cpp_signature.arguments:
            args.append(arg.get_declaration())

        # Note the lack of a separating space.
        args = ','.join(args)

        writer.write(f'|({args})')

    writer.write('", ')

    # Restore the signature state.
    for arg, is_reference in signature_state.items():
        arg.is_const = True
        arg.is_reference = is_reference

    if spec.docstrings:
        docstring = signal.docstring
        if docstring is None:
            docstring = '\\1' + signal.type_hint

        ds = '"' + docstring + '"'
    else:
        ds = 'SIP_NULLPTR'

    writer.write(f'{ds}, {function_impl}, ')

    if _has_optional_args(signal):
        klass_name_as_word = klass.cpp_name_as_word
        writer.write(f'emit_{klass_name_as_word}_{signal.unscoped_cpp_name}')
    else:
        writer.write('SIP_NULLPTR')

    writer.write('},\n')


def _has_optional_args(overload):
    """ Return True if an overload has optional arguments. """

    args = overload.cpp_signature.arguments

    return len(args) != 0 and args[-1].is_optional
