import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  Card,
  CardContent,
  CardHeader,
  Switch,
  FormControlLabel,
  Tabs,
  Tab,
  Alert,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  Avatar,
  LinearProgress
} from '@mui/material';
import {
  Settings as SettingsIcon,
  Person,
  Security,
  Key,
  Notifications,
  Palette,
  Language,
  Storage,
  Api,
  TestTube,
  Edit,
  Delete,
  Add,
  Visibility,
  VisibilityOff,
  Save,
  Refresh,
  CloudDone,
  Error,
  Warning,
  CheckCircle
} from '@mui/icons-material';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:4700';

// API Key management component
const APIKeyManager = ({ apiKeys, onUpdate, onTest }) => {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingKey, setEditingKey] = useState(null);
  const [showKey, setShowKey] = useState({});
  const [keyForm, setKeyForm] = useState({
    service_name: '',
    key_name: '',
    api_key: ''
  });

  const serviceTypes = [
    { id: 'google_api_key', name: 'Google API Key', description: 'For Google Cloud services' },
    { id: 'gemini_api_key', name: 'Gemini API Key', description: 'For Gemini AI features' },
    { id: 'google_cloud_project', name: 'Google Cloud Project', description: 'Your project ID' },
    { id: 'openai_api_key', name: 'OpenAI API Key', description: 'For OpenAI services' }
  ];

  const handleSaveKey = async () => {
    try {
      if (editingKey) {
        // Update existing key
        await onUpdate(editingKey.id, keyForm);
      } else {
        // Create new key
        await onUpdate(null, keyForm);
      }
      
      setDialogOpen(false);
      setEditingKey(null);
      setKeyForm({ service_name: '', key_name: '', api_key: '' });
    } catch (error) {
      console.error('Failed to save API key:', error);
    }
  };

  const handleEdit = (key) => {
    setEditingKey(key);
    setKeyForm({
      service_name: key.service_name,
      key_name: key.key_name,
      api_key: '••••••••' // Don't show actual key
    });
    setDialogOpen(true);
  };

  const toggleShowKey = (keyId) => {
    setShowKey(prev => ({ ...prev, [keyId]: !prev[keyId] }));
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active': return <CheckCircle color="success" />;
      case 'error': return <Error color="error" />;
      case 'warning': return <Warning color="warning" />;
      default: return <Api color="disabled" />;
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">API Keys</Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => setDialogOpen(true)}
        >
          Add API Key
        </Button>
      </Box>

      <List>
        {apiKeys.map((key) => (
          <ListItem key={key.id}>
            <ListItemText
              primary={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  {getStatusIcon(key.status)}
                  <Typography variant="body1">{key.key_name}</Typography>
                  <Chip label={key.service_name} size="small" />
                </Box>
              }
              secondary={
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    {showKey[key.id] ? key.api_key : '••••••••••••••••••••••••••••'}
                  </Typography>
                  <Typography variant="caption">
                    Created: {new Date(key.created_at).toLocaleDateString()}
                    {key.last_used && ` • Last used: ${new Date(key.last_used).toLocaleDateString()}`}
                  </Typography>
                </Box>
              }
            />
            <ListItemSecondaryAction>
              <IconButton onClick={() => toggleShowKey(key.id)}>
                {showKey[key.id] ? <VisibilityOff /> : <Visibility />}
              </IconButton>
              <IconButton onClick={() => onTest(key)}>
                <TestTube />
              </IconButton>
              <IconButton onClick={() => handleEdit(key)}>
                <Edit />
              </IconButton>
            </ListItemSecondaryAction>
          </ListItem>
        ))}
      </List>

      {/* Add/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editingKey ? 'Edit API Key' : 'Add API Key'}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Service Type"
                select
                value={keyForm.service_name}
                onChange={(e) => setKeyForm(prev => ({ ...prev, service_name: e.target.value }))}
                SelectProps={{ native: true }}
              >
                <option value="">Select service</option>
                {serviceTypes.map((service) => (
                  <option key={service.id} value={service.id}>
                    {service.name}
                  </option>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Key Name"
                value={keyForm.key_name}
                onChange={(e) => setKeyForm(prev => ({ ...prev, key_name: e.target.value }))}
                placeholder="e.g., Production Google API Key"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="API Key"
                type="password"
                value={keyForm.api_key}
                onChange={(e) => setKeyForm(prev => ({ ...prev, api_key: e.target.value }))}
                placeholder="Enter your API key"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSaveKey} variant="contained">
            {editingKey ? 'Update' : 'Add'} Key
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

// Connection test component
const ConnectionTest = ({ onTest, testResults }) => {
  const [testing, setTesting] = useState(false);

  const handleTest = async () => {
    setTesting(true);
    try {
      await onTest();
    } catch (error) {
      console.error('Connection test failed:', error);
    } finally {
      setTesting(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'success': return 'success';
      case 'failed': return 'error';
      case 'warning': return 'warning';
      default: return 'default';
    }
  };

  return (
    <Card>
      <CardHeader
        title="Connection Test"
        subheader="Test your API connections to ensure everything is working"
        action={
          <Button
            variant="contained"
            startIcon={testing ? <Refresh /> : <TestTube />}
            onClick={handleTest}
            disabled={testing}
          >
            {testing ? 'Testing...' : 'Test Connection'}
          </Button>
        }
      />
      <CardContent>
        {testing && <LinearProgress sx={{ mb: 2 }} />}
        
        {testResults && (
          <Box>
            <Typography variant="h6" gutterBottom>
              Test Results
            </Typography>
            <Chip
              icon={testResults.overall_status === 'success' ? <CheckCircle /> : <Error />}
              label={testResults.message}
              color={getStatusColor(testResults.overall_status)}
              sx={{ mb: 2 }}
            />
            
            {testResults.details && (
              <List dense>
                {Object.entries(testResults.details).map(([service, details]) => (
                  <ListItem key={service}>
                    <ListItemText
                      primary={service.replace('_', ' ').toUpperCase()}
                      secondary={details.message}
                    />
                    <Chip
                      size="small"
                      label={details.status}
                      color={getStatusColor(details.status)}
                    />
                  </ListItem>
                ))}
              </List>
            )}
            
            {testResults.recommendations && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Recommendations:
                </Typography>
                <List dense>
                  {testResults.recommendations.map((rec, index) => (
                    <ListItem key={index}>
                      <ListItemText primary={rec} />
                    </ListItem>
                  ))}
                </List>
              </Box>
            )}
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

// Main Settings component
const Settings = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // User profile
  const [profile, setProfile] = useState({
    username: '',
    full_name: '',
    email: '',
    avatar_url: ''
  });

  // User preferences
  const [preferences, setPreferences] = useState({
    theme: 'light',
    language: 'en',
    notifications_enabled: true,
    auto_save: true,
    default_video_duration: 5,
    default_video_style: 'cinematic',
    quality_preference: 'high'
  });

  // API keys
  const [apiKeys, setApiKeys] = useState([]);
  const [testResults, setTestResults] = useState(null);

  const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return { Authorization: `Bearer ${token}` };
  };

  useEffect(() => {
    loadUserData();
  }, []);

  const loadUserData = async () => {
    try {
      setLoading(true);
      
      // Load profile
      const profileResponse = await axios.get(
        `${API_BASE_URL}/api/v1/auth/profile`,
        { headers: getAuthHeaders() }
      );
      setProfile(profileResponse.data);
      setPreferences(profileResponse.data.settings || {});

      // Load API keys
      const keysResponse = await axios.get(
        `${API_BASE_URL}/api/v1/auth/api-keys`,
        { headers: getAuthHeaders() }
      );
      setApiKeys(keysResponse.data);

    } catch (error) {
      console.error('Failed to load user data:', error);
      setError('Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  const updateProfile = async () => {
    try {
      setLoading(true);
      const response = await axios.put(
        `${API_BASE_URL}/api/v1/auth/profile`,
        {
          username: profile.username,
          full_name: profile.full_name,
          avatar_url: profile.avatar_url
        },
        { headers: getAuthHeaders() }
      );
      
      setProfile(response.data);
      setSuccess('Profile updated successfully!');
      
      // Update local storage
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      localStorage.setItem('user', JSON.stringify({ ...user, ...response.data }));
      
    } catch (error) {
      console.error('Failed to update profile:', error);
      setError('Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  const updatePreferences = async () => {
    try {
      setLoading(true);
      
      // Update each preference
      for (const [key, value] of Object.entries(preferences)) {
        await axios.put(
          `${API_BASE_URL}/api/v1/auth/settings`,
          {
            key,
            value,
            value_type: typeof value === 'boolean' ? 'boolean' : 
                       typeof value === 'number' ? 'number' : 'string'
          },
          { headers: getAuthHeaders() }
        );
      }
      
      setSuccess('Preferences updated successfully!');
      
    } catch (error) {
      console.error('Failed to update preferences:', error);
      setError('Failed to update preferences');
    } finally {
      setLoading(false);
    }
  };

  const handleAPIKeyUpdate = async (keyId, keyData) => {
    try {
      if (keyId) {
        // Update existing key
        await axios.put(
          `${API_BASE_URL}/api/v1/auth/api-keys/${keyId}`,
          keyData,
          { headers: getAuthHeaders() }
        );
      } else {
        // Create new key
        const response = await axios.post(
          `${API_BASE_URL}/api/v1/auth/api-keys`,
          keyData,
          { headers: getAuthHeaders() }
        );
        setApiKeys(prev => [...prev, response.data]);
      }
      
      // Reload API keys
      loadUserData();
      setSuccess('API key updated successfully!');
      
    } catch (error) {
      console.error('Failed to update API key:', error);
      setError('Failed to update API key');
    }
  };

  const testConnection = async () => {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/enhanced-auth/test-connection`,
        {},
        { headers: getAuthHeaders() }
      );
      
      setTestResults(response.data.test_results);
      
      if (response.data.test_results.overall_status === 'success') {
        setSuccess('All connections tested successfully!');
      } else {
        setError('Some connections failed. Check the results below.');
      }
      
    } catch (error) {
      console.error('Connection test failed:', error);
      setError('Connection test failed');
    }
  };

  const TabPanel = ({ children, value, index, ...other }) => (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        ⚙️ Settings
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" sx={{ mb: 3 }}>
        Manage your account, preferences, and API configurations.
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>{success}</Alert>}

      <Paper sx={{ width: '100%' }}>
        <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)}>
          <Tab label="Profile" icon={<Person />} />
          <Tab label="Preferences" icon={<Palette />} />
          <Tab label="API Keys" icon={<Key />} />
          <Tab label="Connection" icon={<Api />} />
        </Tabs>

        <TabPanel value={activeTab} index={0}>
          {/* Profile Settings */}
          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Avatar
                    src={profile.avatar_url}
                    sx={{ width: 120, height: 120, mx: 'auto', mb: 2 }}
                  >
                    {profile.full_name?.charAt(0) || profile.username?.charAt(0) || 'U'}
                  </Avatar>
                  <Typography variant="h6">{profile.full_name || profile.username}</Typography>
                  <Typography variant="body2" color="text.secondary">{profile.email}</Typography>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={8}>
              <Card>
                <CardHeader title="Profile Information" />
                <CardContent>
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                      <TextField
                        fullWidth
                        label="Username"
                        value={profile.username}
                        onChange={(e) => setProfile(prev => ({ ...prev, username: e.target.value }))}
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <TextField
                        fullWidth
                        label="Full Name"
                        value={profile.full_name}
                        onChange={(e) => setProfile(prev => ({ ...prev, full_name: e.target.value }))}
                      />
                    </Grid>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label="Email"
                        value={profile.email}
                        disabled
                        helperText="Email cannot be changed"
                      />
                    </Grid>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label="Avatar URL"
                        value={profile.avatar_url || ''}
                        onChange={(e) => setProfile(prev => ({ ...prev, avatar_url: e.target.value }))}
                        placeholder="https://example.com/avatar.jpg"
                      />
                    </Grid>
                    <Grid item xs={12}>
                      <Button
                        variant="contained"
                        onClick={updateProfile}
                        disabled={loading}
                        startIcon={<Save />}
                      >
                        Save Profile
                      </Button>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={activeTab} index={1}>
          {/* Preferences */}
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardHeader title="General Preferences" />
                <CardContent>
                  <List>
                    <ListItem>
                      <ListItemText primary="Theme" secondary="Choose your preferred theme" />
                      <ListItemSecondaryAction>
                        <FormControlLabel
                          control={
                            <Switch
                              checked={preferences.theme === 'dark'}
                              onChange={(e) => setPreferences(prev => ({
                                ...prev,
                                theme: e.target.checked ? 'dark' : 'light'
                              }))}
                            />
                          }
                          label={preferences.theme === 'dark' ? 'Dark' : 'Light'}
                        />
                      </ListItemSecondaryAction>
                    </ListItem>
                    
                    <ListItem>
                      <ListItemText primary="Notifications" secondary="Enable desktop notifications" />
                      <ListItemSecondaryAction>
                        <Switch
                          checked={preferences.notifications_enabled}
                          onChange={(e) => setPreferences(prev => ({
                            ...prev,
                            notifications_enabled: e.target.checked
                          }))}
                        />
                      </ListItemSecondaryAction>
                    </ListItem>
                    
                    <ListItem>
                      <ListItemText primary="Auto Save" secondary="Automatically save your work" />
                      <ListItemSecondaryAction>
                        <Switch
                          checked={preferences.auto_save}
                          onChange={(e) => setPreferences(prev => ({
                            ...prev,
                            auto_save: e.target.checked
                          }))}
                        />
                      </ListItemSecondaryAction>
                    </ListItem>
                  </List>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Card>
                <CardHeader title="Default Generation Settings" />
                <CardContent>
                  <Grid container spacing={2}>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        type="number"
                        label="Default Video Duration (seconds)"
                        value={preferences.default_video_duration}
                        onChange={(e) => setPreferences(prev => ({
                          ...prev,
                          default_video_duration: parseInt(e.target.value)
                        }))}
                        inputProps={{ min: 5, max: 60 }}
                      />
                    </Grid>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label="Default Video Style"
                        select
                        value={preferences.default_video_style}
                        onChange={(e) => setPreferences(prev => ({
                          ...prev,
                          default_video_style: e.target.value
                        }))}
                        SelectProps={{ native: true }}
                      >
                        <option value="cinematic">Cinematic</option>
                        <option value="anime">Anime</option>
                        <option value="realistic">Realistic</option>
                        <option value="artistic">Artistic</option>
                      </TextField>
                    </Grid>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label="Quality Preference"
                        select
                        value={preferences.quality_preference}
                        onChange={(e) => setPreferences(prev => ({
                          ...prev,
                          quality_preference: e.target.value
                        }))}
                        SelectProps={{ native: true }}
                      >
                        <option value="draft">Draft</option>
                        <option value="standard">Standard</option>
                        <option value="high">High</option>
                      </TextField>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12}>
              <Button
                variant="contained"
                onClick={updatePreferences}
                disabled={loading}
                startIcon={<Save />}
              >
                Save Preferences
              </Button>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={activeTab} index={2}>
          {/* API Keys */}
          <APIKeyManager
            apiKeys={apiKeys}
            onUpdate={handleAPIKeyUpdate}
            onTest={(key) => console.log('Test key:', key)}
          />
        </TabPanel>

        <TabPanel value={activeTab} index={3}>
          {/* Connection Test */}
          <ConnectionTest
            onTest={testConnection}
            testResults={testResults}
          />
        </TabPanel>
      </Paper>
    </Box>
  );
};

export default Settings;
