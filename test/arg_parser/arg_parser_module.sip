// The SIP implementation of the arg_parser_module test module.


%Module(name=arg_parser_module, gil_use="NotUsed",
        multi_interpreter_support="PerInterpreterGILSupported")

%MinimumABIVersion "12.0"
%MinimumABIVersion "13.0"
%MinimumABIVersion "14.0"


%ModuleHeaderCode
#include <cstring>

inline int encode_options(int base, int tens, int units)
{
    return 100 * base + 10 * tens + units;
}

inline int encoded_length(const char *text) {return text ? std::strlen(text) : -1;}
inline unsigned char encoded_byte(char character) {return character;}

inline int sum_bytes(const unsigned char *data, Py_ssize_t size)
{
    int sum = 0;
    for (Py_ssize_t i = 0; i < size; ++i)
        sum += data[i];

    return sum;
}

inline Py_ssize_t echo_size(Py_ssize_t value) {return value;}
inline Py_ssize_t echo_size_with_hook(Py_ssize_t value) {return value;}

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

inline int operator*(const Operand &lhs, const Operand &rhs)
{
    return lhs.value() * rhs.value();
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


int encode_options(int base, int tens = 2, int units = 3) /KeywordArgs="All"/;
int encoded_length(const char *text /Encoding="ASCII"/);
int latin1_length(const char *text /Encoding="Latin-1"/);
%MethodCode
    sipRes = encoded_length(a0);
%End
int utf8_length(const char *text /Encoding="UTF-8"/);
%MethodCode
    sipRes = encoded_length(a0);
%End
unsigned char encoded_byte(char character /Encoding="ASCII"/);

int sum_bytes(const unsigned char *data /Array/, Py_ssize_t size /ArraySize/);
Py_ssize_t echo_size(Py_ssize_t value);
Py_ssize_t echo_size_with_hook(Py_ssize_t value) /PostHook=_sip_test_optional_hook/;

class Operand
{
public:
    explicit Operand(int value);
};

int operator*(int factor /Constrained/, const Operand &operand);
int operator*(double factor, const Operand &operand);
int operator*(const Operand &lhs, const Operand &rhs) /__matmul__/;

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
