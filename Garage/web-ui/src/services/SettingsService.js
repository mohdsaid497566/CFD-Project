import React, { createContext, useContext, useState, useEffect } from 'react';

// Default settings
const DEFAULT_SETTINGS = {
  // General settings
  debugMode: false,
  autoSaveInterval: 5,
  
  // Appearance settings
  theme: 'light',
  fontSize: 'medium',
  accentColor: '#1976d2',
  enableAnimations: true,
  
  // Simulation settings
  defaultMeshSize: 0.01,
  solverType: 'simpleFoam',
  viscosity: 1.8e-5,
  density: 1.225,
  
  // Advanced settings
  threads: 4,
  memoryLimit: 70,
  
  // Other preferences
  lastOpenedProject: '',
  recentProjects: [],
};

const SettingsContext = createContext(null);

export const SettingsProvider = ({ children }) => {
  const [settings, setSettings] = useState(() => {
    try {
      // Load settings from localStorage on init
      const savedSettings = localStorage.getItem('cfd-app-settings');
      return savedSettings ? { ...DEFAULT_SETTINGS, ...JSON.parse(savedSettings) } : DEFAULT_SETTINGS;
    } catch (error) {
      console.error('Failed to load settings:', error);
      return DEFAULT_SETTINGS;
    }
  });

  // Apply global settings whenever they change
  useEffect(() => {
    try {
      // Apply theme
      document.documentElement.setAttribute('data-theme', settings.theme);
      
      // Apply font size
      const fontSizeMap = {
        small: '14px',
        medium: '16px',
        large: '18px',
        'x-large': '20px'
      };
      document.documentElement.style.fontSize = fontSizeMap[settings.fontSize] || '16px';
      
      // Add CSS variables for theme colors
      const root = document.documentElement;
      
      // Apply accent color
      root.style.setProperty('--accent-color', settings.accentColor || '#1976d2');
      
      // Apply theme colors
      if (settings.theme === 'dark') {
        root.style.setProperty('--background-color', '#121212');
        root.style.setProperty('--text-color', '#e0e0e0');
        root.style.setProperty('--card-bg', '#1e1e1e');
        root.style.setProperty('--border-color', '#444');
        root.style.setProperty('--input-bg', '#333');
        root.style.setProperty('--primary-color', settings.accentColor || '#90caf9');
        root.style.setProperty('--secondary-bg', '#2a2a2a');
        root.style.setProperty('--hover-color', 'rgba(255, 255, 255, 0.08)');
      } else if (settings.theme === 'system') {
        // Use system preference
        const prefersDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
        if (prefersDarkMode) {
          root.style.setProperty('--background-color', '#121212');
          root.style.setProperty('--text-color', '#e0e0e0');
          root.style.setProperty('--card-bg', '#1e1e1e');
          root.style.setProperty('--border-color', '#444');
          root.style.setProperty('--input-bg', '#333');
          root.style.setProperty('--primary-color', settings.accentColor || '#90caf9');
          root.style.setProperty('--secondary-bg', '#2a2a2a');
          root.style.setProperty('--hover-color', 'rgba(255, 255, 255, 0.08)');
        } else {
          root.style.setProperty('--background-color', '#ffffff');
          root.style.setProperty('--text-color', '#333333');
          root.style.setProperty('--card-bg', '#f5f5f5');
          root.style.setProperty('--border-color', '#e0e0e0');
          root.style.setProperty('--input-bg', '#ffffff');
          root.style.setProperty('--primary-color', settings.accentColor || '#1976d2');
          root.style.setProperty('--secondary-bg', '#f9f9f9');
          root.style.setProperty('--hover-color', 'rgba(0, 0, 0, 0.04)');
        }
      } else {
        root.style.setProperty('--background-color', '#ffffff');
        root.style.setProperty('--text-color', '#333333');
        root.style.setProperty('--card-bg', '#f5f5f5');
        root.style.setProperty('--border-color', '#e0e0e0');
        root.style.setProperty('--input-bg', '#ffffff');
        root.style.setProperty('--primary-color', settings.accentColor || '#1976d2');
        root.style.setProperty('--secondary-bg', '#f9f9f9');
        root.style.setProperty('--hover-color', 'rgba(0, 0, 0, 0.04)');
      }
      
      // Apply animations settings
      if (settings.enableAnimations) {
        root.style.setProperty('--transition-speed', '0.3s');
      } else {
        root.style.setProperty('--transition-speed', '0s');
      }
      
      // Save to localStorage whenever settings change
      localStorage.setItem('cfd-app-settings', JSON.stringify(settings));
    } catch (error) {
      console.error('Failed to apply settings:', error);
    }
  }, [settings]);

  const saveSettings = (newSettings) => {
    try {
      const updatedSettings = { ...settings, ...newSettings };
      setSettings(updatedSettings);
      localStorage.setItem('cfd-app-settings', JSON.stringify(updatedSettings));
      return true;
    } catch (error) {
      console.error('Failed to save settings:', error);
      return false;
    }
  };

  const updateSetting = (key, value) => {
    try {
      const updatedSettings = { ...settings, [key]: value };
      setSettings(updatedSettings);
      localStorage.setItem('cfd-app-settings', JSON.stringify(updatedSettings));
      return true;
    } catch (error) {
      console.error(`Failed to update setting ${key}:`, error);
      return false;
    }
  };

  const resetSettings = () => {
    try {
      setSettings(DEFAULT_SETTINGS);
      localStorage.setItem('cfd-app-settings', JSON.stringify(DEFAULT_SETTINGS));
      return true;
    } catch (error) {
      console.error('Failed to reset settings:', error);
      return false;
    }
  };

  const exportSettings = () => {
    try {
      const dataStr = JSON.stringify(settings, null, 2);
      const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
      
      const exportFileDefaultName = 'cfd-app-settings.json';
      
      const linkElement = document.createElement('a');
      linkElement.setAttribute('href', dataUri);
      linkElement.setAttribute('download', exportFileDefaultName);
      linkElement.click();
      return true;
    } catch (error) {
      console.error('Failed to export settings:', error);
      alert('Failed to export settings. See console for details.');
      return false;
    }
  };

  const importSettings = (file, callback) => {
    try {
      const reader = new FileReader();
      reader.onload = (event) => {
        try {
          const importedSettings = JSON.parse(event.target.result);
          // Merge with default settings to ensure all required fields exist
          const mergedSettings = { ...DEFAULT_SETTINGS, ...importedSettings };
          setSettings(mergedSettings);
          localStorage.setItem('cfd-app-settings', JSON.stringify(mergedSettings));
          if (callback) callback(mergedSettings);
        } catch (e) {
          console.error("Failed to parse settings file:", e);
          alert("Invalid settings file format");
        }
      };
      reader.readAsText(file);
    } catch (error) {
      console.error('Failed to import settings:', error);
      alert('Failed to import settings. See console for details.');
      return false;
    }
  };

  const getSettings = () => settings;

  const value = {
    settings,
    saveSettings,
    updateSetting,
    resetSettings,
    exportSettings,
    importSettings,
    getSettings,
  };

  return <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>;
};

export const useSettingsService = () => {
  const context = useContext(SettingsContext);
  if (!context) {
    throw new Error('useSettingsService must be used within a SettingsProvider');
  }
  return context;
};
