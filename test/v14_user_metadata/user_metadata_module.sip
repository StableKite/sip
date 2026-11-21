%Module(name=user_metadata_module, gil_use="NotUsed")
%MinimumABIVersion "14.0"

%ModuleHeaderCode
class Wrapper
{
};
%End

class Wrapper
{
public:
    void replace_data(SIP_PYOBJECT value);
%MethodCode
    sipSetUserObject(reinterpret_cast<sipSimpleWrapper *>(sipSelf), a0);
%End

    SIP_PYOBJECT data();
%MethodCode
    sipRes = sipGetUserObjectRef(reinterpret_cast<sipSimpleWrapper *>(sipSelf));
    if (!sipRes)
        sipRes = Py_NewRef(Py_None);
%End
};

void replace_type_data(SIP_PYOBJECT value);
%MethodCode
    auto *type = sipGetPyTypeRef(sipType_Wrapper);
    if (!type)
        sipError = sipErrorFail;
    else
    {
        sipSetTypeUserObject(reinterpret_cast<sipWrapperType *>(type), a0);
        Py_DECREF(type);
    }
%End

SIP_PYOBJECT type_data();
%MethodCode
    auto *type = sipGetPyTypeRef(sipType_Wrapper);
    if (!type)
        sipError = sipErrorFail;
    else
    {
        sipRes = sipGetTypeUserObjectRef(reinterpret_cast<sipWrapperType *>(type));
        Py_DECREF(type);
        if (!sipRes)
            sipRes = Py_NewRef(Py_None);
    }
%End
