import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { toast } from 'sonner';
import {
  Cog6ToothIcon,
  KeyIcon,
  CloudIcon,
  BellIcon,
  UserIcon,
  ArrowDownTrayIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  LockClosedIcon,
} from '@heroicons/react/24/outline';
import { settingsService } from '../services/settingsService_enhanced';
import { useAuth } from '../contexts/AuthContext';

const SettingsPage = () => {
  const { user, isAuthenticated } = useAuth();
  const [settings, setSettings] = useState({
    googleApiKey: '',
    googleCloudProject: '',
    geminiApiKey: '',
    defaultStyle: 'cinematic',
    defaultDuration: 5,
    defaultAspectRatio: '16:9',
    autoSave: true,
    notifications: true,
    theme: 'dark',
  });

  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [authStatus, setAuthStatus] = useState({ authenticated: false, message: '' });

  // Check authentication status
  useEffect(() => {
    const checkAuthStatus = () => {
      const status = settingsService.getAuthenticationStatus();
      setAuthStatus(status);
    };

    checkAuthStatus();
    // Check auth status when component mounts and when user state changes
  }, [user]);

  // Load settings on component mount
  useEffect(() => {
    const loadSettings = async () => {
      try {
        const userSettings = await settingsService.getSettings();
        setSettings(userSettings);
      } catch (error) {
        console.error('Failed to load settings:', error);
        toast.error('Failed to load settings');
      } finally {
        setLoading(false);
      }
    };

    loadSettings();
  }, []);

  const handleSettingChange = (key, value) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const saveSettings = async () => {
    // Check authentication before attempting to save
    if (!authStatus.authenticated) {
      toast.error('Please log in to save your settings', {
        description: 'You can view settings without logging in, but saving requires authentication.',
        action: {
          label: 'Go to Login',
          onClick: () => window.location.href = '/auth'
        }
      });
      return;
    }

    setSaving(true);
    try {
      await settingsService.updateSettings(settings);
      toast.success('Settings saved successfully!', {
        description: 'Your preferences have been updated and will be applied immediately.'
      });
    } catch (error) {
      console.error('Failed to save settings:', error);
      
      const errorMessage = error.message || 'Failed to save settings';
      
      if (errorMessage.includes('log in') || errorMessage.includes('session')) {
        toast.error('Authentication Required', {
          description: errorMessage,
          action: {
            label: 'Go to Login',
            onClick: () => window.location.href = '/auth'
          }
        });
      } else if (errorMessage.includes('connect') || errorMessage.includes('backend')) {
        toast.error('Connection Error', {
          description: 'Cannot connect to VeoGen servers. Please check that the backend is running.',
        });
      } else {
        toast.error('Save Failed', {
          description: errorMessage
        });
      }
    } finally {
      setSaving(false);
    }
  };

  const testConnection = async () => {
    try {
      toast.info('Testing connection...', { description: 'Checking VeoGen services...' });
      
      const result = await settingsService.testConnection();
      
      if (result.success) {
        let successMessage = result.message || 'Connection successful!';
        
        toast.success('Connection Test Passed', {
          description: successMessage
        });
        
        // Show component details if available
        if (result.details && result.details.length > 0) {
          setTimeout(() => {
            toast.info('Service Components', {
              description: result.details.join(', ')
            });
          }, 1000);
        }
        
        // Test Gemini if API key is provided
        if (settings.geminiApiKey) {
          toast.info('Testing Gemini API...');
          
          const geminiResult = await settingsService.testGeminiConnection(settings.geminiApiKey);
          
          if (geminiResult.success) {
            toast.success('Gemini API', { description: geminiResult.message });
          } else {
            toast.warning('Gemini API Issue', { description: geminiResult.error });
          }
        }
        
      } else {
        toast.error('Connection Test Failed', {
          description: result.error
        });
      }
    } catch (error) {
      toast.error('Connection Test Error', {
        description: error.message
      });
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto space-y-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-purple-400 mx-auto mb-4"></div>
          <p className="text-xl text-gray-300">Loading settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <h1 className="text-3xl md:text-4xl font-bold text-white mb-4">
          Settings
        </h1>
        <p className="text-gray-400">
          Configure your VeoGen experience and API connections
        </p>
      </motion.div>

      {/* Authentication Status Banner */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className={`p-4 rounded-lg border ${
          authStatus.authenticated 
            ? 'bg-green-500/10 border-green-500/20 text-green-400'
            : 'bg-yellow-500/10 border-yellow-500/20 text-yellow-400'
        }`}
      >
        <div className="flex items-center">
          {authStatus.authenticated ? (
            <CheckCircleIcon className="w-5 h-5 mr-2" />
          ) : (
            <ExclamationTriangleIcon className="w-5 h-5 mr-2" />
          )}
          <span className="font-medium">
            {authStatus.authenticated ? 'Authenticated' : 'Authentication Required'}
          </span>
          <span className="ml-2 text-sm opacity-80">
            {authStatus.message}
          </span>
        </div>
      </motion.div>

      <div className="grid lg:grid-cols-2 gap-8">
        {/* API Configuration */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="space-y-6"
        >
          <div className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-white/10">
            <h2 className="text-xl font-semibold text-white mb-4 flex items-center">
              <KeyIcon className="w-6 h-6 mr-2" />
              API Configuration
            </h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-white mb-2">
                  Google API Key
                </label>
                <input
                  type="password"
                  value={settings.googleApiKey}
                  onChange={(e) => handleSettingChange('googleApiKey', e.target.value)}
                  className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder="Enter your Google API key"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-white mb-2">
                  Google Cloud Project ID
                </label>
                <input
                  type="text"
                  value={settings.googleCloudProject}
                  onChange={(e) => handleSettingChange('googleCloudProject', e.target.value)}
                  className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder="your-project-id"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-white mb-2">
                  Gemini API Key
                </label>
                <input
                  type="password"
                  value={settings.geminiApiKey}
                  onChange={(e) => handleSettingChange('geminiApiKey', e.target.value)}
                  className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder="Enter your Gemini API key"
                />
              </div>

              <button
                onClick={testConnection}
                className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white hover:bg-white/20 transition-colors flex items-center justify-center"
              >
                <CloudIcon className="w-5 h-5 mr-2" />
                Test Connection
              </button>
            </div>
          </div>

          {/* Default Settings */}
          <div className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-white/10">
            <h2 className="text-xl font-semibold text-white mb-4 flex items-center">
              <Cog6ToothIcon className="w-6 h-6 mr-2" />
              Default Generation Settings
            </h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-white mb-2">
                  Default Style
                </label>
                <select
                  value={settings.defaultStyle}
                  onChange={(e) => handleSettingChange('defaultStyle', e.target.value)}
                  className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="cinematic">Cinematic</option>
                  <option value="realistic">Realistic</option>
                  <option value="animated">Animated</option>
                  <option value="artistic">Artistic</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-white mb-2">
                  Default Duration (seconds)
                </label>
                <input
                  type="range"
                  min="1"
                  max="60"
                  value={settings.defaultDuration}
                  onChange={(e) => handleSettingChange('defaultDuration', parseInt(e.target.value))}
                  className="w-full accent-purple-500"
                />
                <div className="text-center text-white mt-2">{settings.defaultDuration}s</div>
              </div>

              <div>
                <label className="block text-sm font-medium text-white mb-2">
                  Default Aspect Ratio
                </label>
                <select
                  value={settings.defaultAspectRatio}
                  onChange={(e) => handleSettingChange('defaultAspectRatio', e.target.value)}
                  className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="16:9">16:9 (Landscape)</option>
                  <option value="9:16">9:16 (Portrait)</option>
                  <option value="1:1">1:1 (Square)</option>
                </select>
              </div>
            </div>
          </div>
        </motion.div>

        {/* User Preferences */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.4 }}
          className="space-y-6"
        >
          <div className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-white/10">
            <h2 className="text-xl font-semibold text-white mb-4 flex items-center">
              <UserIcon className="w-6 h-6 mr-2" />
              User Preferences
            </h2>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-white font-medium">Auto-save videos</h3>
                  <p className="text-gray-400 text-sm">Automatically save generated videos</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={settings.autoSave}
                    onChange={(e) => handleSettingChange('autoSave', e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                </label>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-white font-medium">Notifications</h3>
                  <p className="text-gray-400 text-sm">Receive notifications when videos are ready</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={settings.notifications}
                    onChange={(e) => handleSettingChange('notifications', e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                </label>
              </div>

              <div>
                <label className="block text-sm font-medium text-white mb-2">
                  Theme
                </label>
                <select
                  value={settings.theme}
                  onChange={(e) => handleSettingChange('theme', e.target.value)}
                  className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="dark">Dark</option>
                  <option value="light">Light</option>
                  <option value="auto">Auto</option>
                </select>
              </div>
            </div>
          </div>

          {/* System Info */}
          <div className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-white/10">
            <h2 className="text-xl font-semibold text-white mb-4">
              System Information
            </h2>
            
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">Version:</span>
                <span className="text-white">1.0.0</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Build:</span>
                <span className="text-white">2025.07.09</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Authentication:</span>
                <span className={authStatus.authenticated ? 'text-green-400' : 'text-yellow-400'}>
                  {authStatus.authenticated ? 'Logged In' : 'Anonymous'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Settings:</span>
                <span className={authStatus.authenticated ? 'text-green-400' : 'text-yellow-400'}>
                  {authStatus.authenticated ? 'Can Save' : 'Read Only'}
                </span>
              </div>
            </div>
          </div>

          {/* Save Button */}
          <motion.button
            onClick={saveSettings}
            disabled={saving}
            whileHover={{ scale: saving ? 1 : 1.02 }}
            whileTap={{ scale: saving ? 1 : 0.98 }}
            className={`w-full py-4 px-6 rounded-xl font-semibold transition-all duration-300 relative ${
              saving
                ? 'bg-gray-600 cursor-not-allowed'
                : authStatus.authenticated
                ? 'bg-gradient-to-r from-purple-500 to-pink-500 hover:shadow-lg hover:shadow-purple-500/25'
                : 'bg-gradient-to-r from-gray-600 to-gray-700 hover:from-gray-500 hover:to-gray-600'
            } text-white`}
          >
            {!authStatus.authenticated && (
              <LockClosedIcon className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5" />
            )}
            
            {saving ? (
              <div className="flex items-center justify-center">
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                Saving...
              </div>
            ) : (
              <div className="flex items-center justify-center">
                <ArrowDownTrayIcon className="w-5 h-5 mr-2" />
                {authStatus.authenticated ? 'Save Settings' : 'Login Required to Save'}
              </div>
            )}
          </motion.button>

          {/* Login Prompt */}
          {!authStatus.authenticated && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-lg"
            >
              <p className="text-yellow-400 text-sm mb-2">
                You can view settings without logging in, but saving requires authentication.
              </p>
              <button
                onClick={() => window.location.href = '/auth'}
                className="px-4 py-2 bg-yellow-500 text-black rounded-lg font-medium hover:bg-yellow-400 transition-colors"
              >
                Go to Login
              </button>
            </motion.div>
          )}
        </motion.div>
      </div>
    </div>
  );
};

export default SettingsPage;
