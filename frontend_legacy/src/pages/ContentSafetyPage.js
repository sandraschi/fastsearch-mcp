import React from 'react';
import { motion } from 'framer-motion';
import { ShieldCheckIcon, ExclamationTriangleIcon, CheckCircleIcon } from '@heroicons/react/24/outline';

const ContentSafetyPage = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-green-900 to-emerald-800 text-white">
      <div className="container mx-auto px-4 py-8">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <ShieldCheckIcon className="w-12 h-12 text-green-400 mr-4" />
            <h1 className="text-4xl font-bold bg-gradient-to-r from-green-400 to-emerald-400 bg-clip-text text-transparent">
              Content Safety Monitor
            </h1>
          </div>
          <p className="text-xl text-gray-300">AI-powered content moderation and safety analysis</p>
        </motion.div>
        <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-8 border border-white/10">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center p-6 bg-green-500/10 rounded-lg border border-green-500/30">
              <CheckCircleIcon className="w-8 h-8 text-green-400 mx-auto mb-3" />
              <h3 className="font-semibold text-green-400 mb-2">Safe Content</h3>
              <div className="text-2xl font-bold">98.7%</div>
            </div>
            <div className="text-center p-6 bg-yellow-500/10 rounded-lg border border-yellow-500/30">
              <ExclamationTriangleIcon className="w-8 h-8 text-yellow-400 mx-auto mb-3" />
              <h3 className="font-semibold text-yellow-400 mb-2">Flagged</h3>
              <div className="text-2xl font-bold">1.2%</div>
            </div>
            <div className="text-center p-6 bg-red-500/10 rounded-lg border border-red-500/30">
              <ShieldCheckIcon className="w-8 h-8 text-red-400 mx-auto mb-3" />
              <h3 className="font-semibold text-red-400 mb-2">Blocked</h3>
              <div className="text-2xl font-bold">0.1%</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ContentSafetyPage;