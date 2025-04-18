import unittest
import threading
import time
import os
import json
import sys
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QFontDialog, QComboBox, QVBoxLayout
from PyQt5.QtCore import QMetaObject, Qt, Q_ARG, QObject, pyqtSignal, QThread, QTimer, QEventLoop
from PyQt5.QtGui import QFont

class TestDisplaySettings(unittest.TestCase):
    def setUp(self):
        if QApplication.instance() is None:
            self.app = QApplication(['--no-sandbox'])
            self.owns_app = True
        else:
            self.app = QApplication.instance()
            self.owns_app = False
            
        self.widget = QWidget(None)
        self.widget.setObjectName("MainTestWidget")
        
        self.pressure_value = QLabel(self.widget)
        self.temperature_value = QLabel(self.widget)
        self.flow_rate_value = QLabel(self.widget)
        
        self.update_signal = UpdateSignal()
        self.update_signal.signal.connect(self._safe_update_ui)
        
        self.root = self.widget
        self.log_messages = []
        self.config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_config")
        os.makedirs(self.config_dir, exist_ok=True)
        
        self.memory_widget = None
        self.memory_usage_data = [10, 20, 30, 40, 50]
        
        self.font_combo = QComboBox(self.widget)
        self.font_combo.addItems(['Arial', 'Times New Roman', 'Courier New'])
        self.font_size_combo = QComboBox(self.widget)
        self.font_size_combo.addItems(['8', '10', '12', '14', '16'])
        
        self.parallel_settings = {
            "use_parallel": True,
            "max_processes": 4,
            "chunk_size": 100
        }

        if hasattr(self.app, 'processEvents'):
            self.app.processEvents()
        
        self.is_main_thread_ready = True
        
        self.main_layout = QVBoxLayout(self.widget)
        self.widget.setLayout(self.main_layout)
        
        self.main_layout.addWidget(self.pressure_value)
        self.main_layout.addWidget(self.temperature_value)
        self.main_layout.addWidget(self.flow_rate_value)
        self.main_layout.addWidget(self.font_combo)
        self.main_layout.addWidget(self.font_size_combo)
        
        self.widget.show()
        self.app.processEvents()

    def log(self, message):
        print(message)
        if not hasattr(self, 'log_messages'):
            self.log_messages = []
        self.log_messages.append(message)

    def update_ui_elements(self, data):
        self.update_signal.signal.emit(data)

    def _safe_update_ui(self, data):
        if 'pressure' in data:
            self.pressure_value.setText(str(data['pressure']))
        if 'temperature' in data:
            self.temperature_value.setText(str(data['temperature']))
        if 'flow_rate' in data:
            self.flow_rate_value.setText(str(data['flow_rate']))
        if 'log_message' in data:
            self.log(data['log_message'])
        
        if 'action' in data and data['action'] == 'run_callback':
            if 'callback' in data and callable(data['callback']):
                try:
                    data['callback']()
                except Exception as e:
                    print(f"Error executing callback: {str(e)}")
        
        self.app.processEvents()

    def process_data_from_thread(self, data):
        self.update_ui_elements(data)

    def after(self, delay_ms, callback):
        if threading.current_thread() is not threading.main_thread():
            self.update_signal.signal.emit({
                'action': 'run_callback',
                'callback': callback,
                'log_message': f"Scheduled callback via signal after {delay_ms}ms"
            })
        else:
            QTimer.singleShot(delay_ms, callback)
        return "timer_id"

    def background_task(self):
        for i in range(10):
            try:
                if hasattr(self.app, 'log'):
                    data = {"log_message": f"Background log {i}"}
                    self.update_ui_elements(data)
                else:
                    self.after(0, lambda x=i: self.log(f"Background log {x}"))
                time.sleep(0.1)
            except Exception as e:
                print(f"Error in background task: {e}")

    def apply_font_changes(self, widget_list=None, font_name=None, font_size=None, font_weight=None):
        if widget_list is None:
            widget_list = []
            
        valid_widgets = []
        for widget in widget_list:
            if widget and not widget.isDestroyed():
                valid_widgets.append(widget)
        
        done_event = threading.Event()
        result_container = {'success': False}
        
        def _apply_font():
            try:
                font = QFont()
                if font_name:
                    font.setFamily(font_name)
                if font_size:
                    font.setPointSize(font_size)
                if font_weight:
                    font.setWeight(font_weight)
                
                success_count = 0    
                for widget in valid_widgets:
                    if hasattr(widget, 'setFont'):
                        widget.setFont(font)
                        widget.update()
                        success_count += 1
                
                self.app.processEvents()
                result_container['success'] = success_count > 0
            except Exception as e:
                print(f"Error applying font: {str(e)}", file=sys.stderr)
                result_container['success'] = False
            finally:
                done_event.set()
        
        if threading.current_thread() is not threading.main_thread():
            self.update_signal.signal.emit({
                'action': 'run_callback',
                'callback': _apply_font,
                'log_message': "Applying font changes via signal"
            })
            done_event.wait(timeout=2.0)
        else:
            _apply_font()
        
        return result_container['success']
    
    def create_memory_visualizer(self, parent=None):
        result_container = {'widget': None}
        done_event = threading.Event()
        
        def _create_widget():
            try:
                parent_widget = parent if parent else self.widget
                widget = QWidget(parent_widget)
                widget.setObjectName("MemoryVisualizer")
                
                layout = QVBoxLayout(widget)
                layout.setContentsMargins(10, 10, 10, 10)
                
                for i, value in enumerate(self.memory_usage_data):
                    label = QLabel(f"Memory usage: {value}MB", widget)
                    label.setObjectName(f"MemoryLabel{i}")
                    layout.addWidget(label)
                
                widget.show()
                widget.raise_()
                
                self.memory_widget = widget
                result_container['widget'] = widget
                self.app.processEvents()
            except Exception as e:
                print(f"Error creating memory visualizer: {str(e)}", file=sys.stderr)
            finally:
                done_event.set()
        
        if threading.current_thread() is not threading.main_thread():
            self.update_signal.signal.emit({
                'action': 'run_callback',
                'callback': _create_widget,
                'log_message': "Creating memory visualizer via signal"
            })
            done_event.wait(timeout=2.0)
        else:
            _create_widget()
        
        return result_container['widget']
    
    def save_parallel_settings(self, settings=None):
        if settings is None:
            settings = self.parallel_settings
        
        config_dir = os.path.abspath(self.config_dir)
        try:
            if not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)
        except Exception as e:
            print(f"Error creating config directory: {str(e)}", file=sys.stderr)
            return False
            
        settings_file = os.path.join(config_dir, "parallel_settings.json")
        
        try:
            if not os.access(os.path.dirname(settings_file), os.W_OK):
                settings_file = os.path.join(os.path.expanduser("~"), "parallel_settings.json")
            
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=4)
            
            if not os.path.exists(settings_file) or os.path.getsize(settings_file) == 0:
                return False
                
            return True
        except Exception as e:
            print(f"Error saving parallel settings: {str(e)}", file=sys.stderr)
            return False
    
    def load_parallel_settings(self):
        for settings_dir in [self.config_dir, os.path.expanduser("~")]:
            settings_file = os.path.join(settings_dir, "parallel_settings.json")
            if os.path.exists(settings_file):
                try:
                    with open(settings_file, 'r') as f:
                        settings = json.load(f)
                    return settings
                except Exception as e:
                    print(f"Error loading settings from {settings_file}: {str(e)}", file=sys.stderr)
        
        return self.parallel_settings
    
    def wait_for_ui_update(self, timeout_ms=500):
        end_time = time.time() + (timeout_ms / 1000.0)
        while time.time() < end_time:
            self.app.processEvents()
            time.sleep(0.01)
    
    def test_ui_update(self):
        data = {'pressure': 101.3, 'temperature': 25.0, 'flow_rate': 10.5}
        self.process_data_from_thread(data)
        self.assertEqual(self.pressure_value.text(), '101.3')
        self.assertEqual(self.temperature_value.text(), '25.0')
        self.assertEqual(self.flow_rate_value.text(), '10.5')

    def test_display_update_during_intensive_operations(self):
        thread = threading.Thread(target=self.background_task, name="Thread-1")
        thread.daemon = True
        thread.start()
        
        for _ in range(5):
            self.app.processEvents()
            time.sleep(0.1)
        
        thread.join(timeout=1.0)
        self.assertTrue(len(self.log_messages) > 0, "No log messages were recorded")

    def test_apply_font_changes_comprehensive(self):
        label1 = QLabel("Test Label 1", self.widget)
        label2 = QLabel("Test Label 2", self.widget)
        label3 = QLabel("Test Label 3", self.widget)
        
        self.main_layout.addWidget(label1)
        self.main_layout.addWidget(label2)
        self.main_layout.addWidget(label3)
        
        label1.show()
        label2.show()
        label3.show()
        
        self.app.processEvents()
        
        widgets = [label1, label2, label3]
        result = self.apply_font_changes(widgets, font_name="Arial", font_size=12)
        
        self.wait_for_ui_update(1000)
        
        self.assertTrue(result, "Font changes should have been applied successfully")
        self.assertEqual(label1.font().family(), "Arial", "Font family should be Arial")
        self.assertEqual(label1.font().pointSize(), 12, "Font size should be 12")
    
    def test_memory_visualizer_creation(self):
        visualizer = self.create_memory_visualizer()
        self.wait_for_ui_update(1000)
        self.assertIsNotNone(visualizer, "Visualizer should not be None")
        
        if visualizer:
            self.assertIsInstance(visualizer, QWidget, "Visualizer should be a QWidget")
            self.assertTrue(visualizer.isVisible(), "Visualizer should be visible")
            self.assertEqual(visualizer.layout().count(), len(self.memory_usage_data), 
                            "Visualizer should have one widget per data point")
    
    def test_save_load_parallel_settings(self):
        test_settings = {
            "use_parallel": True,
            "max_processes": 8,
            "chunk_size": 200,
            "test_value": "test string with unicode: 汉字"
        }
        
        save_result = self.save_parallel_settings(test_settings)
        self.assertTrue(save_result, "Settings should save successfully")
        
        settings_file = os.path.join(self.config_dir, "parallel_settings.json")
        alternate_file = os.path.join(os.path.expanduser("~"), "parallel_settings.json")
        
        found_file = ""
        if os.path.exists(settings_file):
            found_file = settings_file
        elif os.path.exists(alternate_file):
            found_file = alternate_file
            
        self.assertTrue(bool(found_file), "Settings file should exist")
        
        loaded_settings = self.load_parallel_settings()
        
        self.assertEqual(loaded_settings.get("max_processes"), 8, 
                         "max_processes should be 8")
        self.assertEqual(loaded_settings.get("chunk_size"), 200, 
                         "chunk_size should be 200")
        self.assertEqual(loaded_settings.get("test_value"), "test string with unicode: 汉字", 
                         "Complex string should be preserved")
        
        self.assertEqual(loaded_settings.get("use_parallel"), True, 
                         "use_parallel should be preserved")

    def tearDown(self):
        try:
            settings_file = os.path.join(self.config_dir, "parallel_settings.json")
            alternate_file = os.path.join(os.path.expanduser("~"), "parallel_settings.json")
            
            for file_path in [settings_file, alternate_file]:
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        print(f"Error removing settings file {file_path}: {str(e)}", file=sys.stderr)
        except Exception as e:
            print(f"Error in tearDown: {str(e)}", file=sys.stderr)
        
        try:
            QApplication.processEvents()
            if hasattr(self, 'owns_app') and self.owns_app and self.app:
                self.app = None
        except Exception as e:
            print(f"Error cleaning up QApplication: {str(e)}", file=sys.stderr)

class UpdateSignal(QObject):
    signal = pyqtSignal(dict)

if __name__ == "__main__":
    unittest.main()