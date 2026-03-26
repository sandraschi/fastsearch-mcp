// Image Generation API Service

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:4700';

class ImageService {
  async generateImage(imageData) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/image/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // Add authorization header when auth is implemented
          // 'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(imageData)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Image generation failed:', error);
      throw error;
    }
  }

  async getImageGeneration(imageId) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/image/${imageId}`, {
        headers: {
          // 'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to get image generation:', error);
      throw error;
    }
  }

  async listImageGenerations(params = {}) {
    try {
      const queryParams = new URLSearchParams({
        skip: params.skip || 0,
        limit: params.limit || 20,
        ...(params.style && { style: params.style }),
        ...(params.quality && { quality: params.quality }),
        ...(params.status && { status: params.status })
      });

      const response = await fetch(`${API_BASE_URL}/api/v1/image/?${queryParams}`, {
        headers: {
          // 'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to list image generations:', error);
      throw error;
    }
  }

  async deleteImageGeneration(imageId) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/image/${imageId}`, {
        method: 'DELETE',
        headers: {
          // 'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to delete image generation:', error);
      throw error;
    }
  }

  async regenerateImage(imageId) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/image/${imageId}/regenerate`, {
        method: 'POST',
        headers: {
          // 'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to regenerate image:', error);
      throw error;
    }
  }

  async getImageStyles() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/image/styles/`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to get image styles:', error);
      throw error;
    }
  }

  async getImageQualities() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/image/qualities/`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to get image qualities:', error);
      throw error;
    }
  }

  async downloadImage(imageId, format = 'png') {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/image/${imageId}/download?format=${format}`, {
        headers: {
          // 'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.download_url;
    } catch (error) {
      console.error('Failed to get download URL:', error);
      throw error;
    }
  }

  async createImageVariations(imageId, variationCount = 4) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/image/${imageId}/variations?variation_count=${variationCount}`, {
        method: 'POST',
        headers: {
          // 'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to create image variations:', error);
      throw error;
    }
  }
}

export const imageService = new ImageService();
