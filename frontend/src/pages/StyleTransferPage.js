import React from 'react';
import { motion } from 'framer-motion';
import { PaintBrushIcon, PhotoIcon, SparklesIcon } from '@heroicons/react/24/outline';

const StyleTransferPage = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-pink-900 to-rose-800 text-white">
      <div className="container mx-auto px-4 py-8">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <PaintBrushIcon className="w-12 h-12 text-pink-400 mr-4" />
            <h1 className="text-4xl font-bold bg-gradient-to-r from-pink-400 to-rose-400 bg-clip-text text-transparent">
              AI Style Transfer
            </h1>
          </div>
          <p className="text-xl text-gray-300">Transform images with artistic AI style transfer</p>
        </motion.div>
        <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-8 border border-white/10">
          <div className="text-center py-12">
            <PhotoIcon className="w-16 h-16 text-gray-500 mx-auto mb-4" />
            <h3 className="text-xl font-medium text-gray-400 mb-2">Upload Image for Style Transfer</h3>
            <p className="text-gray-500">Apply artistic styles from famous paintings to your images</p>
            <button className="mt-6 px-6 py-3 bg-gradient-to-r from-pink-600 to-rose-600 rounded-lg hover:from-pink-700 hover:to-rose-700 transition-all">
              <SparklesIcon className="w-5 h-5 inline mr-2" />
              Start Style Transfer
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StyleTransferPage;