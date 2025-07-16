import React from 'react';
import { motion } from 'framer-motion';
import { ChartBarIcon } from '@heroicons/react/24/outline';

const AnalyticsPage = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-indigo-800 text-white">
      <div className="container mx-auto px-4 py-8">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <ChartBarIcon className="w-12 h-12 text-blue-400 mr-4" />
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
              AI Analytics Dashboard
            </h1>
          </div>
          <p className="text-xl text-gray-300">Comprehensive analytics and insights for your content</p>
        </motion.div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10">
            <h3 className="text-lg font-semibold mb-4">Content Performance</h3>
            <div className="text-3xl font-bold text-blue-400 mb-2">847</div>
            <p className="text-gray-400">Total content pieces generated</p>
          </div>
          <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10">
            <h3 className="text-lg font-semibold mb-4">User Engagement</h3>
            <div className="text-3xl font-bold text-green-400 mb-2">94%</div>
            <p className="text-gray-400">Average satisfaction rate</p>
          </div>
          <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10">
            <h3 className="text-lg font-semibold mb-4">Growth Rate</h3>
            <div className="text-3xl font-bold text-purple-400 mb-2">+156%</div>
            <p className="text-gray-400">Month over month growth</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsPage;