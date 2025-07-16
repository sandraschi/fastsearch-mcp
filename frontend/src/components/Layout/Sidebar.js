import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  HomeIcon,
  SparklesIcon,
  FilmIcon,
  PhotoIcon,
  ClockIcon,
  Cog6ToothIcon,
  CameraIcon,
  MusicalNoteIcon,
  QuestionMarkCircleIcon,
  ChatBubbleLeftRightIcon,
  MagnifyingGlassIcon,
  DocumentTextIcon,
  CodeBracketIcon,
  LanguageIcon,
  MicrophoneIcon,
  ChartBarIcon,
  ShieldCheckIcon,
  PaintBrushIcon,
  CircleStackIcon,
  BeakerIcon,
  GlobeAltIcon,
  BookOpenIcon,
} from '@heroicons/react/24/outline';

const navigationItems = [
  { name: 'Home', href: '/', icon: HomeIcon },
  { name: 'Generate', href: '/generate', icon: SparklesIcon },
  { name: 'Movie Maker', href: '/moviemaker', icon: FilmIcon },
  { name: 'Book Maker', href: '/bookmaker', icon: BookOpenIcon },
  { name: 'Images', href: '/images', icon: CameraIcon },
  { name: 'Music', href: '/music', icon: MusicalNoteIcon },
  { name: 'Chat', href: '/chat', icon: ChatBubbleLeftRightIcon },
  { name: 'AI Search', href: '/search', icon: MagnifyingGlassIcon },
  { name: 'Documents', href: '/documents', icon: DocumentTextIcon },
  { name: 'Code Assistant', href: '/code', icon: CodeBracketIcon },
  { name: 'Translation', href: '/translation', icon: LanguageIcon },
  { name: 'Audio Studio', href: '/audio', icon: MicrophoneIcon },
  { name: 'Future Predictor', href: '/predictor', icon: SparklesIcon },
  { name: 'Analytics', href: '/analytics', icon: ChartBarIcon },
  { name: 'Content Safety', href: '/safety', icon: ShieldCheckIcon },
  { name: 'Style Transfer', href: '/style', icon: PaintBrushIcon },
  { name: 'Data Insights', href: '/insights', icon: CircleStackIcon },
  { name: 'Multimodal', href: '/multimodal', icon: GlobeAltIcon },
  { name: 'Lab', href: '/lab', icon: BeakerIcon },
  { name: 'Gallery', href: '/gallery', icon: PhotoIcon },
  { name: 'Jobs', href: '/jobs', icon: ClockIcon },
  { name: 'Settings', href: '/settings', icon: Cog6ToothIcon },
  { name: 'Help', href: '/help', icon: QuestionMarkCircleIcon },
];

const Sidebar = ({ open, setOpen }) => {
  const location = useLocation();

  return (
    <>
      {/* Overlay for mobile */}
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-40 bg-black bg-opacity-50 lg:hidden"
          onClick={() => setOpen(false)}
        />
      )}

      {/* Sidebar */}
      <motion.div
        initial={false}
        animate={{ width: open ? 256 : 64 }}
        className="fixed left-0 top-16 z-50 h-[calc(100vh-4rem)] bg-gray-900/90 backdrop-blur-xl border-r border-white/10 hidden lg:block"
      >
        <div className="flex flex-col h-full">
          {/* Navigation */}
          <nav className="flex-1 px-3 py-4 space-y-1">
            {navigationItems.map((item) => {
              const isActive = location.pathname === item.href;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`flex items-center px-3 py-3 rounded-lg transition-all duration-200 group ${
                    isActive
                      ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white'
                      : 'text-gray-300 hover:bg-white/10 hover:text-white'
                  }`}
                >
                  <item.icon
                    className={`w-6 h-6 ${open ? 'mr-3' : 'mx-auto'} ${
                      isActive ? 'text-white' : 'text-gray-400 group-hover:text-white'
                    }`}
                  />
                  {open && (
                    <motion.span
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: 0.1 }}
                      className="font-medium"
                    >
                      {item.name}
                    </motion.span>
                  )}
                </Link>
              );
            })}
          </nav>

          {/* Footer */}
          <div className="px-3 py-4">
            <div className={`flex items-center ${open ? 'justify-start' : 'justify-center'}`}>
              <div className="w-8 h-8 bg-gradient-to-br from-green-400 to-blue-500 rounded-full flex items-center justify-center">
                <span className="text-xs font-bold text-white">AI</span>
              </div>
              {open && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.1 }}
                  className="ml-3"
                >
                  <p className="text-sm font-medium text-white">AI Studio</p>
                  <p className="text-xs text-gray-400">Powered by Veo</p>
                </motion.div>
              )}
            </div>
          </div>
        </div>
      </motion.div>
    </>
  );
};

export default Sidebar;
