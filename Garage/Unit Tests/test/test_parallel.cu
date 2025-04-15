#include <cuda_runtime.h>
#include <iostream>
#include <vector>

// CUDA kernel for initializing a vector
__global__ void initializeVector(double *data, size_t size) {
    size_t idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < size) {
        data[idx] = static_cast<double>(idx);
    }
}

void runCudaTest(size_t N, std::vector<double> &hostData) {
    double *deviceData;
    cudaMalloc(&deviceData, N * sizeof(double));
    initializeVector<<<(N + 255) / 256, 256>>>(deviceData, N);
    cudaMemcpy(hostData.data(), deviceData, N * sizeof(double), cudaMemcpyDeviceToHost);
    cudaFree(deviceData);
}
