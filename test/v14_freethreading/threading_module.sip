%Module(name=threading_module, gil_use="NotUsed")
%MinimumABIVersion "14.0"

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
