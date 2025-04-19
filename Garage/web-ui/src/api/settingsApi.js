import axios from 'axios';

// Base API URL - this would point to your Python backend
const API_BASE_URL = 'http://localhost:5000/api';

// Settings API methods
const settingsApi = {
  // Get all settings
  getSettings: async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/settings`);
      return response.data;
    } catch (error) {
      console.error('Error fetching settings:', error);
      throw error;
    }
  },
  
  // Save settings
  saveSettings: async (settings) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/settings`, settings);
      return response.data;
    } catch (error) {
      console.error('Error saving settings:', error);
      throw error;
    }
  },
  
  // Reset settings to defaults
  resetSettings: async () => {
    try {
      const response = await axios.post(`${API_BASE_URL}/settings/reset`);
      return response.data;
    } catch (error) {
      console.error('Error resetting settings:', error);
      throw error;
    }
  },
  
  // Get system information
  getSystemInfo: async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/system-info`);
      return response.data;
    } catch (error) {
      console.error('Error fetching system info:', error);
      throw error;
    }
  },
  
  // Check for updates
  checkForUpdates: async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/check-updates`);
      return response.data;
    } catch (error) {
      console.error('Error checking for updates:', error);
      throw error;
    }
  },
  
  // Run diagnostics
  runDiagnostics: async () => {
    try {
      const response = await axios.post(`${API_BASE_URL}/run-diagnostics`);
      return response.data;
    } catch (error) {
      console.error('Error running diagnostics:', error);
      throw error;
    }
  }
};

export default settingsApi;
