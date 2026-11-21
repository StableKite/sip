// The SIP implementation of the arg_parser_module test module.


%Module(name=arg_parser_module, gil_use="NotUsed",
        multi_interpreter_support="PerInterpreterGILSupported")

%MinimumABIVersion "12.0"
%MinimumABIVersion "13.0"
%MinimumABIVersion "14.0"


%ModuleHeaderCode
inline int sum_bytes(const unsigned char *data, Py_ssize_t size)
{
    int sum = 0;
    for (Py_ssize_t i = 0; i < size; ++i)
        sum += data[i];

    return sum;
}

inline Py_ssize_t echo_size(Py_ssize_t value) {return value;}

class Operand
{
public:
    explicit Operand(int value) : m_value(value) {}
    int value() const {return m_value;}
private:
    int m_value;
};

inline int operator*(int factor, const Operand &operand)
{
    return operand.value() * factor;
}

inline int operator*(double factor, const Operand &operand)
{
    return static_cast<int>(operand.value() * factor);
}

class FactoryOnly
{
public:
    int value() const {return 42;}
};

inline FactoryOnly *make_factory_only() {return new FactoryOnly;}

class OwnedClass
{
};

class Klass
{
public:
    Klass() : m_sub(0), m_inst(0), m_prot_inst(0) {}
    Klass(OwnedClass *sub) : m_sub(sub), m_inst(0), m_prot_inst(0) {}
    ~Klass() {
        if (m_sub) {
            delete m_sub;
            m_sub = 0;
        }
    }

    static void set_static(int value) {m_static = value;}
    static int get_static() {return m_static;}

    void set_inst(int value) {m_inst = value;}
    int get_inst() const {return m_inst;}

protected:
    void set_prot_inst(int value) {m_prot_inst = value;}
    int get_prot_inst() const {return m_prot_inst;}

private:
    OwnedClass *m_sub;
    static int m_static;
    int m_inst;
    int m_prot_inst;
};
%End

%ModuleCode
int Klass::m_static = 0;
%End


class Klass
{
public:
    Klass();
    Klass(OwnedClass *sub /Transfer/);
    ~Klass();

    static void set_static(int value);
    static int get_static();

    void set_inst(int value);
    int get_inst() const;

protected:
    void set_prot_inst(int value);
    int get_prot_inst() const;
};

class OwnedClass
{
};


int sum_bytes(const unsigned char *data /Array/, Py_ssize_t size /ArraySize/);
Py_ssize_t echo_size(Py_ssize_t value);

class Operand
{
public:
    explicit Operand(int value);
};

int operator*(int factor /Constrained/, const Operand &operand);
int operator*(double factor, const Operand &operand);

SIP_PYOBJECT get_argument_wrapper(OwnedClass *value /GetWrapper/);
%MethodCode
    sipRes = Py_NewRef(a0Wrapper);
%End


class FactoryOnly /NoDefaultCtors/
{
public:
    int value() const;
};

FactoryOnly *make_factory_only() /Factory/;
