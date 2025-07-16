import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { toast } from 'sonner';
import {
  Cog6ToothIcon,
  KeyIcon,
  CloudIcon,

  UserIcon,
  ArrowDownTrayIcon,
} from '@heroicons/react/24/outline';
import { settingsService } from '../services/settingsService';

const SettingsPage = () => {
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
    setSaving(true);
    try {
      await settingsService.updateSettings(settings);
      toast.success('Settings saved successfully!');
    } catch (error) {
      console.error('Failed to save settings:', error);
      
      // Show specific error message
      const errorMessage = error.message || 'Failed to save settings';
      toast.error(errorMessage);
      
      // If authentication error, suggest login
      if (errorMessage.includes('log in') || errorMessage.includes('401')) {
        toast.error('Please log in to save your settings');
      }
    } finally {
      setSaving(false);
    }
  };

  const testConnection = async () => {
    try {
      // Test basic VeoGen connection
      const result = await settingsService.testConnection();
      
      if (result.success) {
        let successMessage = result.message || 'Connection successful!';
        
        if (result.details && result.details.length > 0) {
          successMessage += `\n\nComponents:\n${result.details.join('\n')}`;
        }
        
        toast.success(successMessage);
        
        // Also test Gemini if API key is provided
        if (settings.geminiApiKey) {
          toast.info('Testing Gemini API...');
          
          const geminiResult = await settingsService.testGeminiConnection(settings.geminiApiKey);
          
          if (geminiResult.success) {
            toast.success('Gemini API connection verified!');
          } else {
            toast.warning(`Gemini API issue: ${geminiResult.error}`);
          }
        }
        
        // Log detailed info for debugging
        console.log('Connection test result:', result.data);
      } else {
        toast.error(`Connection failed: ${result.error}`);
      }
    } catch (error) {
      toast.error(`Connection test failed: ${error.message}`);
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
                <span className="text-white">2024.01.15</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">API Status:</span>
                <span className="text-green-400">Connected</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Storage Used:</span>
                <span className="text-white">2.4 GB / 10 GB</span>
              </div>
            </div>
          </div>

          {/* Save Button */}
          <motion.button
            onClick={saveSettings}
            disabled={saving}
            whileHover={{ scale: saving ? 1 : 1.02 }}
            whileTap={{ scale: saving ? 1 : 0.98 }}
            className={`w-full py-4 px-6 rounded-xl font-semibold transition-all duration-300 ${
              saving
                ? 'bg-gray-600 cursor-not-allowed'
                : 'bg-gradient-to-r from-purple-500 to-pink-500 hover:shadow-lg hover:shadow-purple-500/25'
            } text-white`}
          >
            {saving ? (
              <div className="flex items-center justify-center">
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                Saving...
              </div>
            ) : (
              <div className="flex items-center justify-center">
                <ArrowDownTrayIcon className="w-5 h-5 mr-2" />
                Save Settings
              </div>
            )}
          </motion.button>
        </motion.div>
      </div>
    </div>
  );
};

export default SettingsPage;
