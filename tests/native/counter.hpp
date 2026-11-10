#pragma once
#include <string>
#include <stdexcept>

namespace geo {

class Counter {
public:
    Counter();
    explicit Counter(int start);
    ~Counter();
    void add(int n);
    int value() const;
    double ratio(double a, double b) const;       // throws when b == 0
    std::string label(const std::string& prefix) const;
    void fail(const std::string& why);            // always throws
    Counter* self();                              // a borrowed pointer
    static int answer();
private:
    int v_;
};

std::string greet(const std::string& name);
int clamp(int x, int lo, int hi);

}  // namespace geo
