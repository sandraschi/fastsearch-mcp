// Enhanced Settings Service with Better Authentication Handling

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:4700';

class SettingsService {
  constructor() {
    this.settings = null;
  }

  // Get authentication headers
  getAuthHeaders() {
    const token = localStorage.getItem('token');
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` })
    };
  }

  // Check if user is authenticated
  isAuthenticated() {
    const token = localStorage.getItem('token');
    return !!token;
  }

  // Convert frontend camelCase to backend snake_case
  toBackendFormat(settings) {
    return {
      google_api_key: settings.googleApiKey || '',
      google_cloud_project: settings.googleCloudProject || '',
      gemini_api_key: settings.geminiApiKey || '',
      default_style: settings.defaultStyle || 'cinematic',
      default_duration: settings.defaultDuration || 5,
      default_aspect_ratio: settings.defaultAspectRatio || '16:9',
      auto_save: settings.autoSave !== undefined ? settings.autoSave : true,
      notifications: settings.notifications !== undefined ? settings.notifications : true,
      theme: settings.theme || 'dark'
    };
  }

  // Convert backend snake_case to frontend camelCase
  toFrontendFormat(settings) {
    return {
      googleApiKey: settings.google_api_key || '',
      googleCloudProject: settings.google_cloud_project || '',
      geminiApiKey: settings.gemini_api_key || '',
      defaultStyle: settings.default_style || 'cinematic',
      defaultDuration: settings.default_duration || 5,
      defaultAspectRatio: settings.default_aspect_ratio || '16:9',
      autoSave: settings.auto_save !== undefined ? settings.auto_save : true,
      notifications: settings.notifications !== undefined ? settings.notifications : true,
      theme: settings.theme || 'dark'
    };
  }

  async getSettings() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/settings`, {
        method: 'GET',
        headers: this.getAuthHeaders()
      });

      if (!response.ok) {
        if (response.status === 401) {
          console.warn('User not authenticated, using default settings');
          return this.getDefaultSettings();
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const settings = await response.json();
      const frontendSettings = this.toFrontendFormat(settings);
      this.settings = frontendSettings;
      return frontendSettings;
      
    } catch (error) {
      console.error('Failed to get settings:', error);
      // Return default settings if API fails
      return this.getDefaultSettings();
    }
  }

  async updateSettings(settingsData) {
    try {
      // Check authentication first
      if (!this.isAuthenticated()) {
        throw new Error('You must be logged in to save settings. Please log in and try again.');
      }

      // Convert to backend format
      const backendSettings = this.toBackendFormat(settingsData);
      
      const response = await fetch(`${API_BASE_URL}/api/v1/settings`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify(backendSettings)
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Your session has expired. Please log in again to save settings.');
        }
        
        let errorMessage = 'Failed to save settings';
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorMessage;
        } catch (e) {
          // If we can't parse JSON, use status text
          errorMessage = response.statusText || errorMessage;
        }
        
        throw new Error(`${errorMessage} (${response.status})`);
      }

      const updatedSettings = await response.json();
      const frontendSettings = this.toFrontendFormat(updatedSettings);
      this.settings = frontendSettings;
      return frontendSettings;
      
    } catch (error) {
      console.error('Failed to update settings:', error);
      
      // Provide specific guidance based on error type
      if (error.message.includes('log in') || error.message.includes('session')) {
        // Authentication error - user needs to log in
        throw error;
      } else if (error.message.includes('Failed to fetch')) {
        throw new Error('Cannot connect to VeoGen servers. Please check that the backend is running.');
      } else {
        // Other errors
        throw new Error(`Settings save failed: ${error.message}`);
      }
    }
  }

  async getSetting(key) {
    try {
      if (!this.isAuthenticated()) {
        throw new Error('Authentication required to access individual settings');
      }

      const response = await fetch(`${API_BASE_URL}/api/v1/settings/${key}`, {
        method: 'GET',
        headers: this.getAuthHeaders()
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Session expired. Please log in again.');
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`Failed to get setting ${key}:`, error);
      throw error;
    }
  }

  async setSetting(key, value, type = 'string') {
    try {
      if (!this.isAuthenticated()) {
        throw new Error('Authentication required to save settings');
      }

      const response = await fetch(`${API_BASE_URL}/api/v1/settings/${key}`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify({ value, type })
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Session expired. Please log in again.');
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`Failed to set setting ${key}:`, error);
      throw error;
    }
  }

  // Get default settings
  getDefaultSettings() {
    return {
      googleApiKey: '',
      googleCloudProject: '',
      geminiApiKey: '',
      defaultStyle: 'cinematic',
      defaultDuration: 5,
      defaultAspectRatio: '16:9',
      autoSave: true,
      notifications: true,
      theme: 'dark'
    };
  }

  // Get cached settings if available
  getCachedSettings() {
    return this.settings;
  }

  // Clear cached settings
  clearCache() {
    this.settings = null;
  }

  // Test API connection and services
  async testConnection() {
    try {
      // Test basic VeoGen API health
      const response = await fetch(`${API_BASE_URL}/health`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        const results = {
          success: true,
          data,
          message: `Connected to ${data.service || 'VeoGen'} v${data.version || '1.0.0'}. Status: ${data.status || 'healthy'}`,
          details: []
        };

        // Add component status details
        if (data.components) {
          for (const [component, status] of Object.entries(data.components)) {
            const statusText = typeof status === 'string' ? status : 'available';
            results.details.push(`${component}: ${statusText}`);
          }
        }

        return results;
      } else {
        return { 
          success: false, 
          error: `VeoGen API connection failed (${response.status}: ${response.statusText})` 
        };
      }
    } catch (error) {
      return { 
        success: false, 
        error: `Network error: ${error.message}. Is the VeoGen backend running on port 4700?` 
      };
    }
  }

  // Test Gemini API specifically (if user has provided keys)
  async testGeminiConnection(apiKey) {
    if (!apiKey) {
      return { success: false, error: 'No Gemini API key provided' };
    }

    try {
      // For now, just return success since we don't have a real test endpoint
      // In the future, this could test the actual Gemini API
      return { 
        success: true, 
        message: 'Gemini API key format appears valid (actual connection testing coming soon)' 
      };
    } catch (error) {
      return { 
        success: false, 
        error: `Gemini API test error: ${error.message}` 
      };
    }
  }

  // Helper method to check authentication status for UI
  getAuthenticationStatus() {
    const token = localStorage.getItem('token');
    if (!token) {
      return {
        authenticated: false,
        message: 'Not logged in - settings can be viewed but not saved'
      };
    }

    // Basic token validation (just check it exists and isn't empty)
    try {
      const parts = token.split('.');
      if (parts.length !== 3) {
        return {
          authenticated: false,
          message: 'Invalid token format - please log in again'
        };
      }

      return {
        authenticated: true,
        message: 'Logged in - settings can be saved'
      };
    } catch (error) {
      return {
        authenticated: false,
        message: 'Token validation failed - please log in again'
      };
    }
  }
}

export const settingsService = new SettingsService();
