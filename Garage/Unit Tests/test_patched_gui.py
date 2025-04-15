import os
import sys

class MockNXOpen:
    """Mock NXOpen for testing outside of NX environment"""
    class UI:
        class NXDialog:
            def __init__(self):
                self.title = ""
                self.controls = []
                
            def SetTitle(self, title):
                self.title = title
                
            def AddLabel(self, x, y, text):
                self.controls.append(("Label", x, y, text))
                
            def AddButton(self, x, y, text):
                class Button:
                    def __init__(self, parent, text):
                        self.parent = parent
                        self.text = text
                        self.handlers = []
                        
                    def AddHandler(self, handler):
                        self.handlers.append(handler)
                
                button = Button(self, text)
                self.controls.append(("Button", x, y, button))
                return button
                
            def AddTabControl(self, x, y):
                class TabControl:
                    def __init__(self, parent):
                        self.parent = parent
                        self.tabs = []
                        
                    def AddTab(self, name):
                        tab = MockNXOpen.UI.NXDialog()
                        self.tabs.append((name, tab))
                        return tab
                
                tab_control = TabControl(self)
                self.controls.append(("TabControl", x, y, tab_control))
                return tab_control
                
            def AddReal(self, x, y, default_value):
                class RealInput:
                    def __init__(self, value):
                        self.value = value
                        
                    def GetRealValue(self):
                        return self.value
                
                real_input = RealInput(default_value)
                self.controls.append(("RealInput", x, y, real_input))
                return real_input
                
            def AddInteger(self, x, y, default_value):
                class IntegerInput:
                    def __init__(self, value):
                        self.value = value
                        
                    def GetIntegerValue(self):
                        return self.value
                
                int_input = IntegerInput(default_value)
                self.controls.append(("IntegerInput", x, y, int_input))
                return int_input
                
            def AddString(self, x, y, default_value):
                class StringInput:
                    def __init__(self, value):
                        self.value = value
                        
                    def GetStringValue(self):
                        return self.value
                
                str_input = StringInput(default_value)
                self.controls.append(("StringInput", x, y, str_input))
                return str_input
                
            def AddComboBox(self, x, y, options):
                class ComboBox:
                    def __init__(self, options):
                        self.options = options
                        self.selected = 0
                        
                    def GetSelectedItem(self):
                        return self.selected
                
                combo = ComboBox(options)
                self.controls.append(("ComboBox", x, y, combo))
                return combo
                
            def Show(self):
                print(f"Showing dialog: '{self.title}' with {len(self.controls)} controls")
                
            def Dispose(self):
                print(f"Disposing dialog: '{self.title}'")
        
        @staticmethod
        def GetUI():
            class UI:
                class NXMessageBox:
                    @staticmethod
                    def Show(title, type, message):
                        print(f"MessageBox ({title}): {message}")
            
            return UI()
    
    class Session:
        @staticmethod
        def GetSession():
            class Session:
                class Parts:
                    Work = None
            
            return Session()

def test_patched_gui():
    """
    Test the patched WorkflowGUI class without NX environment
    """
    try:
        # Add mock NXOpen for testing
        sys.modules['NXOpen'] = MockNXOpen
        
        # Import the patch module
        import patch
        
        print("Testing patched WorkflowGUI class")
        
        # Create a basic test class
        class WorkflowGUI:
            def __init__(self):
                print("Original WorkflowGUI initialized")
        
        # Patch the test class
        PatchedGUI = patch.patch_workflow_gui(WorkflowGUI)
        
        # Create an instance to show the GUI
        gui = PatchedGUI()
        print("GUI object created successfully")
        
        # Test the load_preset method
        preset_result = gui.load_preset("Test Preset")
        print(f"load_preset result: {preset_result}")
        
        # Test the show_cfd_gui method
        gui.show_cfd_gui()
        print("show_cfd_gui called successfully")
        
        return True
        
    except Exception as e:
        print(f"Error testing patched GUI: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_patched_gui()
    if success:
        print("Patched GUI test completed successfully")
    else:
        print("Failed to test patched GUI")
