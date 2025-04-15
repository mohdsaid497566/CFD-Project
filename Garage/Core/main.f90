program main
    use gmsh_process
    use gmsh_interface
    use, intrinsic :: iso_fortran_env, only: error_unit
    implicit none

    character(len=100) :: step_file, output_msh
    type(boundary_layer_type) :: bl_params
    integer :: ierr
    logical :: file_exists

    ! Set input parameters
    step_file = "INTAKE3D.stp"
    output_msh = "INTAKE3D_surface_domain_v5.msh"

    write(*,*) "Starting the program..."

    ! Check if input file exists
    inquire(file=step_file, exist=file_exists)
    if (.not. file_exists) then
        write(error_unit,*) "Error: Input file ", trim(step_file), " not found"
        stop 1
    end if
    write(*,*) "Input file found: ", trim(step_file)

    bl_params%first_layer_thickness = 0.05_dp
    bl_params%progression = 1.2_dp
    bl_params%thickness = 0.5_dp
    bl_params%num_layers = 10

    write(*,*) "Boundary layer parameters set."

    ! Call the mesh generation subroutine
    write(*,*) "Calling the mesh generation subroutine..."
    call create_engine_intake_cfd_mesh_surfaces_v5( &
        step_file, output_msh, 5.0_dp, 0.5_dp, bl_params, &
        10, 5, 0, .true., ierr)

    if (ierr /= 0) then
        write(error_unit,*) "Error in mesh generation. ierr = ", ierr
        stop 1
    end if

    ! Explicitly finalize Gmsh before exiting
    write(*,*) "Finalizing Gmsh..."
    call gmsh_finalize()
    write(*,*) "Program completed successfully. Output mesh: ", trim(output_msh)
end program main
