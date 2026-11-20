%Module(name=threading_module, gil_use="NotUsed")
%MinimumABIVersion "14.0"

%ModuleHeaderCode
class FactoryValue
{
public:
    explicit FactoryValue(int value) : value_(value) {}
    int value() const { return value_; }

private:
    int value_;
};

inline FactoryValue make_value(int value) { return FactoryValue(value); }
%End

class FactoryValue
{
public:
    explicit FactoryValue(int value);
    int value() const;
};

FactoryValue make_value(int value) /ReleaseGIL/;

class Counter
{
%TypeHeaderCode
#include <atomic>

class Counter
{
public:
    Counter() = default;
    int next() { return value.fetch_add(1, std::memory_order_relaxed); }

private:
    std::atomic<int> value{0};
};
%End

public:
    Counter();
    int next() /ReleaseGIL/;

private:
    Counter(const Counter &);
};

void set_counter_type_data(SIP_PYOBJECT data);
%MethodCode
    PyTypeObject *type = sipGetPyTypeRef(sipType_Counter);
    if (!type)
        sipError = sipErrorFail;
    else
    {
        sipSetTypeUserObject(reinterpret_cast<sipWrapperType *>(type), a0);
        Py_DECREF(type);
    }
%End

SIP_PYOBJECT get_counter_type_data();
%MethodCode
    PyTypeObject *type = sipGetPyTypeRef(sipType_Counter);
    if (!type)
        sipError = sipErrorFail;
    else
    {
        sipRes = sipGetTypeUserObject(reinterpret_cast<sipWrapperType *>(type));
        Py_DECREF(type);
        if (!sipRes)
            sipRes = Py_NewRef(Py_None);
    }
%End
