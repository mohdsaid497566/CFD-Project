# Main.py Documentation

This document provides a comprehensive overview of all functions, methods, and classes found in the `main.py` file of the Intake CFD Optimization Suite.

## Global Variables

- **DEMO_MODE** (boolean): Flag for controlling demonstration mode. When enabled, actual execution of external processes is simulated. ✅ Fully implemented and functional.
- **PARAMIKO_AVAILABLE** (boolean): Flag indicating whether the paramiko SSH library is available. ✅ Fully implemented and functional.

## Utility Functions

### run_command(command, cwd=None, timeout=300)
**Description**: Executes shell commands with timeout and logging capabilities. Handles demo mode, file not found errors, and exceptions.  
**Implementation Status**: ✅ Fully implemented and functional.

### is_wsl()
**Description**: Checks if the code is running within Windows Subsystem for Linux (WSL) environment.  
**Implementation Status**: ✅ Fully implemented and functional.

### get_nx_command()
**Description**: Identifies and validates the path to the Siemens NX executable based on the platform (WSL or Windows).  
**Implementation Status**: ✅ Fully implemented and functional.

### create_mock_executables()
**Description**: Creates mock script files and directories for demonstration purposes when real executables are not available.  
**Implementation Status**: ✅ Fully implemented and functional.

### exp(L4, L5, alpha1, alpha2, alpha3)
**Description**: Generates parameter expressions and exports them to an expressions file for NX integration.  
**Implementation Status**: ✅ Fully implemented and functional.

### run_nx_workflow()
**Description**: Manages the NX geometry modification and STEP export process.  
**Implementation Status**: ✅ Fully implemented with both real and demo mode support.

### process_mesh(step_file, mesh_file)
**Description**: Processes STEP geometry files with GMSH to produce mesh files for CFD simulation.  
**Implementation Status**: ✅ Fully implemented with both real and demo mode support.

### run_cfd(mesh_file)
**Description**: Executes the CFD solver on the generated mesh file.  
**Implementation Status**: ✅ Fully implemented with both real and demo mode support.

### process_results(results_dir, output_file)
**Description**: Processes CFD simulation results to create summary output files.  
**Implementation Status**: ✅ Fully implemented with both real and demo mode support.

### run_tests()
**Description**: Runs unit tests with enhanced error handling.  
**Implementation Status**: ✅ Fully implemented but skipped in demo mode.

### setup_app_header(root, theme)
**Description**: Sets up the application header with logo and title.  
**Implementation Status**: ✅ Fully implemented and functional.

## Classes

### ModernTheme
**Description**: Defines modern styling settings for the application including colors, fonts, and padding.  
**Implementation Status**: ✅ Fully implemented and functional.

#### Methods:
- **__init__()**: Initializes theme settings. ✅ Fully implemented.
- **apply_theme(root)**: Applies the theme styling to the application. ✅ Fully implemented.

### WorkflowGUI
**Description**: Main GUI class for the Intake CFD Optimization Suite.  
**Implementation Status**: ✅ Mostly implemented but some features are placeholders.

