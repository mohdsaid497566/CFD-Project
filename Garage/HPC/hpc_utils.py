def update_hpc_info(workflow_gui, hpc_info=None):
    """
    Updates the HPC information in the workflow GUI.
    
    Parameters:
    -----------
    workflow_gui : object
        The workflow GUI object that needs to be updated
    hpc_info : dict, optional
        Dictionary containing HPC information (servers, configurations, etc.)
        If None, the function will try to fetch the latest information
    
    Returns:
    --------
    bool
        True if the update was successful, False otherwise
    """
    try:
        # If no HPC info is provided, try to fetch it
        if hpc_info is None:
            from .hpc_connection import get_hpc_info
            hpc_info = get_hpc_info()
        
        # Update server list in GUI
        if hasattr(workflow_gui, 'hpc_server_combo') and 'servers' in hpc_info:
            workflow_gui.hpc_server_combo.clear()
            for server in hpc_info['servers']:
                workflow_gui.hpc_server_combo.addItem(server['name'])
        
        # Update resource options
        if hasattr(workflow_gui, 'hpc_resource_combo') and 'resources' in hpc_info:
            workflow_gui.hpc_resource_combo.clear()
            for resource in hpc_info['resources']:
                workflow_gui.hpc_resource_combo.addItem(resource['name'])
        
        # Update status indicator
        if hasattr(workflow_gui, 'hpc_status_label'):
            workflow_gui.hpc_status_label.setText("HPC: Connected")
            workflow_gui.hpc_status_label.setStyleSheet("color: green;")
        
        # Store HPC info in the workflow GUI for later use
        workflow_gui.hpc_info = hpc_info
        
        return True
        
    except Exception as e:
        # Handle errors
        import traceback
        print(f"Error updating HPC info: {str(e)}")
        print(traceback.format_exc())
        
        # Update status indicator to show error
        if hasattr(workflow_gui, 'hpc_status_label'):
            workflow_gui.hpc_status_label.setText("HPC: Error")
            workflow_gui.hpc_status_label.setStyleSheet("color: red;")
        
        return False
