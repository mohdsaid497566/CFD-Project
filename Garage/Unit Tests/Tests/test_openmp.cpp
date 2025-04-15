#include <iostream>
#include <vector>
#include <omp.h>

int main() {
    try {
        // Test OpenMP thread control
        int max_threads = omp_get_max_threads();
        std::cout << "Maximum available threads: " << max_threads << std::endl;

        // Test parallel operations
        const size_t N = 1000000;
        std::vector<double> test_data(N, 0.0);

        #pragma omp parallel for
        for (size_t i = 0; i < N; ++i) {
            test_data[i] = static_cast<double>(i);
        }

        // Verify computation
        bool success = true;
        for (size_t i = 0; i < N && success; ++i) {
            if (test_data[i] != static_cast<double>(i)) {
                success = false;
            }
        }
        std::cout << "Parallel operation " << (success ? "completed successfully" : "failed") << std::endl;

        return 0;
    } catch (const std::exception &e) {
        std::cerr << "Fatal error: " << e.what() << std::endl;
        return 1;
    }
}
