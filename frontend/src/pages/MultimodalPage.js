import React from 'react';
import { motion } from 'framer-motion';
import { GlobeAltIcon, PhotoIcon, MicrophoneIcon, VideoCameraIcon } from '@heroicons/react/24/outline';

const MultimodalPage = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-violet-800 text-white">
      <div className="container mx-auto px-4 py-8">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <GlobeAltIcon className="w-12 h-12 text-purple-400 mr-4" />
            <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-400 to-violet-400 bg-clip-text text-transparent">
              Multimodal AI Studio
            </h1>
          </div>
          <p className="text-xl text-gray-300">Combine text, image, audio, and video with AI</p>
        </motion.div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10 text-center">
            <PhotoIcon className="w-8 h-8 text-blue-400 mx-auto mb-4" />
            <h3 className="font-semibold mb-2">Image + Text</h3>
            <p className="text-sm text-gray-400">Visual content generation</p>
          </div>
          <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10 text-center">
            <MicrophoneIcon className="w-8 h-8 text-green-400 mx-auto mb-4" />
            <h3 className="font-semibold mb-2">Audio + Text</h3>
            <p className="text-sm text-gray-400">Voice synthesis and analysis</p>
          </div>
          <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10 text-center">
            <VideoCameraIcon className="w-8 h-8 text-purple-400 mx-auto mb-4" />
            <h3 className="font-semibold mb-2">Video + Audio</h3>
            <p className="text-sm text-gray-400">Complete multimedia creation</p>
          </div>
          <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10 text-center">
            <GlobeAltIcon className="w-8 h-8 text-orange-400 mx-auto mb-4" />
            <h3 className="font-semibold mb-2">Multi-Modal</h3>
            <p className="text-sm text-gray-400">All formats combined</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MultimodalPage;