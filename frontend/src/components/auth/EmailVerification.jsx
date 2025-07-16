import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  Container, 
  Typography, 
  Button, 
  Box, 
  Alert, 
  CircularProgress,
  Card,
  CardContent 
} from '@mui/material';
import { CheckCircle, Error } from '@mui/icons-material';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:4700';

const EmailVerification = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [status, setStatus] = useState('verifying'); // 'verifying', 'success', 'error'
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const verifyEmail = async () => {
      const params = new URLSearchParams(location.search);
      const token = params.get('token');
      const userId = params.get('user');

      if (!token || !userId) {
        setStatus('error');
        setMessage('Invalid verification link. Please check your email for the correct link.');
        setLoading(false);
        return;
      }

      try {
        const response = await axios.post(`${API_BASE_URL}/api/v1/enhanced-auth/verify-email`, {
          token,
          user_id: userId
        });

        if (response.status === 200) {
          setStatus('success');
          setMessage('Your email has been successfully verified! You can now access all VeoGen features.');
          
          // Auto-redirect after 3 seconds
          setTimeout(() => {
            navigate('/auth');
          }, 3000);
        }
      } catch (error) {
        console.error('Email verification error:', error);
        setStatus('error');
        if (error.response?.status === 400) {
          setMessage('This verification link has expired or is invalid. Please request a new verification email.');
        } else if (error.response?.status === 404) {
          setMessage('User not found. Please check the verification link or register again.');
        } else {
          setMessage('Verification failed. Please try again or contact support.');
        }
      }
      
      setLoading(false);
    };

    verifyEmail();
  }, [location, navigate]);

  const handleResendVerification = async () => {
    try {
      const token = localStorage.getItem('token');
      if (token) {
        await axios.post(`${API_BASE_URL}/api/v1/enhanced-auth/resend-verification`, {}, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setMessage('New verification email sent! Please check your inbox.');
      } else {
        navigate('/auth');
      }
    } catch (error) {
      setMessage('Failed to resend verification email. Please try logging in again.');
    }
  };

  return (
    <Container component="main" maxWidth="sm" sx={{ py: 8 }}>
      <Card elevation={3}>
        <CardContent sx={{ p: 4, textAlign: 'center' }}>
          {loading ? (
            <>
              <CircularProgress size={60} sx={{ mb: 3 }} />
              <Typography variant="h5" gutterBottom>
                Verifying your email...
              </Typography>
              <Typography color="text.secondary">
                Please wait while we verify your email address.
              </Typography>
            </>
          ) : (
            <>
              {status === 'success' ? (
                <>
                  <CheckCircle sx={{ fontSize: 80, color: 'success.main', mb: 2 }} />
                  <Typography variant="h4" gutterBottom color="success.main">
                    Email Verified!
                  </Typography>
                  <Alert severity="success" sx={{ mb: 3 }}>
                    {message}
                  </Alert>
                  <Typography variant="body2" color="text.secondary">
                    Redirecting you to login...
                  </Typography>
                </>
              ) : (
                <>
                  <Error sx={{ fontSize: 80, color: 'error.main', mb: 2 }} />
                  <Typography variant="h4" gutterBottom color="error.main">
                    Verification Failed
                  </Typography>
                  <Alert severity="error" sx={{ mb: 3 }}>
                    {message}
                  </Alert>
                  <Box sx={{ mt: 3 }}>
                    <Button 
                      variant="contained" 
                      onClick={handleResendVerification}
                      sx={{ mr: 2 }}
                    >
                      Resend Verification Email
                    </Button>
                    <Button 
                      variant="outlined" 
                      onClick={() => navigate('/auth')}
                    >
                      Back to Login
                    </Button>
                  </Box>
                </>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </Container>
  );
};

export default EmailVerification;
