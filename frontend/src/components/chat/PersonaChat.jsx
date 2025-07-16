import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Avatar,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  IconButton,
  Menu,
  MenuItem,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  CircularProgress,
  Alert
} from '@mui/material';
import {
  Send,
  SmartToy,
  Person,
  MoreVert,
  Add,
  VideoCall,
  Image,
  MusicNote,
  Code,
  School,
  Business,
  Movie,
  Brush
} from '@mui/icons-material';
import { format } from 'date-fns';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:4700';

// Persona selection dialog
const PersonaSelectionDialog = ({ open, onClose, onSelect, personas }) => {
  const getPersonaIcon = (personaId) => {
    const iconMap = {
      creative_assistant: <Brush />,
      technical_guide: <Code />,
      story_director: <Movie />,
      music_composer: <MusicNote />,
      brand_strategist: <Business />,
      educational_tutor: <School />
    };
    return iconMap[personaId] || <SmartToy />;
  };

  const getPersonaColor = (personaId) => {
    const colorMap = {
      creative_assistant: '#FF6B6B',
      technical_guide: '#4ECDC4',
      story_director: '#45B7D1',
      music_composer: '#96CEB4',
      brand_strategist: '#FFEAA7',
      educational_tutor: '#DDA0DD'
    };
    return colorMap[personaId] || '#666';
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Choose Your AI Persona</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Each persona has unique expertise and personality traits to help with different types of creative projects.
        </Typography>
        
        <Grid container spacing={2}>
          {personas.map((persona) => (
            <Grid item xs={12} sm={6} md={4} key={persona.id}>
              <Card 
                sx={{ 
                  cursor: 'pointer',
                  height: '100%',
                  '&:hover': { 
                    elevation: 4,
                    transform: 'translateY(-2px)',
                    transition: 'all 0.2s ease-in-out'
                  }
                }}
                onClick={() => onSelect(persona)}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Avatar sx={{ bgcolor: getPersonaColor(persona.id), mr: 2 }}>
                      {getPersonaIcon(persona.id)}
                    </Avatar>
                    <Typography variant="h6" component="div">
                      {persona.name}
                    </Typography>
                  </Box>
                  
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {persona.description}
                  </Typography>
                  
                  <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                    Personality: {persona.personality}
                  </Typography>
                  
                  <Box sx={{ mb: 1 }}>
                    {persona.expertise.slice(0, 3).map((skill, index) => (
                      <Chip 
                        key={index}
                        label={skill}
                        size="small"
                        variant="outlined"
                        sx={{ mr: 0.5, mb: 0.5 }}
                      />
                    ))}
                  </Box>
                  
                  {persona.tools.length > 0 && (
                    <Typography variant="caption" color="primary">
                      Can generate: {persona.tools.join(', ')}
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
      </DialogActions>
    </Dialog>
  );
};

// Message component
const ChatMessage = ({ message, persona }) => {
  const isUser = message.role === 'user';
  
  const renderGeneratedContent = (content) => {
    if (!content) return null;
    
    const getContentIcon = () => {
      switch (content.type) {
        case 'video': return <VideoCall />;
        case 'image': return <Image />;
        case 'music': return <MusicNote />;
        default: return <SmartToy />;
      }
    };
    
    return (
      <Card sx={{ mt: 1, bgcolor: 'primary.light', color: 'primary.contrastText' }}>
        <CardContent sx={{ p: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            {getContentIcon()}
            <Typography variant="subtitle2" sx={{ ml: 1 }}>
              {content.description}
            </Typography>
          </Box>
          
          <Typography variant="body2">
            Generated {content.type} content
          </Typography>
          
          {content.data && (
            <Button
              variant="outlined"
              size="small"
              sx={{ mt: 1, color: 'inherit', borderColor: 'inherit' }}
              onClick={() => {
                console.log('View content:', content.data);
              }}
            >
              View {content.type}
            </Button>
          )}
        </CardContent>
      </Card>
    );
  };

  return (
    <ListItem
      sx={{
        display: 'flex',
        flexDirection: isUser ? 'row-reverse' : 'row',
        alignItems: 'flex-start',
        mb: 1
      }}
    >
      <ListItemAvatar sx={{ minWidth: isUser ? 40 : 48, ml: isUser ? 1 : 0, mr: isUser ? 0 : 1 }}>
        <Avatar sx={{ bgcolor: isUser ? 'primary.main' : 'secondary.main' }}>
          {isUser ? <Person /> : <SmartToy />}
        </Avatar>
      </ListItemAvatar>
      
      <Box sx={{ flex: 1, maxWidth: '70%' }}>
        <Paper
          elevation={1}
          sx={{
            p: 2,
            bgcolor: isUser ? 'primary.main' : 'grey.100',
            color: isUser ? 'primary.contrastText' : 'text.primary',
            borderRadius: isUser ? '16px 16px 4px 16px' : '16px 16px 16px 4px'
          }}
        >
          {!isUser && persona && (
            <Typography variant="caption" color="primary" sx={{ fontWeight: 'bold', display: 'block', mb: 0.5 }}>
              {persona.name}
            </Typography>
          )}
          
          <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
            {message.content}
          </Typography>
          
          {message.generated_content && renderGeneratedContent(message.generated_content)}
          
          <Typography variant="caption" sx={{ opacity: 0.7, display: 'block', mt: 1 }}>
            {format(new Date(message.timestamp), 'HH:mm')}
          </Typography>
        </Paper>
      </Box>
    </ListItem>
  );
};

// Main Chat Interface
const PersonaChat = () => {
  const [conversations, setConversations] = useState([]);
  const [activeConversation, setActiveConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [personas, setPersonas] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const [personaDialogOpen, setPersonaDialogOpen] = useState(false);
  const [menuAnchor, setMenuAnchor] = useState(null);
  
  const messagesEndRef = useRef(null);
  const chatInputRef = useRef(null);

  // Scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load personas and conversations on component mount
  useEffect(() => {
    loadPersonas();
    loadConversations();
  }, []);

  const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return { Authorization: `Bearer ${token}` };
  };

  const loadPersonas = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/v1/chat/personas`);
      setPersonas(response.data);
    } catch (error) {
      console.error('Failed to load personas:', error);
      setError('Failed to load AI personas');
    }
  };

  const loadConversations = async () => {
    try {
      setLoading(true);
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/chat/conversations`,
        { headers: getAuthHeaders() }
      );
      setConversations(response.data);
    } catch (error) {
      console.error('Failed to load conversations:', error);
      setError('Failed to load conversations');
    } finally {
      setLoading(false);
    }
  };

  const loadConversationHistory = async (conversationId) => {
    try {
      setLoading(true);
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/chat/${conversationId}/history`,
        { headers: getAuthHeaders() }
      );
      
      setMessages(response.data.messages);
      setActiveConversation(response.data);
    } catch (error) {
      console.error('Failed to load conversation history:', error);
      setError('Failed to load conversation history');
    } finally {
      setLoading(false);
    }
  };

  const startNewConversation = async (persona) => {
    if (!newMessage.trim()) {
      setError('Please enter a message to start the conversation');
      return;
    }

    try {
      setSending(true);
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/chat/start`,
        {
          persona_id: persona.id,
          initial_message: newMessage,
          context: {}
        },
        { headers: getAuthHeaders() }
      );

      // Add user message and AI response to messages
      const userMessage = {
        role: 'user',
        content: newMessage,
        timestamp: new Date().toISOString()
      };

      const aiMessage = {
        role: 'assistant',
        content: response.data.response.message,
        persona_id: persona.id,
        generated_content: response.data.response.generated_content,
        timestamp: response.data.response.timestamp
      };

      setMessages([userMessage, aiMessage]);
      setActiveConversation({
        conversation_id: response.data.conversation_id,
        persona: response.data.persona
      });

      setNewMessage('');
      setPersonaDialogOpen(false);
      
      // Reload conversations list
      loadConversations();

    } catch (error) {
      console.error('Failed to start conversation:', error);
      setError('Failed to start conversation');
    } finally {
      setSending(false);
    }
  };

  const sendMessage = async () => {
    if (!newMessage.trim() || !activeConversation) return;

    try {
      setSending(true);
      
      // Add user message immediately
      const userMessage = {
        role: 'user',
        content: newMessage,
        timestamp: new Date().toISOString()
      };
      
      setMessages(prev => [...prev, userMessage]);
      const messageToSend = newMessage;
      setNewMessage('');

      // Send to API
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/chat/${activeConversation.conversation_id}/message`,
        {
          message: messageToSend,
          message_type: 'text'
        },
        { headers: getAuthHeaders() }
      );

      // Add AI response
      const aiMessage = {
        role: 'assistant',
        content: response.data.response.message,
        persona_id: activeConversation.persona.id,
        generated_content: response.data.response.generated_content,
        timestamp: response.data.response.timestamp
      };

      setMessages(prev => [...prev, aiMessage]);

    } catch (error) {
      console.error('Failed to send message:', error);
      setError('Failed to send message');
    } finally {
      setSending(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (activeConversation) {
        sendMessage();
      } else if (newMessage.trim()) {
        setPersonaDialogOpen(true);
      }
    }
  };

  const deleteConversation = async (conversationId) => {
    try {
      await axios.delete(
        `${API_BASE_URL}/api/v1/chat/${conversationId}`,
        { headers: getAuthHeaders() }
      );
      
      // Remove from conversations list
      setConversations(prev => prev.filter(conv => conv.id !== conversationId));
      
      // Clear active conversation if it was deleted
      if (activeConversation?.conversation_id === conversationId) {
        setActiveConversation(null);
        setMessages([]);
      }
      
    } catch (error) {
      console.error('Failed to delete conversation:', error);
      setError('Failed to delete conversation');
    }
  };

  return (
    <Box sx={{ display: 'flex', height: '100vh', bgcolor: 'background.default' }}>
      {/* Conversations Sidebar */}
      <Paper sx={{ width: 300, display: 'flex', flexDirection: 'column' }}>
        <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
          <Typography variant="h6">Persona Chat</Typography>
          <Button
            variant="contained"
            startIcon={<Add />}
            fullWidth
            sx={{ mt: 1 }}
            onClick={() => {
              if (newMessage.trim()) {
                setPersonaDialogOpen(true);
              } else {
                setError('Enter a message first, then choose a persona');
                chatInputRef.current?.focus();
              }
            }}
          >
            New Chat
          </Button>
        </Box>
        
        <List sx={{ flex: 1, overflow: 'auto' }}>
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          ) : conversations.length === 0 ? (
            <Box sx={{ p: 3, textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                No conversations yet. Start your first chat!
              </Typography>
            </Box>
          ) : (
            conversations.map((conv) => (
              <ListItem
                key={conv.id}
                button
                selected={activeConversation?.conversation_id === conv.id}
                onClick={() => loadConversationHistory(conv.id)}
                sx={{ borderRadius: 1, mx: 1 }}
              >
                <ListItemAvatar>
                  <Avatar sx={{ bgcolor: 'secondary.main' }}>
                    <SmartToy />
                  </Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={conv.persona.name}
                  secondary={conv.last_message}
                  secondaryTypographyProps={{
                    noWrap: true,
                    sx: { maxWidth: 180 }
                  }}
                />
                <IconButton
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation();
                    setMenuAnchor(e.currentTarget);
                  }}
                >
                  <MoreVert />
                </IconButton>
              </ListItem>
            ))
          )}
        </List>

        <Menu
          anchorEl={menuAnchor}
          open={Boolean(menuAnchor)}
          onClose={() => setMenuAnchor(null)}
        >
          <MenuItem onClick={() => {
            setMenuAnchor(null);
          }}>
            Delete Conversation
          </MenuItem>
        </Menu>
      </Paper>

      {/* Chat Area */}
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {/* Chat Header */}
        {activeConversation && (
          <Paper sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Avatar sx={{ bgcolor: 'secondary.main', mr: 2 }}>
                <SmartToy />
              </Avatar>
              <Box>
                <Typography variant="h6">
                  {activeConversation.persona.name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {activeConversation.persona.description}
                </Typography>
              </Box>
            </Box>
          </Paper>
        )}

        {/* Messages Area */}
        <Box sx={{ flex: 1, overflow: 'auto', p: 1 }}>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
              {error}
            </Alert>
          )}

          {!activeConversation ? (
            <Box sx={{ 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center', 
              height: '100%',
              textAlign: 'center'
            }}>
              <Box>
                <SmartToy sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h5" color="text.secondary" gutterBottom>
                  Welcome to Persona Chat
                </Typography>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                  Choose an AI persona to start a conversation. Each persona has unique expertise 
                  and can help with different creative projects.
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Type your message below and click "New Chat" to begin!
                </Typography>
              </Box>
            </Box>
          ) : (
            <List sx={{ width: '100%' }}>
              {messages.map((message, index) => (
                <ChatMessage
                  key={index}
                  message={message}
                  persona={activeConversation.persona}
                />
              ))}
              {sending && (
                <ListItem sx={{ justifyContent: 'center' }}>
                  <CircularProgress size={24} />
                  <Typography variant="body2" sx={{ ml: 1 }}>
                    {activeConversation.persona.name} is thinking...
                  </Typography>
                </ListItem>
              )}
              <div ref={messagesEndRef} />
            </List>
          )}
        </Box>

        {/* Message Input */}
        <Paper sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <TextField
              ref={chatInputRef}
              fullWidth
              multiline
              maxRows={4}
              placeholder={
                activeConversation 
                  ? `Message ${activeConversation.persona.name}...`
                  : "Type your message and choose a persona to start chatting..."
              }
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={sending}
            />
            <Button
              variant="contained"
              endIcon={<Send />}
              onClick={activeConversation ? sendMessage : () => setPersonaDialogOpen(true)}
              disabled={!newMessage.trim() || sending}
              sx={{ minWidth: 100 }}
            >
              {activeConversation ? 'Send' : 'Chat'}
            </Button>
          </Box>
        </Paper>
      </Box>

      {/* Persona Selection Dialog */}
      <PersonaSelectionDialog
        open={personaDialogOpen}
        onClose={() => setPersonaDialogOpen(false)}
        onSelect={startNewConversation}
        personas={personas}
      />
    </Box>
  );
};

export default PersonaChat;