#### Methods:
- **__init__(root)**: Initializes the GUI with tabs, frames, and components. ✅ Fully implemented.
- **setup_app_header()**: Sets up the application header. ✅ Fully implemented.
- **create_hpc_tab()**: Creates the HPC tab with connection and job management features. ✅ Fully implemented UI, but some backend functionality is not implemented.
- **toggle_auth_type()**: Toggles between password and key authentication display. ✅ Fully implemented.
- **select_key_file()**: Opens file dialog to select SSH key file. ✅ Fully implemented.
- **save_hpc_profile_dialog()**: Shows dialog to save HPC connection profile. ✅ Fully implemented.
- **delete_hpc_profile()**: Deletes the selected HPC profile. ✅ Fully implemented.
- **load_hpc_profiles()**: Loads saved HPC profiles. ✅ Fully implemented.
- **get_hpc_config()**: Gets HPC configuration from UI. ✅ Fully implemented.
- **test_hpc_connection()**: Tests connection to HPC system. ✅ Fully implemented.
- **update_connection_result(success, message)**: Updates the UI with connection test results. ✅ Fully implemented.
- **connect_to_hpc()**: Connects to HPC system. ❌ Not fully implemented (placeholder).
- **disconnect_from_hpc()**: Disconnects from HPC system. ✅ Partially implemented (UI updates only).
- **refresh_job_list()**: Refreshes the HPC job list. ❌ Not implemented (placeholder).
- **submit_job()**: Shows dialog to submit a new HPC job. ❌ Not implemented (placeholder).
- **cancel_job()**: Cancels a selected HPC job. ❌ Not implemented (placeholder).
- **show_job_details()**: Shows details for a selected HPC job. ❌ Not implemented (placeholder).
- **download_results()**: Downloads results from a selected HPC job. ❌ Not implemented (placeholder).
- **setup_workflow_tab()**: Sets up the Workflow tab. ✅ Fully implemented.
- **setup_visualization_tab()**: Sets up the Visualization tab. ✅ Fully implemented.
- **create_demo_visualization()**: Creates a demo visualization when no data is loaded. ✅ Fully implemented.
- **update_visualization()**: Updates the visualization based on control settings. ✅ Fully implemented.
- **load_visualization_data()**: Loads CFD data for visualization. ✅ Partially implemented (simulated data).
- **data_loading_complete()**: Called when data loading simulation is complete. ✅ Fully implemented.
- **export_visualization()**: Exports the current visualization as an image. ✅ Fully implemented.
- **reset_visualization()**: Resets visualization to default settings. ✅ Fully implemented.
- **toggle_execution_environment()**: Toggles between local and HPC execution environments. ✅ Fully implemented.
- **load_hpc_profiles_for_workflow()**: Loads HPC profiles for the workflow tab. ✅ Fully implemented.
- **toggle_opt_execution_environment()**: Toggles between local and HPC execution environments for optimization. ✅ Fully implemented.
- **load_hpc_profiles_for_opt()**: Loads HPC profiles for the optimization tab. ✅ Fully implemented.
- **initialize_convergence_plot()**: Initializes the convergence history plot. ✅ Fully implemented.
- **initialize_pareto_front()**: Initializes the Pareto front plot for multi-objective optimization. ✅ Fully implemented.
- **_create_workflow_steps()**: Creates workflow visualization steps in the canvas. ✅ Fully implemented.
- **_redraw_workflow()**: Redraws workflow steps on the canvas. ✅ Fully implemented.
- **_step_clicked(event)**: Handles clicks on workflow steps in the canvas. ✅ Fully implemented.
- **setup_optimization_tab()**: Sets up the Optimization tab. ✅ Fully implemented UI, but backend optimization functionality is not fully implemented.
- **setup_settings_tab()**: Sets up the Settings tab. ✅ Fully implemented UI, but some settings functionality is not fully implemented.
- **get_memory_info()**: Gets system memory information. ⚠️ Implementation status unclear.
- **browse_nx_path()**: Opens file browser to select NX path. ⚠️ Implementation status unclear.
- **browse_project_dir()**: Opens directory browser to select project directory. ⚠️ Implementation status unclear.
- **apply_appearance_settings()**: Applies appearance setting changes. ⚠️ Implementation status unclear.
- **apply_dark_theme()**: Applies dark theme. ⚠️ Implementation status unclear.
- **apply_light_theme()**: Applies light theme. ⚠️ Implementation status unclear.
- **apply_system_theme()**: Applies system theme. ⚠️ Implementation status unclear.
- **apply_font_size(small, normal, large)**: Applies font size changes. ⚠️ Implementation status unclear.
- **update_memory_display()**: Updates the memory usage display. ⚠️ Implementation status unclear.
- **save_settings()**: Saves application settings. ⚠️ Implementation status unclear.
- **load_settings()**: Loads application settings. ⚠️ Implementation status unclear.
- **reset_settings()**: Resets settings to default values. ⚠️ Implementation status unclear.
- **check_updates()**: Checks for application updates. ⚠️ Implementation status unclear.
- **run_diagnostics()**: Runs system diagnostics. ⚠️ Implementation status unclear.
- **_run_diagnostics_thread()**: Background thread for running diagnostics. ⚠️ Implementation status unclear.
- **_show_diagnostics_result(results)**: Shows diagnostic results. ⚠️ Implementation status unclear.
- **_show_diagnostics_error(error_message)**: Shows diagnostic error messages. ⚠️ Implementation status unclear.
- **run_workflow()**: Executes the CFD workflow. ⚠️ Implementation status unclear.
- **_validate_workflow_inputs()**: Validates workflow input parameters. ⚠️ Implementation status unclear.
- **_run_workflow_thread(L4, L5, alpha1, alpha2, alpha3)**: Background thread for running the workflow. ⚠️ Implementation status unclear.
- **_update_workflow_status(message)**: Updates workflow status display. ⚠️ Implementation status unclear.
- **_update_workflow_step(step_name, status)**: Updates status of a workflow step. ⚠️ Implementation status unclear.
- **_load_and_display_results(results_file, L4, L5, alpha1, alpha2, alpha3)**: Loads and displays workflow results. ⚠️ Implementation status unclear.
- **_workflow_completed()**: Handles workflow completion. ⚠️ Implementation status unclear.
- **_workflow_canceled()**: Handles workflow cancellation. ⚠️ Implementation status unclear.
- **_workflow_failed(error_message)**: Handles workflow failure. ⚠️ Implementation status unclear.
- **cancel_workflow()**: Cancels the running workflow. ⚠️ Implementation status unclear.

## Main Function

### main()
**Description**: Main entry point for the Intake CFD Optimization Suite application.  
**Implementation Status**: ✅ Fully implemented with argument parsing and exception handling.

## Summary

The Intake CFD Optimization Suite is a comprehensive application for CFD simulation workflow management. The main.py file implements:

1. A modern GUI interface with multiple tabs for different aspects of CFD simulation
2. Workflow management for NX geometry, mesh generation, CFD simulation, and results processing
3. Visualization capabilities for CFD results
4. Optimization tools for parameter studies
5. HPC integration for remote execution
6. Settings and configuration management

While the core functionality (workflow execution in demo mode and GUI) is implemented, some advanced features (real HPC job submission, advanced optimization algorithms, etc.) are only partially implemented or are placeholders for future development.

The application uses a demo mode to allow functionality testing without requiring all external dependencies to be installed, making it accessible for demonstrations and testing.