import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'sonner';
import { AnimatePresence } from 'framer-motion';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

// Components
import Layout from './components/Layout/Layout';
import HomePage from './pages/HomePage';
import GeneratePage from './pages/GeneratePage';
import MovieMakerPage from './pages/MovieMakerPage';
import BookMakerPage from './pages/BookMakerPage';
import ImagesPage from './pages/ImagesPage';
import MusicPage from './pages/MusicPage';
import ChatPage from './pages/ChatPage';
import AISearchPage from './pages/AISearchPage';
import DocumentsPage from './pages/DocumentsPage';
import CodeAssistantPage from './pages/CodeAssistantPage';
import TranslationPage from './pages/TranslationPage';
import AudioStudioPage from './pages/AudioStudioPage';
import FuturePredictorPage from './pages/FuturePredictorPage';
import AnalyticsPage from './pages/AnalyticsPage';
import ContentSafetyPage from './pages/ContentSafetyPage';
import StyleTransferPage from './pages/StyleTransferPage';
import DataInsightsPage from './pages/DataInsightsPage';
import MultimodalPage from './pages/MultimodalPage';
import LabPage from './pages/LabPage';
import GalleryPage from './pages/GalleryPage';
import JobsPage from './pages/JobsPage';
import SettingsPage from './pages/SettingsPage';
import HelpPage from './pages/HelpPage';
import VoiceControlSideTab from './components/VoiceControlSideTab';

// Auth Components
import EnhancedAuth from './components/auth/EnhancedAuth';
import EmailVerification from './components/auth/EmailVerification';
import PasswordReset from './components/auth/PasswordReset';
import ProtectedRoute from './components/auth/ProtectedRoute';
import { AuthProvider } from './contexts/AuthContext';

// Styles
import './App.css';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
});

// Create Material-UI theme
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#8b5cf6',
    },
    secondary: {
      main: '#ec4899',
    },
    background: {
      default: '#0f0f23',
      paper: '#1a1a2e',
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <AuthProvider>
          <Router>
            <div className="App min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-violet-800">
              <AnimatePresence mode="wait">
                <Routes>
                  {/* Public routes */}
                  <Route path="/auth" element={<EnhancedAuth />} />
                  <Route path="/verify-email" element={<EmailVerification />} />
                  <Route path="/reset-password" element={<PasswordReset />} />
                  
                  {/* Dashboard redirect to home */}
                  <Route path="/dashboard" element={
                    <ProtectedRoute>
                      <Layout>
                        <HomePage />
                      </Layout>
                    </ProtectedRoute>
                  } />
                  
                  {/* Protected routes */}
                  <Route path="/" element={
                    <ProtectedRoute>
                      <Layout>
                        <HomePage />
                      </Layout>
                    </ProtectedRoute>
                  } />
                  <Route path="/generate" element={
                    <ProtectedRoute>
                      <Layout>
                        <GeneratePage />
                      </Layout>
                    </ProtectedRoute>
                  } />
                  <Route path="/moviemaker" element={
                    <ProtectedRoute>
                      <Layout>
                        <MovieMakerPage />
                      </Layout>
                    </ProtectedRoute>
                  } />
                  <Route path="/bookmaker" element={
                    <ProtectedRoute>
                      <Layout>
                        <BookMakerPage />
                      </Layout>
                    </ProtectedRoute>
                  } />
                  <Route path="/images" element={
                    <ProtectedRoute>
                      <Layout>
                        <ImagesPage />
                      </Layout>
                    </ProtectedRoute>
                  } />
                  <Route path="/music" element={
                    <ProtectedRoute>
                      <Layout>
                        <MusicPage />
                      </Layout>
                    </ProtectedRoute>
                  } />
                  <Route path="/chat" element={
                    <ProtectedRoute>
                      <Layout>
                        <ChatPage />
                      </Layout>
                    </ProtectedRoute>
                  } />
                  <Route path="/search" element={
                    <ProtectedRoute>
                      <Layout>
                        <AISearchPage />
                      </Layout>
                    </ProtectedRoute>
                  } />
                  <Route path="/documents" element={
                    <ProtectedRoute>
                      <Layout>
                        <DocumentsPage />
                      </Layout>
                    </ProtectedRoute>
                  } />
                  <Route path="/code" element={
                    <ProtectedRoute>
                      <Layout>
                        <CodeAssistantPage />
                      </Layout>
                    </ProtectedRoute>
                  } />
                  <Route path="/translation" element={
                    <ProtectedRoute>
                      <Layout>
                        <TranslationPage />
                      </Layout>
                    </ProtectedRoute>
                  } />
                  <Route path="/audio" element={
                    <ProtectedRoute>
                      <Layout>
                        <AudioStudioPage />
                      </Layout>
                    </ProtectedRoute>
                  } />
                  <Route path="/predictor" element={
                    <ProtectedRoute>
                      <Layout>
                        <FuturePredictorPage />
                      </Layout>
                    </ProtectedRoute>
                  } />
                  <Route path="/analytics" element={
                    <ProtectedRoute>
                      <Layout>
                        <AnalyticsPage />
                      </Layout>
                    </ProtectedRoute>
                  } />
                  <Route path="/safety" element={
                    <ProtectedRoute>
                      <Layout>
                        <ContentSafetyPage />
                      </Layout>
                    </ProtectedRoute>
                  } />
                  <Route path="/style" element={
                    <ProtectedRoute>
                      <Layout>
                        <StyleTransferPage />
                      </Layout>
                    </ProtectedRoute>
                  } />
                  <Route path="/insights" element={
                    <ProtectedRoute>
                      <Layout>
                        <DataInsightsPage />
                      </Layout>
                    </ProtectedRoute>
                  } />
                  <Route path="/multimodal" element={
                    <ProtectedRoute>
                      <Layout>
                        <MultimodalPage />
                      </Layout>
                    </ProtectedRoute>
                  } />
                  <Route path="/lab" element={
                    <ProtectedRoute>
                      <Layout>
                        <LabPage />
                      </Layout>
                    </ProtectedRoute>
                  } />
                  <Route path="/gallery" element={
                    <ProtectedRoute>
                      <Layout>
                        <GalleryPage />
                      </Layout>
                    </ProtectedRoute>
                  } />
                  <Route path="/jobs" element={
                    <ProtectedRoute>
                      <Layout>
                        <JobsPage />
                      </Layout>
                    </ProtectedRoute>
                  } />
                  <Route path="/settings" element={
                    <ProtectedRoute>
                      <Layout>
                        <SettingsPage />
                      </Layout>
                    </ProtectedRoute>
                  } />
                  <Route path="/help" element={
                    <ProtectedRoute>
                      <Layout>
                        <HelpPage />
                      </Layout>
                    </ProtectedRoute>
                  } />
                </Routes>
              </AnimatePresence>
              
              {/* Toast notifications */}
              <Toaster 
                position="top-right" 
                theme="dark"
                richColors
                closeButton
              />
              
              {/* Voice Control Side Tab - Available globally */}
              <VoiceControlSideTab />
            </div>
          </Router>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
