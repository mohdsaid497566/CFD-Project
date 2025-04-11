#include <iostream>
#include <vector>
#include <omp.h>

// Declare the CUDA function
void runCudaTest(size_t N, std::vector<double> &hostData);

int main() {
    // Force OpenMP to use NVIDIA's implementation
    setenv("OMP_PROC_BIND", "true", 1);
    setenv("OMP_NUM_THREADS", "4", 1);  // Adjust as needed

    // Initialize OpenMP
    omp_set_dynamic(0);
    if(omp_get_num_devices() > 0) {
        omp_set_default_device(0);
    }

    const size_t N = 1000000;
    std::vector<double> hostData(N, 0.0);

    int max_threads = omp_get_max_threads();
    std::cout << "OpenMP initialized with " << max_threads << " threads." << std::endl;

    // Test OpenMP
    #pragma omp parallel for
    for (size_t i = 0; i < N; ++i) {
        hostData[i] = static_cast<double>(i);
    }

    // Verify OpenMP results
    bool success = true;
    for (size_t i = 0; i < N && success; ++i) {
        if (hostData[i] != static_cast<double>(i)) {
            success = false;
        }
    }
    std::cout << "OpenMP test " << (success ? "passed" : "failed") << std::endl;

    // Test CUDA
    runCudaTest(N, hostData);

    // Verify CUDA results
    success = true;
    for (size_t i = 0; i < N && success; ++i) {
        if (hostData[i] != static_cast<double>(i)) {
            success = false;
        }
    }
    std::cout << "CUDA test " << (success ? "passed" : "failed") << std::endl;

    return 0;
}
