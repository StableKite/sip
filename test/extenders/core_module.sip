// The SIP implementation of the core_module test module.


%Module(name=extenders.core_module, gil_use="NotUsed",
        multi_interpreter_support="PerInterpreterGILSupported")

%MinimumABIVersion "12.0"
%MinimumABIVersion "13.0"
%MinimumABIVersion "14.0"


%ModuleHeaderCode
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


%MappedType WrappedValue
{
%TypeHeaderCode
#include "klass.h"
%End

%ConvertToTypeCode
    if (sipIsErr == NULL)
        return sipCanConvertToType(sipPy, sipType_Klass, SIP_NOT_NONE);

    int state = 0;
    auto *value = reinterpret_cast<Klass *>(sipForceConvertToType(sipPy,
            sipType_Klass, NULL, SIP_NOT_NONE, &state, sipIsErr));
    if (!value)
        return 0;

    *sipCppPtr = new WrappedValue{*value};
    sipReleaseType(value, sipType_Klass, state);
    return SIP_TEMPORARY;
%End

%ConvertFromTypeCode
    return sipConvertFromNewType(new Klass(sipCpp->value), sipType_Klass, NULL);
%End
};
