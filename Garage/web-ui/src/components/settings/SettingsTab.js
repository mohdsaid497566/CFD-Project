import React, { useState, useEffect } from 'react';
import { useSettingsService } from '../../services/SettingsService';
import './Settings.css';

const SettingsTab = () => {
  const settingsService = useSettingsService();
  const [settings, setSettings] = useState(settingsService.getSettings());
  const [saveStatus, setSaveStatus] = useState({ message: '', type: '' });

  // Save settings when changed
  const handleSettingChange = (key, value) => {
    try {
      const newSettings = { ...settings, [key]: value };
      setSettings(newSettings);
      const success = settingsService.saveSettings(newSettings);
      
      if (success) {
        setSaveStatus({ message: 'Settings saved successfully', type: 'success' });
      } else {
        setSaveStatus({ message: 'Failed to save settings', type: 'error' });
      }
      
      // Clear status after 3 seconds
      setTimeout(() => {
        setSaveStatus({ message: '', type: '' });
      }, 3000);
    } catch (error) {
      console.error('Error saving setting:', error);
      setSaveStatus({ message: 'Error saving settings', type: 'error' });
    }
  };

  // Reset settings to default
  const handleReset = () => {
    try {
      const success = settingsService.resetSettings();
      setSettings(settingsService.getSettings());
      
      if (success) {
        setSaveStatus({ message: 'Settings reset to defaults', type: 'success' });
      } else {
        setSaveStatus({ message: 'Failed to reset settings', type: 'error' });
      }
      
      setTimeout(() => {
        setSaveStatus({ message: '', type: '' });
      }, 3000);
    } catch (error) {
      console.error('Error resetting settings:', error);
      setSaveStatus({ message: 'Error resetting settings', type: 'error' });
    }
  };

  return (
    <div className="settings-container">
      <h2>Settings</h2>
      
      {saveStatus.message && (
        <div className={`status-message ${saveStatus.type}`}>
          {saveStatus.message}
        </div>
      )}
      
      <div className="settings-section">
        <h3>General Settings</h3>
        
        <div className="setting-item">
          <label htmlFor="debugMode">Debug Mode</label>
          <input
            type="checkbox"
            id="debugMode"
            checked={settings.debugMode || false}
            onChange={(e) => handleSettingChange('debugMode', e.target.checked)}
          />
        </div>

        <div className="setting-item">
          <label htmlFor="autoSave">Auto Save (minutes)</label>
          <input
            type="number"
            id="autoSave"
            value={settings.autoSaveInterval || 5}
            min="1"
            max="60"
            onChange={(e) => handleSettingChange('autoSaveInterval', parseInt(e.target.value) || 5)}
          />
        </div>
      </div>

      <div className="settings-section">
        <h3>Appearance</h3>
        
        <div className="setting-item">
          <label htmlFor="theme">Theme</label>
          <select
            id="theme"
            value={settings.theme || 'light'}
            onChange={(e) => handleSettingChange('theme', e.target.value)}
          >
            <option value="light">Light</option>
            <option value="dark">Dark</option>
            <option value="system">System Default</option>
          </select>
        </div>

        <div className="setting-item">
          <label htmlFor="fontSize">Font Size</label>
          <select
            id="fontSize"
            value={settings.fontSize || 'medium'}
            onChange={(e) => handleSettingChange('fontSize', e.target.value)}
          >
            <option value="small">Small</option>
            <option value="medium">Medium</option>
            <option value="large">Large</option>
          </select>
        </div>
      </div>

      <div className="settings-section">
        <h3>CFD Settings</h3>
        
        <div className="setting-item">
          <label htmlFor="defaultMeshSize">Default Mesh Size</label>
          <input
            type="number"
            id="defaultMeshSize"
            value={settings.defaultMeshSize || 0.01}
            step="0.001"
            min="0.001"
            onChange={(e) => handleSettingChange('defaultMeshSize', parseFloat(e.target.value) || 0.01)}
          />
        </div>

        <div className="setting-item">
          <label htmlFor="solverType">Solver Type</label>
          <select
            id="solverType"
            value={settings.solverType || 'simpleFoam'}
            onChange={(e) => handleSettingChange('solverType', e.target.value)}
          >
            <option value="simpleFoam">simpleFoam</option>
            <option value="pimpleFoam">pimpleFoam</option>
            <option value="potentialFoam">potentialFoam</option>
          </select>
        </div>
      </div>

      <div className="settings-section">
        <h3>Settings Management</h3>
        <div className="settings-buttons">
          <button 
            className="settings-btn export-btn"
            onClick={() => settingsService.exportSettings()}
          >
            Export Settings
          </button>
          
          <button 
            className="settings-btn reset-btn"
            onClick={handleReset}
          >
            Reset to Defaults
          </button>
        </div>
        
        <div className="setting-item">
          <label htmlFor="importSettings">Import Settings</label>
          <input
            type="file"
            id="importSettings"
            accept=".json"
            onChange={(e) => {
              const file = e.target.files[0];
              if (file) {
                settingsService.importSettings(file, setSettings);
              }
            }}
          />
        </div>
      </div>
    </div>
  );
};

export default SettingsTab;
