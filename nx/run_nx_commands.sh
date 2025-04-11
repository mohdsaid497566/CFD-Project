#!/bin/bash

# Constants
readonly DEBUG=1
readonly LOG_FILE="/tmp/nx_automation_$(date +%Y%m%d_%H%M%S).log"
readonly NX_PATH_LINUX="/mnt/c/Program Files/Siemens/NX2406/UGII"
readonly NX_PATH_WIN="/mnt/c/Program Files/Siemens/NX2406/UGII"
readonly DESKTOP_PATH_LINUX="/mnt/c/Users/Mohammed/Desktop/nx"
readonly DESKTOP_PATH_WIN="/mnt/c/Users/Mohammed/Desktop/nx"

# Logging functions
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"; }
debug_log() { [[ $DEBUG -eq 1 ]] && log "[DEBUG] $1"; }
error_log() { log "[ERROR] $1"; }

# Function to execute Windows commands
run_cmd() {
    local cmd="$1"
    debug_log "Executing: $cmd"
    if ! cmd.exe /c "$cmd"; then
        error_log "Command failed: $cmd"
        return 1
    fi
}

# Main function to run NX commands
run_nx_commands() {
    local input_prt="$1"
    local express_py="$2"
    local export_py="$3"
    local output_name="$4"

    # Construct Windows paths
    local input_path="${DESKTOP_PATH_WIN}\\${input_prt}"
    local express_path="${DESKTOP_PATH_WIN}\\${express_py}"
    local export_path="${DESKTOP_PATH_WIN}\\${export_py}"
    local output_path="${DESKTOP_PATH_WIN}\\${output_name}.stp"
    local nxcmd_path="${NX_PATH_WIN}"

    # Log input parameters
    debug_log "Input Files:
        PRT: $input_path
        Express Script: $express_path
        Export Script: $export_path
        Output: $output_path"

    # Set environment variables
    export UGII_BASE_DIR="$NX_PATH_LINUX"
    export PATH="$NX_PATH_LINUX/nxbin:$NX_PATH_LINUX/ugii:$PATH"
    export DISPLAY="${DISPLAY:-LOCALPC:0.0}"

    # Initialize NX environment
    debug_log "Initializing NX environment..."
    if ! cd "${NX_PATH_WIN}"; then
        error_log "Failed to change directory to NX path"
        return 1
    fi

    if ! run_cmd "nxcommand.bat"; then
        error_log "Failed to initialize NX environment"
        return 1
    fi


    # Execute journals
    debug_log "Running journals..."
    local journal_cmd="run_journal \"$express_path\" -args \"$input_path\" && \
                      run_journal \"$export_path\" -args \"$output_path\""
    if ! run_cmd "$journal_cmd"; then
        return 1
    fi

    # Verify output
    local output_linux="${DESKTOP_PATH_LINUX}/${output_name}.stp"
    if [[ ! -f "$output_linux" ]]; then
        error_log "STEP file not created: $output_linux"
        return 1
    fi

    debug_log "Operations completed successfully"
    return 0
}

# Main execution
main() {
    local input_file="INSTAKE3D.prt"
    local express_script="nx_express2.py"
    local export_script="nx_export.py"
    local output_name="output_test"

    log "Starting NX automation..."
    if run_nx_commands "$input_file" "$express_script" "$export_script" "$output_name"; then
        log "Script finished successfully"
        return 0
    else
        error_log "Script finished with errors"
        return 1
    fi
}

# Execute main function
main "$@"