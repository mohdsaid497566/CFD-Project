module gmsh_interface
    use iso_c_binding
    implicit none

    interface
        ! Core functions
        function gmsh_is_initialized() bind(C, name="gmshIsInitialized")
            import c_int
            integer(c_int) :: gmsh_is_initialized
        end function

        ! Multiple versions of initialize with different signatures
        subroutine gmsh_initialize(argc, argv, ierr) bind(C, name="gmshInitialize") 
            import c_int, c_ptr
            integer(c_int), value :: argc
            type(c_ptr), value :: argv
            integer(c_int), intent(out) :: ierr
        end subroutine

        subroutine gmshinitialize(ierr) bind(C, name="gmshInitialize")
            import c_int
            integer(c_int), intent(out) :: ierr
        end subroutine

        subroutine gmshfinalize(ierr) bind(C, name="gmshFinalize")
            import c_int
            integer(c_int), intent(out) :: ierr
        end subroutine
        
        ! Multiple signatures for merge based on how it's called
        subroutine gmsh_merge(filename, ierr) bind(C, name="gmshMerge")
            import c_char, c_int
            character(kind=c_char), dimension(*), intent(in) :: filename
            integer(c_int), intent(out) :: ierr
        end subroutine
        
        subroutine gmsh_write(filename, ierr) bind(C, name="gmshWrite")
            import c_char, c_int
            character(kind=c_char), dimension(*), intent(in) :: filename
            integer(c_int), intent(out) :: ierr
        end subroutine

        ! Model functions
        function gmsh_model_add(name) bind(C, name="gmshModelAdd")
            import c_char, c_int
            character(kind=c_char), dimension(*), intent(in) :: name
            integer(c_int) :: gmsh_model_add
        end function
        
        ! Support the function with additional integer parameters 
        subroutine gmsh_model_get_bounding_box(dim1, tag1, xmin, ymin, zmin, xmax, &
                                              ymax, zmax, ierr) &
                                              bind(C, name="gmshModelGetBoundingBox")
            import c_int, c_double
            integer(c_int), value :: dim1, tag1
            real(c_double), intent(out) :: xmin, ymin, zmin, xmax, ymax, zmax
            integer(c_int), intent(out) :: ierr
        end subroutine
        
        ! Mesh functions
        subroutine gmsh_model_mesh_generate(dim, ierr) bind(C, name="gmshModelMeshGenerate")
            import c_int
            integer(c_int), value :: dim
            integer(c_int), intent(out) :: ierr
        end subroutine
        
        ! OCC functions
        subroutine gmsh_model_occ_synchronize(ierr) bind(C, name="gmshModelOccSynchronize")
            import c_int
            integer(c_int), intent(out) :: ierr
        end subroutine
        
        subroutine gmsh_model_occ_add_box(x, y, z, dx, dy, dz, tag, ierr) &
                                         bind(C, name="gmshModelOccAddBox")
            import c_double, c_int
            real(c_double), value :: x, y, z, dx, dy, dz
            integer(c_int), intent(out) :: tag
            integer(c_int), intent(out) :: ierr
        end subroutine

        ! Option functions
        subroutine gmsh_option_set_number(name, value, ierr) bind(C, name="gmshOptionSetNumber")
            import c_char, c_double, c_int
            character(kind=c_char), dimension(*), intent(in) :: name
            real(c_double), value :: value
            integer(c_int), intent(out) :: ierr
        end subroutine
    end interface
end module gmsh_interface
