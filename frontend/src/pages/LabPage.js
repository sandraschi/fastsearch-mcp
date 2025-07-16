import React from 'react';
import { motion } from 'framer-motion';
import { BeakerIcon, CpuChipIcon, SparklesIcon, RocketLaunchIcon } from '@heroicons/react/24/outline';

const LabPage = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-orange-900 to-red-800 text-white">
      <div className="container mx-auto px-4 py-8">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <BeakerIcon className="w-12 h-12 text-orange-400 mr-4" />
            <h1 className="text-4xl font-bold bg-gradient-to-r from-orange-400 to-red-400 bg-clip-text text-transparent">
              AI Research Lab
            </h1>
          </div>
          <p className="text-xl text-gray-300">Experimental AI features and cutting-edge research</p>
        </motion.div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10">
            <CpuChipIcon className="w-8 h-8 text-orange-400 mb-4" />
            <h3 className="text-lg font-semibold mb-2">Beta Models</h3>
            <p className="text-gray-400 mb-4">Test the latest AI models before public release</p>
            <button className="px-4 py-2 bg-orange-600 hover:bg-orange-700 rounded transition-colors">
              Access Beta
            </button>
          </div>
          <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10">
            <SparklesIcon className="w-8 h-8 text-yellow-400 mb-4" />
            <h3 className="text-lg font-semibold mb-2">Experiments</h3>
            <p className="text-gray-400 mb-4">Try experimental AI features and techniques</p>
            <button className="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 rounded transition-colors">
              Start Experiment
            </button>
          </div>
          <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10">
            <RocketLaunchIcon className="w-8 h-8 text-red-400 mb-4" />
            <h3 className="text-lg font-semibold mb-2">Future Tech</h3>
            <p className="text-gray-400 mb-4">Preview upcoming AI technologies and innovations</p>
            <button className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded transition-colors">
              Explore Future
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LabPage;