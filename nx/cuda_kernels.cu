#include <cuda_runtime.h>

// CUDA kernel for initializing a vector
__global__ void initializeVector(double *data, size_t size) {
    size_t idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < size) {
        data[idx] = static_cast<double>(idx);
    }
}
