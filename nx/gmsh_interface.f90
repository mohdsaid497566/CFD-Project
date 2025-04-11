module gmsh_interface
    use iso_c_binding
    implicit none

    interface
        ! Add initialization status check
        function gmsh_is_initialized() bind(C, name="gmshIsInitialized")
            import c_int
            integer(c_int) :: gmsh_is_initialized
        end function

        ! Modify initialization to include error code
        function gmsh_initialize_with_error(argc, argv, ierr) bind(C, name="gmshInitialize")
            import c_int, c_ptr
            integer(c_int), value :: argc
            type(c_ptr), value :: argv
            integer(c_int), intent(out) :: ierr
            integer(c_int) :: gmsh_initialize_with_error
        end function

        ! Remove gmshGetVersion and rely on initialization
        subroutine gmsh_initialize(argc, argv) bind(C, name="gmshInitialize")
            import c_int, c_ptr
            integer(c_int), value :: argc
            type(c_ptr), value :: argv
        end subroutine

        subroutine gmsh_finalize() bind(C, name="gmshFinalize")
        end subroutine

        ! Modified for proper string handling
        subroutine gmsh_option_set_number(name, value) bind(C, name="gmshOptionSetNumber")
            import c_char, c_double
            character(kind=c_char), dimension(*), intent(in) :: name
            real(c_double), value :: value
        end subroutine

        ! Add error handling for option setting
        function gmsh_option_set_number_with_error(name, value, ierr) bind(C, name="gmshOptionSetNumber")
            import c_char, c_double, c_int
            character(kind=c_char), dimension(*), intent(in) :: name
            real(c_double), value :: value
            integer(c_int), intent(out) :: ierr
            integer(c_int) :: gmsh_option_set_number_with_error
        end function

        ! Add status return for model operations
        function gmsh_model_add(name) bind(C, name="gmshModelAdd")
            import c_char, c_int
            character(kind=c_char), dimension(*), intent(in) :: name
            integer(c_int) :: gmsh_model_add
        end function

        subroutine gmsh_merge(filename, ierr) bind(C, name="gmshMerge")
            import c_char, c_int
            character(kind=c_char), intent(in) :: filename(*)
            integer(c_int), intent(out) :: ierr
        end subroutine

        subroutine gmsh_model_occ_synchronize() bind(C, name="gmshModelOccSynchronize")
        end subroutine

        subroutine gmsh_model_get_bounding_box(dim, tag, xmin, ymin, zmin, xmax, ymax, zmax) &
            bind(C, name="gmshModelGetBoundingBox")
            import c_int, c_double
            integer(c_int), value :: dim, tag
            real(c_double), intent(out) :: xmin, ymin, zmin, xmax, ymax, zmax
        end subroutine

        subroutine gmsh_model_occ_add_box(x, y, z, dx, dy, dz, tag) bind(C, name="gmshModelOccAddBox")
            import c_double, c_int
            real(c_double), value :: x, y, z, dx, dy, dz
            integer(c_int), intent(out) :: tag
        end subroutine

        subroutine gmsh_model_mesh_generate(dim) bind(C, name="gmshModelMeshGenerate")
            import c_int
            integer(c_int), value :: dim
        end subroutine

        subroutine gmsh_write(filename) bind(C, name="gmshWrite")
            import c_char
            character(kind=c_char), intent(in) :: filename(*)
        end subroutine

        ! Add new GUI-related interfaces
        function gmsh_fltk_initialize() bind(C, name="gmshFltkInitialize")
            import c_int
            integer(c_int) :: gmsh_fltk_initialize
        end function

        subroutine gmsh_option_set_number_with_name(name, value) bind(C, name="gmshOptionSetNumber")
            import c_char, c_double
            character(kind=c_char), intent(in) :: name(*)
            real(c_double), value :: value
        end subroutine

        subroutine gmsh_graphics_draw() bind(C, name="gmshGraphicsDraw")
        end subroutine

        function gmsh_fltk_run() bind(C, name="gmshFltkRun")
            import c_int
            integer(c_int) :: gmsh_fltk_run
        end function

        ! Add error status query
        function gmsh_get_last_error(msg) bind(C, name="gmshGetLastError")
            import c_char, c_int
            character(kind=c_char), dimension(*), intent(out) :: msg
            integer(c_int) :: gmsh_get_last_error
        end function

        ! Correct version query interface
        subroutine gmsh_get_version(major, minor, patch) bind(C, name="gmshGetVersion")
            import c_int
            integer(c_int), intent(out) :: major, minor, patch
        end subroutine

    end interface
end module gmsh_interface
