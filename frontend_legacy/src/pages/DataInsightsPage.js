import React from 'react';
import { motion } from 'framer-motion';
import { CircleStackIcon, ChartBarIcon, CpuChipIcon } from '@heroicons/react/24/outline';

const DataInsightsPage = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-teal-900 to-cyan-800 text-white">
      <div className="container mx-auto px-4 py-8">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <CircleStackIcon className="w-12 h-12 text-teal-400 mr-4" />
            <h1 className="text-4xl font-bold bg-gradient-to-r from-teal-400 to-cyan-400 bg-clip-text text-transparent">
              AI Data Insights
            </h1>
          </div>
          <p className="text-xl text-gray-300">Extract meaningful insights from your data with AI</p>
        </motion.div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10">
            <ChartBarIcon className="w-8 h-8 text-teal-400 mb-4" />
            <h3 className="text-lg font-semibold mb-2">Data Analysis</h3>
            <p className="text-gray-400">Automated pattern recognition and trend analysis</p>
          </div>
          <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10">
            <CpuChipIcon className="w-8 h-8 text-cyan-400 mb-4" />
            <h3 className="text-lg font-semibold mb-2">ML Insights</h3>
            <p className="text-gray-400">Machine learning powered data interpretation</p>
          </div>
          <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10">
            <CircleStackIcon className="w-8 h-8 text-blue-400 mb-4" />
            <h3 className="text-lg font-semibold mb-2">Smart Reports</h3>
            <p className="text-gray-400">Automated report generation and visualization</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DataInsightsPage;