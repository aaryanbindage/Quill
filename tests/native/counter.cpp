#include "counter.hpp"

namespace geo {
Counter::Counter() : v_(0) {}
Counter::Counter(int start) : v_(start) {}
Counter::~Counter() {}
void Counter::add(int n) { v_ += n; }
int Counter::value() const { return v_; }
double Counter::ratio(double a, double b) const {
    if (b == 0) throw std::runtime_error("division by zero");
    return a / b;
}
std::string Counter::label(const std::string& prefix) const { return prefix + std::to_string(v_); }
void Counter::fail(const std::string& why) { throw std::runtime_error(why); }
Counter* Counter::self() { return this; }
int Counter::answer() { return 42; }
std::string greet(const std::string& name) { return "hello, " + name; }
int clamp(int x, int lo, int hi) { return x < lo ? lo : x > hi ? hi : x; }
}
