import React from 'react';
import { useSettingsService } from '../src/services/SettingsService';

const ThemeSettings = () => {
  const { settings, saveSettings } = useSettingsService();
  
  // Get current settings or use defaults
  const theme = settings.theme || 'light';
  const fontSize = settings.fontSize || 'medium';
  const accentColor = settings.accentColor || '#1976d2';
  const enableAnimations = settings.enableAnimations !== undefined ? settings.enableAnimations : true;

  const handleThemeChange = (e) => {
    saveSettings({
      ...settings,
      theme: e.target.value
    });
  };

  const handleFontSizeChange = (e) => {
    saveSettings({
      ...settings,
      fontSize: e.target.value
    });
  };

  const handleAccentColorChange = (e) => {
    saveSettings({
      ...settings,
      accentColor: e.target.value
    });
  };

  const handleAnimationsChange = (e) => {
    saveSettings({
      ...settings,
      enableAnimations: e.target.checked
    });
  };

  const resetToDefaults = () => {
    const defaultThemeSettings = {
      ...settings,
      theme: 'light',
      fontSize: 'medium',
      accentColor: '#1976d2',
      enableAnimations: true
    };
    saveSettings(defaultThemeSettings);
  };

  return (
    <div className="theme-settings-container">
      <h2>Theme Settings</h2>
      
      <div className="setting-group">
        <label>Application Theme</label>
        <select 
          value={theme} 
          onChange={handleThemeChange}
        >
          <option value="light">Light</option>
          <option value="dark">Dark</option>
          <option value="system">System Default</option>
        </select>
      </div>
      
      <div className="setting-group">
        <label>Font Size</label>
        <select 
          value={fontSize} 
          onChange={handleFontSizeChange}
        >
          <option value="small">Small</option>
          <option value="medium">Medium</option>
          <option value="large">Large</option>
          <option value="x-large">X-Large</option>
        </select>
      </div>
      
      <div className="setting-group">
        <label>Accent Color</label>
        <input
          type="color"
          value={accentColor}
          onChange={handleAccentColorChange}
        />
      </div>
      
      <div className="setting-group">
        <label>
          <input
            type="checkbox"
            checked={enableAnimations}
            onChange={handleAnimationsChange}
          />
          Enable UI animations
        </label>
      </div>
      
      <div className="theme-controls">
        <button className="reset-defaults" onClick={resetToDefaults}>Reset to Defaults</button>
      </div>
    </div>
  );
};

export default ThemeSettings;