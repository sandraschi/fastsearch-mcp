// Chat Service for AI Personas

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:4700';

class ChatService {
  constructor() {
    this.conversations = new Map(); // Store conversations client-side for demo
  }

  async sendMessage(messageData) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // Add authorization header when auth is implemented
          // 'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(messageData)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Chat message failed:', error);
      throw error;
    }
  }

  async getPersonas() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/personas`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to get personas:', error);
      throw error;
    }
  }

  async createConversation(personaId, title = null) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/conversations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // 'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          persona_id: personaId,
          title
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to create conversation:', error);
      throw error;
    }
  }

  async getConversations() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/conversations`, {
        headers: {
          // 'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to get conversations:', error);
      throw error;
    }
  }

  async getConversationMessages(conversationId) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/conversations/${conversationId}/messages`, {
        headers: {
          // 'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to get conversation messages:', error);
      throw error;
    }
  }

  async deleteConversation(conversationId) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/conversations/${conversationId}`, {
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
      console.error('Failed to delete conversation:', error);
      throw error;
    }
  }

  async updateConversationTitle(conversationId, title) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/conversations/${conversationId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          // 'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ title })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to update conversation title:', error);
      throw error;
    }
  }

  async exportConversation(conversationId, format = 'json') {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/conversations/${conversationId}/export?format=${format}`, {
        headers: {
          // 'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      if (format === 'json') {
        return await response.json();
      } else {
        return await response.text();
      }
    } catch (error) {
      console.error('Failed to export conversation:', error);
      throw error;
    }
  }

  async regenerateResponse(conversationId, messageId) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/conversations/${conversationId}/messages/${messageId}/regenerate`, {
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
      console.error('Failed to regenerate response:', error);
      throw error;
    }
  }

  // Client-side conversation management for demo
  saveConversationLocally(conversationId, messages) {
    this.conversations.set(conversationId, {
      id: conversationId,
      messages: [...messages],
      lastUpdated: new Date()
    });
  }

  getLocalConversation(conversationId) {
    return this.conversations.get(conversationId);
  }

  getAllLocalConversations() {
    return Array.from(this.conversations.values());
  }

  clearLocalConversations() {
    this.conversations.clear();
  }
}

export const chatService = new ChatService();
