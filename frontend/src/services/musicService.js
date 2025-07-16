// Music Generation API Service

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:4700';

class MusicService {
  async generateMusic(musicData) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/music/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // Add authorization header when auth is implemented
          // 'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(musicData)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Music generation failed:', error);
      throw error;
    }
  }

  async getMusicGeneration(musicId) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/music/${musicId}`, {
        headers: {
          // 'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to get music generation:', error);
      throw error;
    }
  }

  async listMusicGenerations(params = {}) {
    try {
      const queryParams = new URLSearchParams({
        skip: params.skip || 0,
        limit: params.limit || 20,
        ...(params.style && { style: params.style }),
        ...(params.mood && { mood: params.mood }),
        ...(params.status && { status: params.status })
      });

      const response = await fetch(`${API_BASE_URL}/api/v1/music/?${queryParams}`, {
        headers: {
          // 'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to list music generations:', error);
      throw error;
    }
  }

  async deleteMusicGeneration(musicId) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/music/${musicId}`, {
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
      console.error('Failed to delete music generation:', error);
      throw error;
    }
  }

  async regenerateMusic(musicId) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/music/${musicId}/regenerate`, {
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
      console.error('Failed to regenerate music:', error);
      throw error;
    }
  }

  async getMusicStyles() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/music/styles/`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to get music styles:', error);
      throw error;
    }
  }

  async getMusicMoods() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/music/moods/`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to get music moods:', error);
      throw error;
    }
  }

  async downloadMusic(musicId, format = 'mp3') {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/music/${musicId}/download?format=${format}`, {
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

  async remixMusic(musicId, remixStyle, remixMood = null) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/music/${musicId}/remix`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // 'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          remix_style: remixStyle,
          ...(remixMood && { remix_mood: remixMood })
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to create music remix:', error);
      throw error;
    }
  }
}

export const musicService = new MusicService();
