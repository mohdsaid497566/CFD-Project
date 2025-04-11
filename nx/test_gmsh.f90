program test_gmsh
    use iso_c_binding
    implicit none
    interface
        subroutine gmsh_initialize(argc, argv) bind(C, name="gmshInitialize")
            import c_int, c_ptr
            integer(c_int), value :: argc
            type(c_ptr), value :: argv
        end subroutine

        function gmsh_is_initialized() bind(C, name="gmshIsInitialized")
            import c_int
            integer(c_int) :: gmsh_is_initialized
        end function

        subroutine gmsh_finalize() bind(C, name="gmshFinalize")
        end subroutine
    end interface

    integer(c_int) :: initialized

    write(*,*) "DEBUG: Testing Gmsh initialization..."
    call gmsh_initialize(0_c_int, c_null_ptr)
    write(*,*) "DEBUG: gmsh_initialize completed."

    initialized = gmsh_is_initialized()
    if (initialized /= 1) then
        write(*,*) "ERROR: Gmsh is not initialized."
    else
        write(*,*) "DEBUG: Gmsh is initialized successfully."
    end if

    call gmsh_finalize()
    write(*,*) "DEBUG: Gmsh finalized."
end program test_gmsh
