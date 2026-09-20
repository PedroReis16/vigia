#include "capture_runner.hpp"

#include <iostream>
#include <stdexcept>

int main() {
  try {
    vigia::run_capture();
  } catch (const std::exception& e) {
    std::cerr << "Fatal: " << e.what() << std::endl;
    return 1;
  }
  return 0;
}
