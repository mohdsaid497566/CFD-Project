import NXOpen
import os
import sys

# Add the directory containing patch.py to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    # Import the patch module
    import patch
    
    # Launch the GUI
    patch.patch_workflow_gui()
    print("GUI launched successfully")
    
except Exception as ex:
    print(f"Error launching GUI: {str(ex)}")
    
    # Try to show the error in an NX message box as well
    try:
        NXOpen.UI.GetUI().NXMessageBox.Show(
            "Error", 
            NXOpen.UI.MessageBoxType.Error, 
            f"Error launching GUI: {str(ex)}")
    except:
        pass
