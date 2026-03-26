import React from 'react';
import { motion } from 'framer-motion';
import {
  Bars3Icon,
  BellIcon,
  UserCircleIcon,
} from '@heroicons/react/24/outline';

const Header = ({ toggleSidebar }) => {
  return (
    <header className="bg-white/5 backdrop-blur-xl border-b border-white/10">
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Left side */}
          <div className="flex items-center">
            <button
              onClick={toggleSidebar}
              className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-colors lg:hidden"
            >
              <Bars3Icon className="w-6 h-6" />
            </button>
            
            <div className="hidden lg:block">
              <h1 className="text-2xl font-bold text-white">
                AI Video Studio
              </h1>
              <p className="text-sm text-gray-400">
                Create stunning videos with Veo AI
              </p>
            </div>
          </div>

          {/* Right side */}
          <div className="flex items-center space-x-4">
            {/* Notifications */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="relative p-2 text-gray-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
            >
              <BellIcon className="w-6 h-6" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
            </motion.button>

            {/* User menu */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="flex items-center space-x-3 p-2 text-gray-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
            >
              <UserCircleIcon className="w-8 h-8" />
              <div className="hidden md:block text-left">
                <p className="text-sm font-medium text-white">Creator</p>
                <p className="text-xs text-gray-400">Pro Plan</p>
              </div>
            </motion.button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
