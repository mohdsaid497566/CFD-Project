import React, { useState, useEffect } from 'react';
import { createTheme, ThemeProvider, CssBaseline } from '@mui/material';
import { Box, AppBar, Toolbar, Typography, Drawer, List, ListItem, ListItemIcon, ListItemText, IconButton, Divider } from '@mui/material';
import { Menu as MenuIcon, Dashboard, Settings, Build, Assessment, ViewInAr, Science, Speed, DarkMode, LightMode } from '@mui/icons-material';
import SettingsPage from './components/settings/SettingsPage';
import { SettingsProvider, useSettingsService } from './services/SettingsService';
import './styles/global.css'; // Import global CSS for theming

// App wrapper to access settings context
function AppContent() {
  const [open, setOpen] = useState(false);
  const [currentPage, setCurrentPage] = useState('dashboard');
  const { settings, updateSetting } = useSettingsService();
  
  // Create a theme based on current settings
  const theme = createTheme({
    palette: {
      mode: settings.theme === 'dark' ? 'dark' : 'light',
      primary: {
        main: settings.accentColor || '#1976d2',
      },
      secondary: {
        main: '#2ecc71',
      },
    },
    typography: {
      fontSize: settings.fontSize === 'small' ? 14 : 
               settings.fontSize === 'large' ? 18 : 
               settings.fontSize === 'x-large' ? 20 : 16,
    },
    components: {
      MuiCssBaseline: {
        styleOverrides: {
          body: {
            transition: settings.enableAnimations ? 'all 0.3s ease' : 'none',
          },
        },
      },
    },
  });
  
  const handleDrawerToggle = () => {
    setOpen(!open);
  };
  
  const handlePageChange = (page) => {
    setCurrentPage(page);
    setOpen(false);
  };

  // Apply settings to the app container
  useEffect(() => {
    // You can apply app-specific settings here that aren't handled globally
    // For example, set debug information visibility based on settings.debugMode
    if (settings.debugMode) {
      console.log('Debug mode is enabled');
      // Show debug elements if needed
    }
    
    // Set up auto-save timer based on settings.autoSaveInterval
    const autoSaveTimer = settings.autoSaveInterval > 0 ? 
      setInterval(() => {
        console.log('Auto-saving...');
        // Implement auto-save functionality here
      }, settings.autoSaveInterval * 60 * 1000) : null;
    
    return () => {
      if (autoSaveTimer) clearInterval(autoSaveTimer);
    };
  }, [settings]);

  // Toggle theme helper function
  const toggleTheme = () => {
    const newTheme = settings.theme === 'dark' ? 'light' : 'dark';
    updateSetting('theme', newTheme);
  };
  
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ display: 'flex' }}>
        {/* App Bar */}
        <AppBar position="fixed">
          <Toolbar>
            <IconButton
              color="inherit"
              aria-label="open drawer"
              edge="start"
              onClick={handleDrawerToggle}
              sx={{ mr: 2 }}
            >
              <MenuIcon />
            </IconButton>
            <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
              Intake CFD Optimization Suite
            </Typography>
            <IconButton 
              color="inherit" 
              onClick={toggleTheme}
              aria-label="toggle theme"
            >
              {settings.theme === 'dark' ? <LightMode /> : <DarkMode />}
            </IconButton>
          </Toolbar>
        </AppBar>
        
        {/* Navigation Drawer */}
        <Drawer
          variant="temporary"
          open={open}
          onClose={handleDrawerToggle}
          sx={{
            width: 240,
            flexShrink: 0,
            '& .MuiDrawer-paper': {
              width: 240,
              boxSizing: 'border-box',
            },
          }}
        >
          <Toolbar />
          <Divider />
          <List>
            <ListItem button onClick={() => handlePageChange('dashboard')} selected={currentPage === 'dashboard'}>
              <ListItemIcon><Dashboard /></ListItemIcon>
              <ListItemText primary="Dashboard" />
            </ListItem>
            <ListItem button onClick={() => handlePageChange('workflow')} selected={currentPage === 'workflow'}>
              <ListItemIcon><Speed /></ListItemIcon>
              <ListItemText primary="Workflow" />
            </ListItem>
            <ListItem button onClick={() => handlePageChange('optimization')} selected={currentPage === 'optimization'}>
              <ListItemIcon><Assessment /></ListItemIcon>
              <ListItemText primary="Optimization" />
            </ListItem>
            <ListItem button onClick={() => handlePageChange('visualization')} selected={currentPage === 'visualization'}>
              <ListItemIcon><ViewInAr /></ListItemIcon>
              <ListItemText primary="Visualization" />
            </ListItem>
            <ListItem button onClick={() => handlePageChange('hpc')} selected={currentPage === 'hpc'}>
              <ListItemIcon><Science /></ListItemIcon>
              <ListItemText primary="HPC" />
            </ListItem>
            <ListItem button onClick={() => handlePageChange('settings')} selected={currentPage === 'settings'}>
              <ListItemIcon><Settings /></ListItemIcon>
              <ListItemText primary="Settings" />
            </ListItem>
          </List>
        </Drawer>
        
        {/* Main Content */}
        <Box 
          component="main" 
          sx={{ 
            flexGrow: 1, 
            p: 3, 
            mt: 8,
            transition: settings.enableAnimations ? 'all 0.3s ease' : 'none',
          }}
        >
          {currentPage === 'settings' && <SettingsPage />}
          {currentPage === 'dashboard' && <div>Dashboard Page (Coming Soon)</div>}
          {currentPage === 'workflow' && <div>Workflow Page (Coming Soon)</div>}
          {currentPage === 'optimization' && <div>Optimization Page (Coming Soon)</div>}
          {currentPage === 'visualization' && <div>Visualization Page (Coming Soon)</div>}
          {currentPage === 'hpc' && <div>HPC Page (Coming Soon)</div>}
        </Box>
      </Box>
    </ThemeProvider>
  );
}

// Main App component that provides the SettingsProvider
function App() {
  return (
    <SettingsProvider>
      <AppContent />
    </SettingsProvider>
  );
}

export default App;
