import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  Container, 
  Typography, 
  TextField,
  Button, 
  Box, 
  Alert, 
  Card,
  CardContent,
  IconButton,
  InputAdornment
} from '@mui/material';
import { Visibility, VisibilityOff, Lock } from '@mui/icons-material';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:4700';

const PasswordReset = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [validToken, setValidToken] = useState(false);
  const [checking, setChecking] = useState(true);

  const [token, setToken] = useState('');
  const [userId, setUserId] = useState('');

  useEffect(() => {
    // Verify token is valid when component loads
    const checkToken = async () => {
      const params = new URLSearchParams(location.search);
      const tokenParam = params.get('token');
      const userParam = params.get('user');

      if (!tokenParam || !userParam) {
        setError('Invalid reset link. Please request a new password reset.');
        setChecking(false);
        return;
      }

      setToken(tokenParam);
      setUserId(userParam);

      try {
        const response = await axios.post(`${API_BASE_URL}/api/v1/enhanced-auth/validate-reset-token`, {
          token: tokenParam,
          user_id: userParam
        });

        if (response.status === 200) {
          setValidToken(true);
        }
      } catch (error) {
        if (error.response?.status === 400) {
          setError('This password reset link has expired or is invalid. Please request a new one.');
        } else {
          setError('Failed to validate reset link. Please try again.');
        }
      }
      
      setChecking(false);
    };

    checkToken();
  }, [location]);

  const validatePassword = () => {
    if (password.length < 8) {
      return 'Password must be at least 8 characters long';
    }
    if (!/[A-Z]/.test(password)) {
      return 'Password must contain at least one uppercase letter';
    }
    if (!/[a-z]/.test(password)) {
      return 'Password must contain at least one lowercase letter';
    }
    if (!/[0-9]/.test(password)) {
      return 'Password must contain at least one number';
    }
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
      return 'Password must contain at least one special character';
    }
    if (password !== confirmPassword) {
      return 'Passwords do not match';
    }
    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    const passwordError = validatePassword();
    if (passwordError) {
      setError(passwordError);
      return;
    }

    setLoading(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/v1/enhanced-auth/reset-password`, {
        token,
        user_id: userId,
        new_password: password
      });

      if (response.status === 200) {
        setSuccess(true);
        setTimeout(() => {
          navigate('/auth');
        }, 3000);
      }
    } catch (error) {
      if (error.response?.status === 400) {
        setError('Password reset failed. The link may have expired. Please request a new reset.');
      } else {
        setError('Failed to reset password. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  if (checking) {
    return (
      <Container component="main" maxWidth="sm" sx={{ py: 8 }}>
        <Card elevation={3}>
          <CardContent sx={{ p: 4, textAlign: 'center' }}>
            <Typography variant="h5" gutterBottom>
              Validating reset link...
            </Typography>
          </CardContent>
        </Card>
      </Container>
    );
  }

  if (!validToken) {
    return (
      <Container component="main" maxWidth="sm" sx={{ py: 8 }}>
        <Card elevation={3}>
          <CardContent sx={{ p: 4, textAlign: 'center' }}>
            <Lock sx={{ fontSize: 60, color: 'error.main', mb: 2 }} />
            <Typography variant="h5" gutterBottom color="error.main">
              Invalid Reset Link
            </Typography>
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
            <Button 
              variant="contained" 
              onClick={() => navigate('/auth')}
            >
              Request New Reset Link
            </Button>
          </CardContent>
        </Card>
      </Container>
    );
  }

  if (success) {
    return (
      <Container component="main" maxWidth="sm" sx={{ py: 8 }}>
        <Card elevation={3}>
          <CardContent sx={{ p: 4, textAlign: 'center' }}>
            <Typography variant="h4" gutterBottom color="success.main">
              Password Reset Successful!
            </Typography>
            <Alert severity="success" sx={{ mb: 3 }}>
              Your password has been successfully reset. You can now log in with your new password.
            </Alert>
            <Typography variant="body2" color="text.secondary">
              Redirecting you to login...
            </Typography>
          </CardContent>
        </Card>
      </Container>
    );
  }

  return (
    <Container component="main" maxWidth="sm" sx={{ py: 8 }}>
      <Card elevation={3}>
        <CardContent sx={{ p: 4 }}>
          <Box sx={{ textAlign: 'center', mb: 3 }}>
            <Lock sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
            <Typography variant="h4" gutterBottom>
              Reset Your Password
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Enter your new password below
            </Typography>
          </Box>

          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

          <form onSubmit={handleSubmit}>
            <TextField
              fullWidth
              label="New Password"
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              margin="normal"
              required
              InputProps={{
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

            <TextField
              fullWidth
              label="Confirm New Password"
              type={showPassword ? 'text' : 'password'}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              margin="normal"
              required
            />

            <Box sx={{ mt: 2, mb: 2 }}>
              <Typography variant="caption" color="text.secondary">
                Password must contain at least 8 characters with uppercase, lowercase, number, and special character.
              </Typography>
            </Box>

            <Button
              type="submit"
              fullWidth
              variant="contained"
              disabled={loading}
              sx={{ mt: 3, mb: 2 }}
            >
              {loading ? 'Resetting Password...' : 'Reset Password'}
            </Button>

            <Button
              fullWidth
              variant="text"
              onClick={() => navigate('/auth')}
            >
              Back to Login
            </Button>
          </form>
        </CardContent>
      </Card>
    </Container>
  );
};

export default PasswordReset;
