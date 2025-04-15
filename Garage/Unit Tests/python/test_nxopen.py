try:
    import NXOpen
    import NXOpen.UI
    
    def show_test_dialog():
        # Create a simple dialog
        dialog = NXOpen.UI.NXDialog()
        dialog.SetTitle("NXOpen Test")
        
        # Add a label
        dialog.AddLabel(10, 10, "NXOpen is working correctly!")
        
        # Add a button
        closeButton = dialog.AddButton(10, 50, "Close")
        
        # Add handler for the button
        def close_callback():
            dialog.Dispose()
        
        closeButton.AddHandler(close_callback)
        
        # Show the dialog
        dialog.Show()
    
    # Show the test dialog
    show_test_dialog()
    print("Test dialog displayed successfully")
    
except ImportError as e:
    print(f"Error: NXOpen not available in this environment - {str(e)}")
    print("This script must be run within NX")
except Exception as e:
    print(f"Error creating test dialog: {str(e)}")
