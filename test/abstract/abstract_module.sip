// The SIP implementation of the abstract_module test module.


%Module(name=abstract_module, gil_use="NotUsed",
        multi_interpreter_support="PerInterpreterGILSupported")

%MinimumABIVersion "12.0"
%MinimumABIVersion "13.0"
%MinimumABIVersion "14.0"


%ModuleHeaderCode
class AbstractBaseClass
{
public:
    virtual ~AbstractBaseClass() {}
    virtual int get_value() const = 0;
};

class ConcreteClass : public AbstractBaseClass
{
public:
    virtual int get_value() const {return 10;}
};
class FactoryValue
{
public:
    static FactoryValue *make() {return new FactoryValue(42);}
    int value() const {return stored_value;}

private:
    explicit FactoryValue(int value) : stored_value(value) {}
    int stored_value;
};
%End


class AbstractBaseClass
{
public:
    virtual ~AbstractBaseClass();
    virtual int get_value() const = 0;
};

class ConcreteClass : public AbstractBaseClass
{
public:
    virtual int get_value() const;
};


class FactoryValue /NoDefaultCtors/
{
public:
    static FactoryValue *make() /Factory/;
    int value() const;
};
