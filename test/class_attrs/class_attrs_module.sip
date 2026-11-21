// The SIP implementation of the class_attrs_module test module.


%Module(name=class_attrs_module, gil_use="NotUsed",
        multi_interpreter_support="PerInterpreterGILSupported")

%MinimumABIVersion "12.0"
%MinimumABIVersion "13.0"
%MinimumABIVersion "14.0"


%ModuleHeaderCode
class Value
{
public:
    Value(int v = 0) : m_value(v) {}

    int get_value() const {return m_value;}

private:
    int m_value;
};

class Klass
{
public:
    enum Mode {Active};

    Klass() : attr(0), class_attr(0) {}

    static int s_attr;
    static int get_s_attr() {return s_attr;}

    static int s_attr_with_code;
    static PyObject *declaring_type;

    int attr;
    int get_attr() {return attr;}

    Value *class_attr;
    Value *get_class_attr() const {return class_attr;}

    Value value_attr;
};
%End


%ModuleCode
int Klass::s_attr = 0;
int Klass::s_attr_with_code = 0;
PyObject *Klass::declaring_type = nullptr;
%End


class Value
{
public:
    Value(int v = 0);

    int get_value() const;
};

class Klass
{
public:
    enum Mode {Active};

    Klass();

    static int s_attr;
    static int get_s_attr();

    static SIP_PYOBJECT declaring_type
    {
        %GetCode
            sipPy = Py_NewRef(sipPyType);
        %End
    };

    static int s_attr_with_code
    {
        %GetCode
            sipPy = PyLong_FromLong(Klass::s_attr_with_code);
        %End
        %SetCode
            Klass::s_attr_with_code = PyLong_AsLong(sipPy);

            if (PyErr_Occurred())
                sipErr = 1;
        %End
    };

    int attr;
    int get_attr();

    Value *class_attr;
    Value *get_class_attr() const;

    Value value_attr;
};


bool is_user_type(SIP_PYTYPE type);
%MethodCode
    sipRes = sipIsUserType(reinterpret_cast<sipWrapperType *>(a0));
%End


%ModuleHeaderCode
class Derived : public Klass {};
%End

class Derived : public Klass
{
public:
    Derived();
};
