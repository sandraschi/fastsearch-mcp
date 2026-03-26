import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ChatBubbleLeftRightIcon,
  PaperAirplaneIcon,
  SparklesIcon,
  CpuChipIcon,
  LightBulbIcon,
  BeakerIcon,
  PaintBrushIcon,
  MusicalNoteIcon,
  FilmIcon,
  CodeBracketIcon,
  AcademicCapIcon,
  HeartIcon,
  PlusIcon,
  TrashIcon,
} from '@heroicons/react/24/outline';
import { chatService } from '../services/chatService';

const ChatPage = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [selectedPersona, setSelectedPersona] = useState('creative_director');
  const [isTyping, setIsTyping] = useState(false);
  const [personas, setPersonas] = useState([]);
  const [loading, setLoading] = useState(true);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Load personas from backend
  useEffect(() => {
    const loadPersonas = async () => {
      try {
        const personasData = await chatService.getPersonas();
        // Add icon and color mapping for the personas
        const personasWithIcons = personasData.map(persona => {
          const iconMap = {
            'creative_director': SparklesIcon,
            'video_specialist': FilmIcon,
            'image_artist': PaintBrushIcon,
            'music_composer': MusicalNoteIcon,
            'tech_advisor': CpuChipIcon,
            'content_strategist': LightBulbIcon,
            'research_scientist': BeakerIcon,
            'coding_mentor': CodeBracketIcon,
            'learning_coach': AcademicCapIcon,
            'wellness_guide': HeartIcon
          };
          
          const colorMap = {
            'creative_director': 'from-purple-500 to-pink-500',
            'video_specialist': 'from-blue-500 to-cyan-500',
            'image_artist': 'from-green-500 to-emerald-500',
            'music_composer': 'from-orange-500 to-red-500',
            'tech_advisor': 'from-gray-500 to-slate-500',
            'content_strategist': 'from-yellow-500 to-amber-500',
            'research_scientist': 'from-indigo-500 to-purple-500',
            'coding_mentor': 'from-teal-500 to-cyan-500',
            'learning_coach': 'from-rose-500 to-pink-500',
            'wellness_guide': 'from-emerald-500 to-green-500'
          };
          
          return {
            ...persona,
            icon: iconMap[persona.id] || SparklesIcon,
            color: colorMap[persona.id] || 'from-purple-500 to-pink-500'
          };
        });
        
        setPersonas(personasWithIcons);
        if (personasWithIcons.length > 0) {
          setSelectedPersona(personasWithIcons[0].id);
        }
      } catch (error) {
        console.error('Failed to load personas:', error);
        // Fallback to default persona if API fails
        setPersonas([{
          id: 'creative_director',
          name: 'Creative Director',
          icon: SparklesIcon,
          color: 'from-purple-500 to-pink-500',
          description: 'Video production and creative direction expert',
          expertise: ['Video Production', 'Creative Direction', 'Storytelling', 'Visual Design'],
          personality: 'Visionary creative leader with a passion for compelling visual narratives'
        }]);
      } finally {
        setLoading(false);
      }
    };
    
    loadPersonas();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    inputRef.current?.focus();
  }, [selectedPersona]);

  // Initialize with welcome message
  useEffect(() => {
    if (messages.length === 0) {
      const welcomeMessage = {
        id: Date.now(),
        type: 'assistant',
        content: `Hello! I'm your ${personas.find(p => p.id === selectedPersona)?.name}. I'm here to help you with ${personas.find(p => p.id === selectedPersona)?.description.toLowerCase()}. What would you like to work on today?`,
        persona: selectedPersona,
        timestamp: new Date()
      };
      setMessages([welcomeMessage]);
    }
  }, [selectedPersona, messages.length, personas]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputMessage.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsTyping(true);

    try {
      const response = await chatService.sendMessage({
        message: inputMessage.trim(),
        persona: selectedPersona,
        conversation_history: messages
      });

      const assistantMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: response.response,
        persona: selectedPersona,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: 'I apologize, but I encountered an error. Please try again.',
        persona: selectedPersona,
        timestamp: new Date(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const startNewConversation = () => {
    setMessages([]);
  };

  const clearCurrentChat = () => {
    setMessages([]);
  };

  const changePersona = (personaId) => {
    setSelectedPersona(personaId);
    setMessages([]); // Clear messages when changing persona
  };

  const currentPersona = personas.find(p => p.id === selectedPersona);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-violet-800 text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-purple-400 mx-auto mb-4"></div>
          <p className="text-xl text-gray-300">Loading AI personas...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-violet-800 text-white">
      <div className="container mx-auto px-4 py-8 h-screen flex flex-col">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-6"
        >
          <div className="flex items-center justify-center mb-4">
            <ChatBubbleLeftRightIcon className="w-12 h-12 text-purple-400 mr-4" />
            <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
              AI Chat Assistant
            </h1>
          </div>
          <p className="text-xl text-gray-300">
            Chat with specialized AI personas for all your creative needs
          </p>
        </motion.div>

        <div className="flex-1 grid lg:grid-cols-4 gap-6 min-h-0">
          {/* Persona Selector */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="lg:col-span-1 space-y-4"
          >
            <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-4 border border-white/10">
              <h3 className="text-lg font-semibold mb-4">Choose Your Assistant</h3>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {personas.map((persona) => {
                  const IconComponent = persona.icon;
                  return (
                    <button
                      key={persona.id}
                      onClick={() => changePersona(persona.id)}
                      className={`w-full p-3 rounded-lg border-2 transition-all text-left ${
                        selectedPersona === persona.id
                          ? 'border-purple-500 bg-purple-500/20'
                          : 'border-gray-600 bg-gray-700/30 hover:border-gray-500'
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        <div className={`p-2 rounded-lg bg-gradient-to-r ${persona.color}`}>
                          <IconComponent className="w-5 h-5 text-white" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-sm">{persona.name}</div>
                          <div className="text-xs text-gray-400 truncate">{persona.description}</div>
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>

              {/* Chat Controls */}
              <div className="mt-4 pt-4 border-t border-gray-600 space-y-2">
                <button
                  onClick={startNewConversation}
                  className="w-full flex items-center justify-center space-x-2 py-2 px-3 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors text-sm"
                >
                  <PlusIcon className="w-4 h-4" />
                  <span>New Chat</span>
                </button>
                <button
                  onClick={clearCurrentChat}
                  className="w-full flex items-center justify-center space-x-2 py-2 px-3 bg-gray-600 hover:bg-gray-700 rounded-lg transition-colors text-sm"
                >
                  <TrashIcon className="w-4 h-4" />
                  <span>Clear Chat</span>
                </button>
              </div>
            </div>

            {/* Current Persona Info */}
            {currentPersona && (
              <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-4 border border-white/10">
                <div className="flex items-center space-x-3 mb-3">
                  <div className={`p-2 rounded-lg bg-gradient-to-r ${currentPersona.color}`}>
                    <currentPersona.icon className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h4 className="font-medium">{currentPersona.name}</h4>
                    <p className="text-xs text-gray-400">{currentPersona.personality}</p>
                  </div>
                </div>
                <div className="text-xs text-gray-300">
                  <div className="font-medium mb-1">Expertise:</div>
                  <div className="flex flex-wrap gap-1">
                    {currentPersona.expertise.map((skill, index) => (
                      <span key={index} className="px-2 py-1 bg-gray-700 rounded text-xs">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </motion.div>

          {/* Chat Area */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="lg:col-span-3 flex flex-col min-h-0"
          >
            <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl border border-white/10 flex-1 flex flex-col min-h-0">
              {/* Chat Header */}
              <div className="p-4 border-b border-gray-600">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {currentPersona && (
                      <>
                        <div className={`p-2 rounded-lg bg-gradient-to-r ${currentPersona.color}`}>
                          <currentPersona.icon className="w-5 h-5 text-white" />
                        </div>
                        <div>
                          <h3 className="font-semibold">{currentPersona.name}</h3>
                          <p className="text-sm text-gray-400">Ready to assist you</p>
                        </div>
                      </>
                    )}
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-400">
                      {messages.filter(m => m.type === 'user').length} messages
                    </span>
                  </div>
                </div>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0">
                <AnimatePresence>
                  {messages.map((message) => (
                    <motion.div
                      key={message.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-[80%] rounded-lg p-3 ${
                          message.type === 'user'
                            ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white'
                            : message.isError
                            ? 'bg-red-600/20 border border-red-500/50 text-red-200'
                            : 'bg-gray-700/50 text-gray-100'
                        }`}
                      >
                        <div className="flex items-start space-x-2">
                          {message.type === 'assistant' && (
                            <div className="flex-shrink-0 mt-1">
                              {currentPersona ? (
                                <div className={`p-1 rounded bg-gradient-to-r ${currentPersona.color}`}>
                                  <currentPersona.icon className="w-4 h-4 text-white" />
                                </div>
                              ) : (
                                <SparklesIcon className="w-5 h-5 text-purple-400" />
                              )}
                            </div>
                          )}
                          <div className="flex-1">
                            <div className="whitespace-pre-wrap">{message.content}</div>
                            <div className="text-xs opacity-70 mt-1">
                              {message.timestamp.toLocaleTimeString()}
                            </div>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>

                {/* Typing indicator */}
                {isTyping && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex justify-start"
                  >
                    <div className="bg-gray-700/50 rounded-lg p-3 flex items-center space-x-2">
                      <div className={`p-1 rounded bg-gradient-to-r ${currentPersona?.color}`}>
                        {currentPersona?.icon && <currentPersona.icon className="w-4 h-4 text-white" />}
                      </div>
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                      </div>
                    </div>
                  </motion.div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Message Input */}
              <div className="p-4 border-t border-gray-600">
                <div className="flex space-x-3">
                  <textarea
                    ref={inputRef}
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder={`Ask ${currentPersona?.name} anything...`}
                    className="flex-1 bg-gray-700/50 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
                    rows="2"
                    disabled={isTyping}
                  />
                  <button
                    onClick={handleSendMessage}
                    disabled={!inputMessage.trim() || isTyping}
                    className={`px-6 py-3 rounded-lg font-medium transition-all ${
                      !inputMessage.trim() || isTyping
                        ? 'bg-gray-600 cursor-not-allowed'
                        : 'bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700'
                    }`}
                  >
                    <PaperAirplaneIcon className="w-5 h-5" />
                  </button>
                </div>
                <div className="flex items-center justify-between mt-2 text-xs text-gray-400">
                  <span>Press Enter to send, Shift+Enter for new line</span>
                  <span>{inputMessage.length}/2000</span>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default ChatPage;