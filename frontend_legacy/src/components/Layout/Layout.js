import React, { useState } from 'react';
import { motion } from 'framer-motion';
import Navigation from './Navigation';
import Sidebar from './Sidebar';
import TopBar from '../TopBar';

const Layout = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [theme, setTheme] = useState('dark');
  const [language, setLanguage] = useState('en');

  return (
    <div className={`min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-violet-800 ${theme}`}>
      {/* Top Bar */}
      <TopBar 
        toggleSidebar={() => setSidebarOpen(!sidebarOpen)}
        theme={theme}
        setTheme={setTheme}
        language={language}
        setLanguage={setLanguage}
      />
      
      {/* Sidebar */}
      <Sidebar open={sidebarOpen} setOpen={setSidebarOpen} />
      
      {/* Main content */}
      <div className={`transition-all duration-300 ${sidebarOpen ? 'lg:ml-64' : 'lg:ml-16'} pt-16`}>
        {/* Page content */}
        <main className="p-4 lg:p-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3 }}
            className="max-w-7xl mx-auto"
          >
            {children}
          </motion.div>
        </main>
      </div>
      
      {/* Navigation for mobile */}
      <Navigation />
    </div>
  );
};

export default Layout;
