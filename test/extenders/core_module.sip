// The SIP implementation of the core_module test module.


%Module(name=extenders.core_module, gil_use="NotUsed",
        multi_interpreter_support="PerInterpreterGILSupported")

%MinimumABIVersion "12.0"
%MinimumABIVersion "13.0"
%MinimumABIVersion "14.0"


%ModuleHeaderCode
#include "klass.h"

namespace NameSpace
{
    int twice(int n);
};
%End


%ModuleCode
int NameSpace::twice(int n)
{
    return 2 * n;
}
%End


namespace NameSpace
{
    enum Kind { Example };

    int twice(int n /Constrained/);
};

class Klass
{
%TypeHeaderCode
#include "klass.h"
%End

public:
    Klass();

    int get_int_attr() const;
    void set_int_attr(int value);

    int operator+(int n /Constrained/) const;
};


%If (SIP_ABI_14 -)
void call_optional_hook();
%MethodCode
    sipCallHook("_sip_test_optional_hook");
    if (PyErr_Occurred())
        sipError = sipErrorFail;
%End

PyObject *call_handwritten();
%MethodCode
    PyErr_SetString(PyExc_ValueError, "handwritten error");
    sipRes = NULL;
%End

%ModuleCode
extern "C" {
static int mark_python_subclass(sipModuleState *, sipTypeID, PyTypeObject *);
}

static int mark_python_subclass(sipModuleState *, sipTypeID, PyTypeObject *type)
{
    return PyObject_SetAttrString((PyObject *)type, "_created_as_python_subclass", Py_True);
}
%End

%PostInitialisationCode
    static const sipEventHandlerSpec handlers[] = {
        {sipEventPythonSubclass, sipType_Klass, (void *)mark_python_subclass},
        {sipEventNone, 0, nullptr}
    };
    if (sipRegisterEventHandlers(handlers) < 0)
        return -1;
%End
%End
