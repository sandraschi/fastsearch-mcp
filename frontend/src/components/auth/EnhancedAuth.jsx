import React, { useState, useEffect } from 'react';
import { 
  Container, 
  Typography, 
  TextField, 
  Button, 
  Box, 
  Alert, 
  Stepper, 
  Step, 
  StepLabel,
  StepContent,
  Paper,
  Card,
  CardContent,
  LinearProgress,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  InputAdornment,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
  CheckCircle,
  Error,
  Warning,
  Email,
  Key,
  Person,
  Settings,
  CloudDone
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:4700';

// Password strength indicator
const PasswordStrengthIndicator = ({ password }) => {
  const [strength, setStrength] = useState(0);
  const [feedback, setFeedback] = useState([]);

  useEffect(() => {
    const checks = [
      { test: password.length >= 8, message: "At least 8 characters" },
      { test: /[A-Z]/.test(password), message: "Uppercase letter" },
      { test: /[a-z]/.test(password), message: "Lowercase letter" },
      { test: /[0-9]/.test(password), message: "Number" },
      { test: /[!@#$%^&*(),.?":{}|<>]/.test(password), message: "Special character" }
    ];

    const passed = checks.filter(check => check.test).length;
    setStrength(passed);
    setFeedback(checks);
  }, [password]);

  const getStrengthColor = () => {
    if (strength < 2) return 'error';
    if (strength < 4) return 'warning';
    return 'success';
  };

  const getStrengthText = () => {
    if (strength < 2) return 'Weak';
    if (strength < 4) return 'Fair';
    if (strength < 5) return 'Good';
    return 'Strong';
  };

  return (
    <Box sx={{ mt: 1 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Typography variant="caption">Password strength:</Typography>
        <Typography variant="caption" color={getStrengthColor()}>
          {getStrengthText()}
        </Typography>
      </Box>
      <LinearProgress 
        variant="determinate" 
        value={(strength / 5) * 100} 
        color={getStrengthColor()}
        sx={{ height: 4, borderRadius: 2, mt: 0.5 }}
      />
      <List dense sx={{ mt: 1 }}>
        {feedback.map((item, index) => (
          <ListItem key={index} sx={{ py: 0, px: 0 }}>
            <ListItemIcon sx={{ minWidth: 24 }}>
              {item.test ? 
                <CheckCircle color="success" sx={{ fontSize: 16 }} /> : 
                <Error color="error" sx={{ fontSize: 16 }} />
              }
            </ListItemIcon>
            <ListItemText 
              primary={item.message} 
              primaryTypographyProps={{ variant: 'caption' }}
            />
          </ListItem>
        ))}
      </List>
    </Box>
  );
};

// Connection test component
const ConnectionTestDialog = ({ open, onClose, onComplete }) => {
  const [testing, setTesting] = useState(false);
  const [testResults, setTestResults] = useState(null);
  const [apiKeys, setApiKeys] = useState({
    google_api_key: '',
    gemini_api_key: '',
    google_cloud_project: ''
  });

  const runConnectionTest = async () => {
    setTesting(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/enhanced-auth/test-connection`,
        apiKeys,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setTestResults(response.data);
    } catch (error) {
      console.error('Connection test failed:', error);
      setTestResults({
        test_results: { overall_status: 'error', message: 'Test failed' },
        recommendations: ['Check your API keys and try again']
      });
    } finally {
      setTesting(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'success': return <CheckCircle color="success" />;
      case 'failed': return <Error color="error" />;
      case 'warning': return <Warning color="warning" />;
      default: return <Error color="error" />;
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
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Test API Connections</DialogTitle>
      <DialogContent>
        <Box sx={{ mb: 3 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Test your API connections to ensure VeoGen can access Google's AI services.
          </Typography>
          
          <TextField
            fullWidth
            label="Google API Key"
            value={apiKeys.google_api_key}
            onChange={(e) => setApiKeys(prev => ({ ...prev, google_api_key: e.target.value }))}
            margin="normal"
            type="password"
            helperText="Your Google Cloud API key"
          />
          
          <TextField
            fullWidth
            label="Gemini API Key"
            value={apiKeys.gemini_api_key}
            onChange={(e) => setApiKeys(prev => ({ ...prev, gemini_api_key: e.target.value }))}
            margin="normal"
            type="password"
            helperText="Your Gemini API key"
          />
          
          <TextField
            fullWidth
            label="Google Cloud Project ID"
            value={apiKeys.google_cloud_project}
            onChange={(e) => setApiKeys(prev => ({ ...prev, google_cloud_project: e.target.value }))}
            margin="normal"
            helperText="Your Google Cloud project ID"
          />
        </Box>

        {testResults && (
          <Card sx={{ mt: 2 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                {getStatusIcon(testResults.test_results.overall_status)}
                <Typography variant="h6">
                  Test Results: {testResults.test_results.overall_status}
                </Typography>
              </Box>
              
              <Typography variant="body2" sx={{ mb: 2 }}>
                {testResults.test_results.message}
              </Typography>

              {testResults.test_results.details && (
                <Box sx={{ mb: 2 }}>
                  {Object.entries(testResults.test_results.details).map(([service, details]) => (
                    <Box key={service} sx={{ mb: 1 }}>
                      <Chip
                        icon={getStatusIcon(details.status)}
                        label={`${service}: ${details.status}`}
                        color={getStatusColor(details.status)}
                        variant="outlined"
                        size="small"
                      />
                      <Typography variant="caption" sx={{ ml: 1, color: 'text.secondary' }}>
                        {details.message}
                      </Typography>
                    </Box>
                  ))}
                </Box>
              )}

              {testResults.recommendations && (
                <Box>
                  <Typography variant="subtitle2" sx={{ mb: 1 }}>Recommendations:</Typography>
                  <List dense>
                    {testResults.recommendations.map((rec, index) => (
                      <ListItem key={index} sx={{ py: 0 }}>
                        <ListItemText primary={rec} primaryTypographyProps={{ variant: 'body2' }} />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}
            </CardContent>
          </Card>
        )}
      </DialogContent>
      
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button 
          onClick={runConnectionTest}
          disabled={testing || !apiKeys.gemini_api_key}
          startIcon={testing ? <LinearProgress size={20} /> : <Settings />}
        >
          {testing ? 'Testing...' : 'Test Connection'}
        </Button>
        {testResults?.can_save_keys && (
          <Button 
            onClick={() => onComplete(apiKeys)}
            variant="contained"
            startIcon={<CloudDone />}
          >
            Save & Continue
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

// Main Enhanced Auth Component
const EnhancedAuth = () => {
  const navigate = useNavigate();
  const { login: authLogin, register: authRegister } = useAuth();
  const [mode, setMode] = useState('login'); // 'login', 'register', 'forgot'
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [testDialogOpen, setTestDialogOpen] = useState(false);

  // Form data
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    username: '',
    full_name: '',
    remember_me: false
  });

  // Registration form validation
  const [validationErrors, setValidationErrors] = useState({});

  const validateField = (name, value) => {
    const errors = { ...validationErrors };
    
    switch (name) {
      case 'email':
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
          errors.email = 'Please enter a valid email address';
        } else {
          delete errors.email;
        }
        break;
      
      case 'username':
        if (value && value.length < 3) {
          errors.username = 'Username must be at least 3 characters';
        } else if (value && !/^[a-zA-Z0-9_-]+$/.test(value)) {
          errors.username = 'Username can only contain letters, numbers, hyphens, and underscores';
        } else {
          delete errors.username;
        }
        break;
        
      default:
        break;
    }
    
    setValidationErrors(errors);
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    const newValue = type === 'checkbox' ? checked : value;
    
    setFormData(prev => ({
      ...prev,
      [name]: newValue
    }));

    // Validate field on change
    if (mode === 'register') {
      validateField(name, newValue);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const result = await authLogin(formData.email, formData.password);
      
      if (result.success) {
        setSuccess('Login successful!');
        
        // Check if onboarding is needed
        if (!result.user.onboarding_complete) {
          setActiveStep(1); // Move to onboarding
          setMode('onboarding');
        } else {
          // Navigate to main app
          navigate('/');
        }
      } else {
        setError(result.error || 'Login failed. Please try again.');
      }

    } catch (error) {
      console.error('Login error:', error);
      setError('Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    
    // Check for validation errors
    if (Object.keys(validationErrors).length > 0) {
      setError('Please fix the validation errors before continuing.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const result = await authRegister({
        email: formData.email,
        password: formData.password,
        username: formData.username || null,
        full_name: formData.full_name || null
      });

      if (result.success) {
        setSuccess('Registration successful! Welcome to VeoGen!');
        
        // Move to onboarding
        setActiveStep(1);
        setMode('onboarding');
      } else {
        setError(result.error || 'Registration failed. Please try again.');
      }

    } catch (error) {
      console.error('Registration error:', error);
      setError('Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleCompleteOnboarding = async (apiKeys = {}) => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API_BASE_URL}/api/v1/enhanced-auth/complete-onboarding`,
        {
          api_keys: apiKeys,
          preferences: {
            theme: 'dark',
            notifications: true
          },
          skip_tutorial: false
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      setSuccess('Onboarding completed! Welcome to VeoGen!');
      
      // Navigate to main app immediately using React Router
      navigate('/');

    } catch (error) {
      console.error('Onboarding error:', error);
      setError('Failed to complete onboarding. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleForgotPassword = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await axios.post(`${API_BASE_URL}/api/v1/enhanced-auth/request-password-reset`, {
        email: formData.email
      });

      setSuccess('Password reset email sent! Please check your inbox.');
      setMode('login');

    } catch (error) {
      console.error('Password reset error:', error);
      setError('Failed to send password reset email. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const renderLoginForm = () => (
    <Paper elevation={3} sx={{ p: 4, maxWidth: 400, mx: 'auto' }}>
      <Box sx={{ textAlign: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          VeoGen
        </Typography>
        <Typography variant="h6" color="text.secondary">
          Sign in to your account
        </Typography>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

      <form onSubmit={handleLogin}>
        <TextField
          fullWidth
          label="Email"
          name="email"
          type="email"
          value={formData.email}
          onChange={handleInputChange}
          margin="normal"
          required
          autoComplete="email"
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <Email />
              </InputAdornment>
            ),
          }}
        />

        <TextField
          fullWidth
          label="Password"
          name="password"
          type={showPassword ? 'text' : 'password'}
          value={formData.password}
          onChange={handleInputChange}
          margin="normal"
          required
          autoComplete="current-password"
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <Key />
              </InputAdornment>
            ),
            endAdornment: (
              <InputAdornment position="end">
                <IconButton
                  onClick={() => setShowPassword(!showPassword)}
                  edge="end"
                >
                  {showPassword ? <VisibilityOff /> : <Visibility />}
                </IconButton>
              </InputAdornment>
            ),
          }}
        />

        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 2 }}>
          <Button
            variant="text"
            onClick={() => setMode('forgot')}
            size="small"
          >
            Forgot password?
          </Button>
        </Box>

        <Button
          type="submit"
          fullWidth
          variant="contained"
          disabled={loading}
          sx={{ mt: 3, mb: 2 }}
        >
          {loading ? 'Signing in...' : 'Sign In'}
        </Button>

        <Box sx={{ textAlign: 'center' }}>
          <Button
            variant="text"
            onClick={() => setMode('register')}
          >
            Don't have an account? Sign up
          </Button>
        </Box>
      </form>
    </Paper>
  );

  const renderRegisterForm = () => (
    <Paper elevation={3} sx={{ p: 4, maxWidth: 500, mx: 'auto' }}>
      <Box sx={{ textAlign: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Join VeoGen
        </Typography>
        <Typography variant="h6" color="text.secondary">
          Create your account to start generating amazing content
        </Typography>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

      <form onSubmit={handleRegister}>
        <TextField
          fullWidth
          label="Email Address"
          name="email"
          type="email"
          value={formData.email}
          onChange={handleInputChange}
          margin="normal"
          required
          error={!!validationErrors.email}
          helperText={validationErrors.email}
          autoComplete="email"
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <Email />
              </InputAdornment>
            ),
          }}
        />

        <TextField
          fullWidth
          label="Username (optional)"
          name="username"
          value={formData.username}
          onChange={handleInputChange}
          margin="normal"
          error={!!validationErrors.username}
          helperText={validationErrors.username || "Choose a unique username"}
          autoComplete="username"
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <Person />
              </InputAdornment>
            ),
          }}
        />

        <TextField
          fullWidth
          label="Full Name (optional)"
          name="full_name"
          value={formData.full_name}
          onChange={handleInputChange}
          margin="normal"
          autoComplete="name"
        />

        <TextField
          fullWidth
          label="Password"
          name="password"
          type={showPassword ? 'text' : 'password'}
          value={formData.password}
          onChange={handleInputChange}
          margin="normal"
          required
          autoComplete="new-password"
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <Key />
              </InputAdornment>
            ),
            endAdornment: (
              <InputAdornment position="end">
                <IconButton
                  onClick={() => setShowPassword(!showPassword)}
                  edge="end"
                >
                  {showPassword ? <VisibilityOff /> : <Visibility />}
                </IconButton>
              </InputAdornment>
            ),
          }}
        />

        {formData.password && <PasswordStrengthIndicator password={formData.password} />}

        <Button
          type="submit"
          fullWidth
          variant="contained"
          disabled={loading || Object.keys(validationErrors).length > 0}
          sx={{ mt: 3, mb: 2 }}
        >
          {loading ? 'Creating account...' : 'Create Account'}
        </Button>

        <Box sx={{ textAlign: 'center' }}>
          <Button
            variant="text"
            onClick={() => setMode('login')}
          >
            Already have an account? Sign in
          </Button>
        </Box>
      </form>
    </Paper>
  );

  const renderOnboardingFlow = () => (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom align="center">
        Welcome to VeoGen!
      </Typography>
      <Typography variant="h6" color="text.secondary" align="center" sx={{ mb: 4 }}>
        Let's set up your account to start creating amazing AI content
      </Typography>

      <Stepper activeStep={activeStep} orientation="vertical">
        <Step>
          <StepLabel>Account Created</StepLabel>
          <StepContent>
            <Alert severity="success" sx={{ mb: 2 }}>
              <Typography>
                Your VeoGen account has been created successfully! 
                Now let's configure your AI connections.
              </Typography>
            </Alert>
          </StepContent>
        </Step>

        <Step>
          <StepLabel>Set Up API Connections</StepLabel>
          <StepContent>
            <Typography sx={{ mb: 2 }}>
              To use VeoGen's AI features, you'll need to configure your API keys.
              Don't worry - we'll test them to make sure everything works!
            </Typography>
            
            <Box sx={{ mb: 2 }}>
              <Button
                variant="contained"
                onClick={() => setTestDialogOpen(true)}
                startIcon={<Settings />}
                sx={{ mr: 2 }}
              >
                Configure API Keys
              </Button>
              
              <Button
                variant="outlined"
                onClick={() => handleCompleteOnboarding()}
              >
                Skip for Now
              </Button>
            </Box>

            <Alert severity="info">
              <Typography variant="body2">
                You can always configure your API keys later in the settings.
                However, you won't be able to generate content without them.
              </Typography>
            </Alert>
          </StepContent>
        </Step>
      </Stepper>

      <ConnectionTestDialog
        open={testDialogOpen}
        onClose={() => setTestDialogOpen(false)}
        onComplete={handleCompleteOnboarding}
      />
    </Container>
  );

  const renderForgotPasswordForm = () => (
    <Paper elevation={3} sx={{ p: 4, maxWidth: 400, mx: 'auto' }}>
      <Box sx={{ textAlign: 'center', mb: 3 }}>
        <Typography variant="h5" component="h1" gutterBottom>
          Reset Password
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Enter your email to receive a password reset link
        </Typography>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

      <form onSubmit={handleForgotPassword}>
        <TextField
          fullWidth
          label="Email"
          name="email"
          type="email"
          value={formData.email}
          onChange={handleInputChange}
          margin="normal"
          required
          autoComplete="email"
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <Email />
              </InputAdornment>
            ),
          }}
        />

        <Button
          type="submit"
          fullWidth
          variant="contained"
          disabled={loading}
          sx={{ mt: 3, mb: 2 }}
        >
          {loading ? 'Sending...' : 'Send Reset Link'}
        </Button>

        <Box sx={{ textAlign: 'center' }}>
          <Button
            variant="text"
            onClick={() => setMode('login')}
          >
            Back to Sign In
          </Button>
        </Box>
      </form>
    </Paper>
  );

  return (
    <Container component="main" maxWidth={mode === 'onboarding' ? 'md' : 'xs'} sx={{ py: 8 }}>
      {mode === 'login' && renderLoginForm()}
      {mode === 'register' && renderRegisterForm()}
      {mode === 'forgot' && renderForgotPasswordForm()}
      {mode === 'onboarding' && renderOnboardingFlow()}
    </Container>
  );
};

export default EnhancedAuth;
