module gmsh_process
    use iso_fortran_env
    use iso_c_binding
    use gmsh_interface
    use string_utils
    implicit none

    ! Define precision parameters
    integer, parameter :: dp = REAL64

    ! Define boundary layer parameters type
    type :: boundary_layer_type
        real(dp) :: thickness
        real(dp) :: progression
        real(dp) :: min_thickness
        integer :: num_layers
    end type boundary_layer_type

contains
    subroutine create_engine_intake_cfd_mesh_surfaces_v5(step_file, output_msh, &
                                                        domain_scale, base_mesh_size, &
                                                        bl_params, mesh_algorithm_3d, &
                                                        mesh_algorithm_2d, num_threads, &
                                                        optimize_netgen, ierr)
        implicit none
        
        ! Arguments
        character(len=*), intent(in) :: step_file, output_msh
        real(dp), intent(in) :: domain_scale, base_mesh_size
        type(boundary_layer_type), intent(in) :: bl_params
        integer, intent(in) :: mesh_algorithm_3d, mesh_algorithm_2d, num_threads
        logical, intent(in) :: optimize_netgen
        integer, intent(out) :: ierr
        
        ! Local variables
        integer :: num_cores, actual_threads
        real(dp) :: xmin, ymin, zmin, xmax, ymax, zmax
        real(dp) :: domain_center_x, domain_center_y, domain_center_z
        real(dp) :: max_dim, dx, dy, dz
        integer :: domain_vol
        character(kind=c_char, len=:), allocatable :: c_step_file, c_output_msh
        type(c_ptr) :: argv_null = c_null_ptr
        integer(c_int) :: init_status, gmsh_error, model_status
        character(len=256) :: env_value
        integer :: env_status, alloc_status, i
        logical :: file_exists, dir_exists
        character(len=1024) :: error_msg
        integer :: slash_pos

        ! Initialize error status
        ierr = 0
        write(*,*) "DEBUG: Starting subroutine with parameters:"
        write(*,*) "  step_file:", trim(step_file)
        write(*,*) "  output_msh:", trim(output_msh)
        write(*,*) "  domain_scale:", domain_scale
        write(*,*) "  base_mesh_size:", base_mesh_size
        write(*,*) "  num_threads:", num_threads

        ! Force headless mode
        write(*,*) "DEBUG: Setting NoGui option before any Gmsh initialization..."
        call gmsh_option_set_number("General.NoGui", 1.0_dp, ierr)

        ! Check environment variables
        call get_environment_variable("LD_LIBRARY_PATH", env_value, status=env_status)
        write(*,*) "DEBUG: LD_LIBRARY_PATH =", trim(env_value)
        call get_environment_variable("DISPLAY", env_value, status=env_status)
        write(*,*) "DEBUG: DISPLAY =", trim(env_value)

        ! Verify input file exists and is readable
        inquire(file=step_file, exist=file_exists)
        if (.not. file_exists) then
            write(*,*) "ERROR: Input STEP file not found:", trim(step_file)
            ierr = -1
            return
        end if

        ! Check output directory exists and is writable
        env_value = trim(output_msh)
        slash_pos = 0
        do i = len_trim(env_value), 1, -1
            if (env_value(i:i) == '/' .or. env_value(i:i) == '\') then
                slash_pos = i
                inquire(file=env_value(:i-1), exist=dir_exists)
                if (.not. dir_exists) then
                    write(*,*) "ERROR: Output directory does not exist:", trim(env_value(:i-1))
                    ierr = -2
                    return
                end if
                exit
            end if
        end do

        write(*,*) "DEBUG: Converting strings..."
        allocate(character(kind=c_char,len=len_trim(step_file)+1) :: c_step_file, stat=alloc_status)
        if (alloc_status /= 0) then
            write(*,*) "ERROR: Failed to allocate memory for c_step_file"
            ierr = -3
            return
        end if
        
        allocate(character(kind=c_char,len=len_trim(output_msh)+1) :: c_output_msh, stat=alloc_status)
        if (alloc_status /= 0) then
            write(*,*) "ERROR: Failed to allocate memory for c_output_msh"
            deallocate(c_step_file)
            ierr = -4
            return
        end if

        c_step_file = f_c_string(step_file)
        c_output_msh = f_c_string(output_msh)
        write(*,*) "DEBUG: Strings converted successfully"
        
        ! Verify string conversion
        write(*,*) "DEBUG: c_step_file length:", len_trim(c_step_file)
        write(*,*) "DEBUG: c_output_msh length:", len_trim(c_output_msh)

        ! Determine number of threads
        actual_threads = num_threads
        if (num_threads <= 0) then
            write(*,*) "Getting number of cores..."
            call get_number_of_cores(num_cores)
            actual_threads = num_cores
            write(*,*) "Using", actual_threads, "threads"
        end if
        
        write(*,*) "DEBUG: Initializing Gmsh..."
        call gmsh_initialize(0_c_int, argv_null, ierr)
        if (gmsh_is_initialized() /= 1) then
            write(*,*) "ERROR: Gmsh initialization failed. Unable to retrieve error message."
            ierr = -1
            return
        end if
        write(*,*) "DEBUG: Gmsh initialized successfully."

        write(*,*) "Setting initial Gmsh options..."
        call gmsh_option_set_number("General.Terminal", 1.0_dp, ierr)
        call gmsh_option_set_number("General.NumThreads", real(actual_threads, dp), ierr)

        write(*,*) "Adding model..."
        model_status = gmsh_model_add(f_c_string("engine_intake_cfd_surface_v5"))
        if (model_status /= 0) then
            write(*,*) "Error: Failed to add model. Status = ", model_status
            ierr = 2
            return
        end if
        write(*,*) "Model added successfully"

        write(*,*) "Merging STEP file: ", trim(step_file)
        call gmsh_merge(c_step_file, ierr)
        if (ierr /= 0) then
            write(*,*) "Error: Failed to merge STEP file. ierr = ", ierr
            return
        end if

        write(*,*) "Setting geometry fixing options..."
        call gmsh_option_set_number("Geometry.OCCFixDegenerated", 1.0_dp, ierr)
        call gmsh_option_set_number("Geometry.OCCFixSmallEdges", 1.0_dp, ierr)
        call gmsh_option_set_number("Geometry.OCCFixSmallFaces", 1.0_dp, ierr)
        call gmsh_option_set_number("Geometry.OCCSewFaces", 1.0_dp, ierr)
        call gmsh_model_occ_synchronize(ierr)

        write(*,*) "Getting bounding box..."
        call gmsh_model_get_bounding_box(-1, -1, xmin, ymin, zmin, xmax, ymax, zmax, ierr)
        write(*,*) "Bounding box: xmin=", xmin, ", ymin=", ymin, ", zmin=", zmin, &
                   ", xmax=", xmax, ", ymax=", ymax, ", zmax=", zmax

        write(*,*) "Creating domain box..."
        domain_center_x = (xmin + xmax) / 2.0_dp
        domain_center_y = (ymin + ymax) / 2.0_dp
        domain_center_z = (zmin + zmax) / 2.0_dp
        max_dim = max(xmax - xmin, ymax - ymin, zmax - zmin)

        dx = max_dim * domain_scale
        dy = max_dim * domain_scale
        dz = max_dim * domain_scale

        write(*,*) "Domain box dimensions: dx=", dx, ", dy=", dy, ", dz=", dz
        call create_domain_box(domain_center_x, domain_center_y, domain_center_z, &
                             dx, dy, dz, domain_vol)

        write(*,*) "Setting mesh options..."
        call set_mesh_options(mesh_algorithm_2d, mesh_algorithm_3d, optimize_netgen, &
                            base_mesh_size)

        write(*,*) "Applying boundary layer parameters..."
        call gmsh_option_set_number("Mesh.BoundaryLayerThickness", bl_params%thickness, ierr)
        call gmsh_option_set_number("Mesh.BoundaryLayerProgression", bl_params%progression, ierr)

        write(*,*) "Generating mesh..."
        call gmsh_model_mesh_generate(3, ierr)

        write(*,*) "Writing mesh to file: ", trim(output_msh)
        call gmsh_write(c_output_msh, ierr)

        write(*,*) "Cleaning up allocated memory..."
999     continue
        if (allocated(c_step_file)) deallocate(c_step_file)
        if (allocated(c_output_msh)) deallocate(c_output_msh)
        if (ierr /= 0) then
            write(*,*) "DEBUG: Exiting with error code:", ierr
        end if

        write(*,*) "Mesh generation completed successfully."
        
    contains
        subroutine get_number_of_cores(num_cores)
            integer, intent(out) :: num_cores
            ! Platform specific implementation needed here
            num_cores = 4  ! Default fallback
        end subroutine get_number_of_cores
        
        subroutine create_domain_box(cx, cy, cz, dx, dy, dz, vol_tag)
            real(dp), intent(in) :: cx, cy, cz, dx, dy, dz
            integer, intent(out) :: vol_tag
            call gmsh_model_occ_add_box(cx-dx/2.0_dp, cy-dy/2.0_dp, cz-dz/2.0_dp, dx, dy, dz, vol_tag, ierr)
            call gmsh_model_occ_synchronize(ierr)
        end subroutine create_domain_box
        
        subroutine set_mesh_options(alg2d, alg3d, opt_netgen, base_size)
            integer, intent(in) :: alg2d, alg3d
            logical, intent(in) :: opt_netgen
            real(dp), intent(in) :: base_size
            real(dp) :: opt_val
            
            opt_val = 0.0_dp
            if (opt_netgen) opt_val = 1.0_dp
            
            call gmsh_option_set_number("Mesh.Algorithm", real(alg2d, dp), ierr)
            call gmsh_option_set_number("Mesh.Algorithm3D", real(alg3d, dp), ierr)
            call gmsh_option_set_number("Mesh.OptimizeNetgen", opt_val, ierr)
            call gmsh_option_set_number("Mesh.CharacteristicLengthMin", base_size/5.0_dp, ierr)
            call gmsh_option_set_number("Mesh.CharacteristicLengthMax", base_size, ierr)
        end subroutine set_mesh_options
    end subroutine create_engine_intake_cfd_mesh_surfaces_v5
end module gmsh_process