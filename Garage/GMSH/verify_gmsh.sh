#!/bin/bash

# Script to verify Gmsh library functionality
# Exit immediately if a command fails
set -e

echo "===== Gmsh Verification Script ====="

# Check if libgmsh.so exists and is accessible
echo "Checking for libgmsh.so..."
GMSH_PATHS=("/usr/local/lib" "/usr/lib" "$(pwd)/gmsh/lib")

for path in "${GMSH_PATHS[@]}"; do
    if [ -f "$path/libgmsh.so" ]; then
        echo "Found libgmsh.so at: $path/libgmsh.so"
        GMSH_LIB_PATH="$path"
        break
    fi
done

if [ -z "$GMSH_LIB_PATH" ]; then
    echo "ERROR: Could not find libgmsh.so in standard locations."
    echo "Searching entire project directory (this might take a while)..."
    GMSH_LIB=$(find /mnt/c/Users/Mohammed/Desktop/Intake-CFD-Project -name "libgmsh.so" | head -n1)
    if [ -n "$GMSH_LIB" ]; then
        GMSH_LIB_PATH=$(dirname "$GMSH_LIB")
        echo "Found libgmsh.so at: $GMSH_LIB"
    else
        echo "ERROR: Could not find libgmsh.so anywhere in the project."
        exit 1
    fi
fi

# Set the LD_LIBRARY_PATH
export LD_LIBRARY_PATH="$GMSH_LIB_PATH:$LD_LIBRARY_PATH"
echo "Set LD_LIBRARY_PATH=$LD_LIBRARY_PATH"

# Create a simple test program to verify Gmsh functionality
echo "Creating a simple Gmsh test program..."
cat > test_gmsh.f90 << 'EOT'
program test_gmsh
    use iso_c_binding
    implicit none
    
    interface
        subroutine gmsh_initialize(argc, argv, ierr) bind(C, name="gmshInitialize")
            import c_int, c_ptr
            integer(c_int), value :: argc
            type(c_ptr), value :: argv
            integer(c_int), intent(out) :: ierr
        end subroutine
        
        function gmsh_is_initialized() bind(C, name="gmshIsInitialized")
            import c_int
            integer(c_int) :: gmsh_is_initialized
        end function
        
        subroutine gmsh_finalize(ierr) bind(C, name="gmshFinalize")
            import c_int
            integer(c_int), intent(out) :: ierr
        end subroutine
    end interface
    
    integer(c_int) :: ierr, initialized
    type(c_ptr) :: argv_null = c_null_ptr
    
    write(*,*) "TEST: Attempting to initialize Gmsh..."
    call gmsh_initialize(0, argv_null, ierr)
    write(*,*) "TEST: gmsh_initialize returned error code:", ierr
    
    initialized = gmsh_is_initialized()
    write(*,*) "TEST: gmsh_is_initialized returned:", initialized
    
    if (ierr /= 0 .or. initialized /= 1) then
        write(*,*) "ERROR: Gmsh initialization failed!"
    else
        write(*,*) "SUCCESS: Gmsh initialized correctly."
    end if
    
    write(*,*) "TEST: Finalizing Gmsh..."
    call gmsh_finalize(ierr)
    write(*,*) "TEST: gmsh_finalize returned error code:", ierr
    
end program test_gmsh
EOT

# Compile the test program
echo "Compiling test program..."
gfortran -o test_gmsh test_gmsh.f90 -L"$GMSH_LIB_PATH" -lgmsh

# Run the test program
echo "Running test program..."
./test_gmsh

# Check if the test program ran successfully
if [ $? -eq 0 ]; then
    echo "VERIFICATION COMPLETE: Gmsh library appears to be working correctly."
else
    echo "VERIFICATION FAILED: Gmsh library encountered errors."
    exit 1
fi

echo "You can now try running your application with:"
echo "export LD_LIBRARY_PATH=\"$GMSH_LIB_PATH:\$LD_LIBRARY_PATH\""
echo "./gmsh_process"

# Clean up
rm -f test_gmsh.f90 test_gmsh

chmod +x verify_gmsh.sh
