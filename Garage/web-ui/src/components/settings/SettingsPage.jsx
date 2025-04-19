import React, { useState, useEffect } from 'react';
import { 
  Container, Grid, Paper, Typography, TextField, Button, 
  Select, MenuItem, FormControl, InputLabel, Switch, 
  FormControlLabel, Slider, Divider, Box, Card, CardContent,
  Snackbar, Alert, IconButton, Tooltip
} from '@mui/material';
import { styled } from '@mui/material/styles';
import { useSettingsService } from '../../services/SettingsService';
import ColorLensIcon from '@mui/icons-material/ColorLens';

// Styled components for better appearance
const SettingsSection = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(3),
  marginBottom: theme.spacing(3),
  borderRadius: theme.shape.borderRadius,
  boxShadow: theme.shadows[2]
}));

const ColorPickerContainer = styled('div')(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  marginTop: theme.spacing(2),
}));

const ColorPreview = styled('div')(({ color }) => ({
  width: 36,
  height: 36,
  borderRadius: '50%',
  backgroundColor: color,
  marginRight: 16,
  border: '2px solid #ccc',
  boxShadow: '0 0 5px rgba(0,0,0,0.2)',
}));

const SettingsPage = () => {
  const { settings, saveSettings, resetSettings } = useSettingsService();
  
  // Notification state
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'success' });
  
  // General settings state
  const [nxPath, setNxPath] = useState(settings.nxPath || '');
  const [projectDir, setProjectDir] = useState(settings.projectDir || '');
  
  // Appearance settings state
  const [theme, setTheme] = useState(settings.theme || 'light');
  const [fontSize, setFontSize] = useState(settings.fontSize || 'medium');
  const [accentColor, setAccentColor] = useState(settings.accentColor || '#1976d2');
  const [enableAnimations, setEnableAnimations] = useState(
    settings.enableAnimations !== undefined ? settings.enableAnimations : true
  );
  
  // Simulation settings state
  const [cfdSolver, setCfdSolver] = useState(settings.cfdSolver || 'OpenFOAM');
  const [mesher, setMesher] = useState(settings.mesher || 'GMSH');
  const [meshSize, setMeshSize] = useState(settings.defaultMeshSize || 0.1);
  const [viscosity, setViscosity] = useState(settings.viscosity || 1.8e-5);
  const [density, setDensity] = useState(settings.density || 1.225);
  
  // Advanced settings state
  const [threads, setThreads] = useState(settings.threads || 4);
  const [debugMode, setDebugMode] = useState(settings.debugMode || false);
  const [autoSaveInterval, setAutoSaveInterval] = useState(settings.autoSaveInterval || 10);
  const [memoryLimit, setMemoryLimit] = useState(settings.memoryLimit || 70);
  
  // System information state
  const [systemInfo, setSystemInfo] = useState({
    cpu: 'Loading...',
    memory: 'Loading...',
    os: 'Loading...',
    pythonVersion: 'Loading...'
  });
  
  // Load settings from backend
  useEffect(() => {
    // Update local state when settings change
    setNxPath(settings.nxPath || '');
    setProjectDir(settings.projectDir || '');
    setTheme(settings.theme || 'light');
    setFontSize(settings.fontSize || 'medium');
    setAccentColor(settings.accentColor || '#1976d2');
    setEnableAnimations(settings.enableAnimations !== undefined ? settings.enableAnimations : true);
    setCfdSolver(settings.cfdSolver || 'OpenFOAM');
    setMesher(settings.mesher || 'GMSH');
    setMeshSize(settings.defaultMeshSize || 0.1);
    setViscosity(settings.viscosity || 1.8e-5);
    setDensity(settings.density || 1.225);
    setThreads(settings.threads || 4);
    setDebugMode(settings.debugMode || false);
    setAutoSaveInterval(settings.autoSaveInterval || 10);
    setMemoryLimit(settings.memoryLimit || 70);
    
    // Fetch system information
    const fetchSystemInfo = async () => {
      try {
        // This would be an actual API call in production
        // For now, use mock data
        setSystemInfo({
          cpu: 'Intel(R) Core(TM) i7-10700K CPU @ 3.80GHz',
          memory: '32.0 GB',
          os: 'Linux 5.15.0-56-generic',
          pythonVersion: '3.10.6',
        });
      } catch (error) {
        console.error('Failed to fetch system info:', error);
      }
    };
    
    fetchSystemInfo();
  }, [settings]);
  
  // Save all settings
  const handleSaveSettings = async () => {
    try {
      // Validate settings before saving
      if (autoSaveInterval < 1) {
        setNotification({
          open: true,
          message: 'Auto-save interval must be at least 1 minute',
          severity: 'error'
        });
        return;
      }
      
      if (meshSize <= 0) {
        setNotification({
          open: true,
          message: 'Mesh size must be greater than 0',
          severity: 'error'
        });
        return;
      }
      
      // Prepare settings object
      const updatedSettings = {
        ...settings,
        nxPath,
        projectDir,
        theme,
        fontSize,
        accentColor,
        enableAnimations,
        cfdSolver,
        mesher,
        defaultMeshSize: meshSize,
        viscosity,
        density,
        threads,
        debugMode,
        autoSaveInterval,
        memoryLimit
      };
      
      // Save settings
      const success = saveSettings(updatedSettings);
      
      if (success) {
        setNotification({
          open: true,
          message: 'Settings saved successfully!',
          severity: 'success'
        });
      } else {
        setNotification({
          open: true,
          message: 'Failed to save settings',
          severity: 'error'
        });
      }
    } catch (error) {
      console.error('Failed to save settings:', error);
      setNotification({
        open: true,
        message: 'An error occurred while saving settings',
        severity: 'error'
      });
    }
  };
  
  // Apply theme changes immediately
  const handleThemeChange = (e) => {
    const newTheme = e.target.value;
    setTheme(newTheme);
    saveSettings({
      ...settings,
      theme: newTheme
    });
  };
  
  // Apply font size changes immediately
  const handleFontSizeChange = (e) => {
    const newFontSize = e.target.value;
    setFontSize(newFontSize);
    saveSettings({
      ...settings,
      fontSize: newFontSize
    });
  };
  
  // Apply accent color changes immediately
  const handleAccentColorChange = (e) => {
    const newColor = e.target.value;
    setAccentColor(newColor);
    saveSettings({
      ...settings,
      accentColor: newColor
    });
  };
  
  // Apply animations settings immediately
  const handleAnimationsChange = (e) => {
    const newValue = e.target.checked;
    setEnableAnimations(newValue);
    saveSettings({
      ...settings,
      enableAnimations: newValue
    });
  };
  
  // Handle reset to defaults
  const handleResetSettings = () => {
    // Confirm with user
    if (window.confirm('Are you sure you want to reset all settings to defaults?')) {
      resetSettings();
      setNotification({
        open: true,
        message: 'Settings reset to defaults',
        severity: 'info'
      });
    }
  };
  
  // Handle check for updates
  const handleCheckUpdates = () => {
    // This would be an actual API call to check for updates
    setNotification({
      open: true,
      message: 'Checking for updates...',
      severity: 'info'
    });
    
    // Simulate check
    setTimeout(() => {
      setNotification({
        open: true,
        message: 'Application is up to date!',
        severity: 'success'
      });
    }, 2000);
  };
  
  // Handle run diagnostics
  const handleRunDiagnostics = () => {
    // This would be an actual API call to run diagnostics
    setNotification({
      open: true,
      message: 'Running diagnostics...',
      severity: 'info'
    });
    
    // Simulate diagnostic run
    setTimeout(() => {
      setNotification({
        open: true,
        message: 'Diagnostics completed. All systems operational.',
        severity: 'success'
      });
    }, 3000);
  };
  
  // Close notification
  const handleCloseNotification = (event, reason) => {
    if (reason === 'clickaway') {
      return;
    }
    setNotification({ ...notification, open: false });
  };
  
  // Format memory usage display
  const formatMemoryUsage = (value) => {
    return `${value}%`;
  };
  
  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Settings
      </Typography>
      
      {/* General Settings */}
      <SettingsSection>
        <Typography variant="h6" gutterBottom>
          General Settings
        </Typography>
        <Grid container spacing={3}>
          <Grid item xs={12} sm={9}>
            <TextField
              fullWidth
              label="NX Path"
              value={nxPath}
              onChange={(e) => setNxPath(e.target.value)}
              margin="normal"
              variant="outlined"
            />
          </Grid>
          <Grid item xs={12} sm={3}>
            <Button 
              variant="contained" 
              color="primary"
              sx={{ mt: 3 }}
            >
              Browse
            </Button>
          </Grid>
          
          <Grid item xs={12} sm={9}>
            <TextField
              fullWidth
              label="Project Directory"
              value={projectDir}
              onChange={(e) => setProjectDir(e.target.value)}
              margin="normal"
              variant="outlined"
            />
          </Grid>
          <Grid item xs={12} sm={3}>
            <Button 
              variant="contained" 
              color="primary"
              sx={{ mt: 3 }}
            >
              Browse
            </Button>
          </Grid>
        </Grid>
      </SettingsSection>
      
      {/* Appearance Settings */}
      <SettingsSection>
        <Typography variant="h6" gutterBottom>
          Appearance
        </Typography>
        <Grid container spacing={3}>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth margin="normal">
              <InputLabel>Theme</InputLabel>
              <Select
                value={theme}
                onChange={handleThemeChange}
                label="Theme"
              >
                <MenuItem value="light">Light</MenuItem>
                <MenuItem value="dark">Dark</MenuItem>
                <MenuItem value="system">System</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth margin="normal">
              <InputLabel>Font Size</InputLabel>
              <Select
                value={fontSize}
                onChange={handleFontSizeChange}
                label="Font Size"
              >
                <MenuItem value="small">Small</MenuItem>
                <MenuItem value="medium">Medium</MenuItem>
                <MenuItem value="large">Large</MenuItem>
                <MenuItem value="x-large">X-Large</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12}>
            <ColorPickerContainer>
              <ColorPreview color={accentColor} />
              <TextField
                label="Accent Color"
                value={accentColor}
                onChange={(e) => setAccentColor(e.target.value)}
                sx={{ width: '160px', mr: 2 }}
              />
              <input
                type="color"
                value={accentColor}
                onChange={handleAccentColorChange}
                style={{ width: '40px', height: '40px' }}
              />
            </ColorPickerContainer>
            <FormControlLabel
              control={
                <Switch
                  checked={enableAnimations}
                  onChange={handleAnimationsChange}
                  color="primary"
                />
              }
              label="Enable UI animations"
              sx={{ mt: 2 }}
            />
          </Grid>
        </Grid>
      </SettingsSection>
      
      {/* Simulation Settings */}
      <SettingsSection>
        <Typography variant="h6" gutterBottom>
          Simulation Settings
        </Typography>
        <Grid container spacing={3}>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth margin="normal">
              <InputLabel>CFD Solver</InputLabel>
              <Select
                value={cfdSolver}
                onChange={(e) => setCfdSolver(e.target.value)}
                label="CFD Solver"
              >
                <MenuItem value="OpenFOAM">OpenFOAM</MenuItem>
                <MenuItem value="Fluent">Fluent</MenuItem>
                <MenuItem value="Star-CCM+">Star-CCM+</MenuItem>
                <MenuItem value="Custom">Custom</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth margin="normal">
              <InputLabel>Mesher</InputLabel>
              <Select
                value={mesher}
                onChange={(e) => setMesher(e.target.value)}
                label="Mesher"
              >
                <MenuItem value="GMSH">GMSH</MenuItem>
                <MenuItem value="Fluent Meshing">Fluent Meshing</MenuItem>
                <MenuItem value="Star-CCM+ Meshing">Star-CCM+ Meshing</MenuItem>
                <MenuItem value="Custom">Custom</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} sm={4}>
            <TextField
              fullWidth
              label="Default Mesh Size (m)"
              type="number"
              value={meshSize}
              onChange={(e) => setMeshSize(parseFloat(e.target.value))}
              inputProps={{ step: 0.01, min: 0.001 }}
              margin="normal"
              variant="outlined"
              error={meshSize <= 0}
              helperText={meshSize <= 0 ? "Mesh size must be greater than 0" : ""}
            />
          </Grid>
          <Grid item xs={12} sm={4}>
            <TextField
              fullWidth
              label="Default Viscosity (kg/m·s)"
              type="number"
              value={viscosity}
              onChange={(e) => setViscosity(parseFloat(e.target.value))}
              inputProps={{ step: 0.000001, min: 0 }}
              margin="normal"
              variant="outlined"
            />
          </Grid>
          <Grid item xs={12} sm={4}>
            <TextField
              fullWidth
              label="Default Density (kg/m³)"
              type="number"
              value={density}
              onChange={(e) => setDensity(parseFloat(e.target.value))}
              inputProps={{ step: 0.001, min: 0 }}
              margin="normal"
              variant="outlined"
            />
          </Grid>
        </Grid>
      </SettingsSection>
      
      {/* Advanced Settings */}
      <SettingsSection>
        <Typography variant="h6" gutterBottom>
          Advanced Settings
        </Typography>
        <Grid container spacing={3}>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Number of Threads"
              type="number"
              value={threads}
              onChange={(e) => setThreads(parseInt(e.target.value))}
              inputProps={{ min: 1 }}
              margin="normal"
              variant="outlined"
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Auto-save Interval (min)"
              type="number"
              value={autoSaveInterval}
              onChange={(e) => setAutoSaveInterval(parseInt(e.target.value))}
              inputProps={{ min: 1 }}
              margin="normal"
              variant="outlined"
              error={autoSaveInterval < 1}
              helperText={autoSaveInterval < 1 ? "Minimum value is 1 minute" : ""}
            />
          </Grid>
          
          <Grid item xs={12}>
            <FormControlLabel
              control={
                <Switch
                  checked={debugMode}
                  onChange={(e) => setDebugMode(e.target.checked)}
                  color="primary"
                />
              }
              label="Enable Debug Mode"
            />
          </Grid>
          
          <Grid item xs={12}>
            <Typography gutterBottom>Memory Limit: {formatMemoryUsage(memoryLimit)}</Typography>
            <Slider
              value={memoryLimit}
              onChange={(e, newValue) => setMemoryLimit(newValue)}
              aria-labelledby="memory-limit-slider"
              valueLabelDisplay="auto"
              valueLabelFormat={formatMemoryUsage}
              step={5}
              marks
              min={10}
              max={90}
            />
          </Grid>
          
          <Grid item xs={12}>
            <Typography variant="body2" color="textSecondary">
              Current Memory Usage: 45%
            </Typography>
          </Grid>
        </Grid>
      </SettingsSection>
      
      {/* System Information */}
      <SettingsSection>
        <Typography variant="h6" gutterBottom>
          System Information
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={3}>
            <Typography variant="subtitle2">CPU:</Typography>
          </Grid>
          <Grid item xs={12} sm={9}>
            <Typography variant="body2">{systemInfo.cpu}</Typography>
          </Grid>
          
          <Grid item xs={12} sm={3}>
            <Typography variant="subtitle2">Memory:</Typography>
          </Grid>
          <Grid item xs={12} sm={9}>
            <Typography variant="body2">{systemInfo.memory}</Typography>
          </Grid>
          
          <Grid item xs={12} sm={3}>
            <Typography variant="subtitle2">OS:</Typography>
          </Grid>
          <Grid item xs={12} sm={9}>
            <Typography variant="body2">{systemInfo.os}</Typography>
          </Grid>
          
          <Grid item xs={12} sm={3}>
            <Typography variant="subtitle2">Python:</Typography>
          </Grid>
          <Grid item xs={12} sm={9}>
            <Typography variant="body2">{systemInfo.pythonVersion}</Typography>
          </Grid>
        </Grid>
      </SettingsSection>
      
      {/* Action Buttons */}
      <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between' }}>
        <Box>
          <Button 
            variant="contained" 
            color="primary"
            onClick={handleSaveSettings}
            sx={{ mr: 2 }}
          >
            Save Settings
          </Button>
          <Button 
            variant="outlined" 
            color="primary"
            onClick={() => {
              // Trigger file input for importing settings
              const fileInput = document.createElement('input');
              fileInput.type = 'file';
              fileInput.accept = '.json';
              fileInput.onchange = (e) => {
                const file = e.target.files[0];
                if (file) {
                  // Import settings using SettingsService
                  const { importSettings } = useSettingsService();
                  importSettings(file);
                }
              };
              fileInput.click();
            }}
            sx={{ mr: 2 }}
          >
            Import Settings
          </Button>
          <Button 
            variant="outlined" 
            color="primary"
            onClick={() => {
              const { exportSettings } = useSettingsService();
              exportSettings();
            }}
            sx={{ mr: 2 }}
          >
            Export Settings
          </Button>
          <Button 
            variant="outlined" 
            color="warning"
            onClick={handleResetSettings}
          >
            Reset to Defaults
          </Button>
        </Box>
        <Box>
          <Button 
            variant="outlined" 
            color="info"
            onClick={handleRunDiagnostics}
            sx={{ mr: 2 }}
          >
            Run Diagnostics
          </Button>
          <Button 
            variant="outlined" 
            color="info"
            onClick={handleCheckUpdates}
          >
            Check for Updates
          </Button>
        </Box>
      </Box>
      
      {/* Notifications */}
      <Snackbar 
        open={notification.open} 
        autoHideDuration={6000} 
        onClose={handleCloseNotification}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert 
          onClose={handleCloseNotification} 
          severity={notification.severity} 
          sx={{ width: '100%' }}
        >
          {notification.message}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default SettingsPage;
