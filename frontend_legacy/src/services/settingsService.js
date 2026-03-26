// Fixed Settings Service for User Preferences

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
      // Convert to backend format
      const backendSettings = this.toBackendFormat(settingsData);
      
      const response = await fetch(`${API_BASE_URL}/api/v1/settings`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify(backendSettings)
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Please log in to save settings');
        }
        
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to save settings (${response.status})`);
      }

      const updatedSettings = await response.json();
      const frontendSettings = this.toFrontendFormat(updatedSettings);
      this.settings = frontendSettings;
      return frontendSettings;
      
    } catch (error) {
      console.error('Failed to update settings:', error);
      throw error;
    }
  }

  async getSetting(key) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/settings/${key}`, {
        method: 'GET',
        headers: this.getAuthHeaders()
      });

      if (!response.ok) {
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
      const response = await fetch(`${API_BASE_URL}/api/v1/settings/${key}`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify({ value, type })
      });

      if (!response.ok) {
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
        headers: this.getAuthHeaders()
      });

      if (response.ok) {
        const data = await response.json();
        const results = {
          success: true,
          data,
          message: `Connected to ${data.service} v${data.version}. Status: ${data.status}`,
          details: []
        };

        // Add component status details
        if (data.components) {
          for (const [component, status] of Object.entries(data.components)) {
            results.details.push(`${component}: ${status}`);
          }
        }

        return results;
      } else {
        return { 
          success: false, 
          error: `VeoGen API connection failed (${response.status})` 
        };
      }
    } catch (error) {
      return { 
        success: false, 
        error: `Network error: ${error.message}` 
      };
    }
  }

  // Test Gemini API specifically (if user has provided keys)
  async testGeminiConnection(apiKey) {
    if (!apiKey) {
      return { success: false, error: 'No Gemini API key provided' };
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/personas`, {
        method: 'GET',
        headers: {
          ...this.getAuthHeaders(),
          'X-Test-Gemini-Key': apiKey
        }
      });

      if (response.ok) {
        return { 
          success: true, 
          message: 'Gemini API connection successful' 
        };
      } else {
        return { 
          success: false, 
          error: `Gemini API test failed (${response.status})` 
        };
      }
    } catch (error) {
      return { 
        success: false, 
        error: `Gemini API error: ${error.message}` 
      };
    }
  }
}

export const settingsService = new SettingsService();
