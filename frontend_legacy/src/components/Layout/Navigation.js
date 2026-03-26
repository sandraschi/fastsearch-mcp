import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  HomeIcon,
  SparklesIcon,
  FilmIcon,
  BookOpenIcon,
  PhotoIcon,
  Cog6ToothIcon,
} from '@heroicons/react/24/outline';

const navigationItems = [
  { name: 'Home', href: '/', icon: HomeIcon },
  { name: 'Generate', href: '/generate', icon: SparklesIcon },
  { name: 'Movies', href: '/moviemaker', icon: FilmIcon },
  { name: 'Books', href: '/bookmaker', icon: BookOpenIcon },
  { name: 'Gallery', href: '/gallery', icon: PhotoIcon },
  { name: 'Settings', href: '/settings', icon: Cog6ToothIcon },
];

const Navigation = () => {
  const location = useLocation();

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-40 bg-gray-900/90 backdrop-blur-xl border-t border-white/10 lg:hidden pb-safe">
      <div className="flex items-center justify-around py-2">
        {navigationItems.map((item) => {
          const isActive = location.pathname === item.href;
          return (
            <Link
              key={item.name}
              to={item.href}
              className="flex flex-col items-center px-3 py-2 text-xs"
            >
              <motion.div
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
                className={`p-2 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                <item.icon className="w-5 h-5" />
              </motion.div>
              <span
                className={`mt-1 ${
                  isActive ? 'text-white font-medium' : 'text-gray-400'
                }`}
              >
                {item.name}
              </span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
};

export default Navigation;
