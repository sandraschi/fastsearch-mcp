import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { XMarkIcon, ClockIcon } from '@heroicons/react/24/outline';

const ProgressModal = ({ isOpen, progress, jobId, onClose }) => {
  const getProgressColor = (progress) => {
    if (progress < 30) return 'from-red-500 to-orange-500';
    if (progress < 70) return 'from-orange-500 to-yellow-500';
    return 'from-green-500 to-blue-500';
  };

  const getProgressMessage = (progress) => {
    if (progress < 10) return 'Initializing video generation...';
    if (progress < 30) return 'Processing your prompt...';
    if (progress < 60) return 'Generating video frames...';
    if (progress < 90) return 'Rendering final video...';
    return 'Almost done!';
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/80 backdrop-blur-sm"
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            className="relative bg-gray-900/90 backdrop-blur-xl border border-white/10 rounded-2xl p-8 max-w-md w-full mx-4"
          >
            {/* Close button */}
            <button
              onClick={onClose}
              className="absolute top-4 right-4 p-2 text-gray-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
            >
              <XMarkIcon className="w-5 h-5" />
            </button>

            {/* Content */}
            <div className="text-center">
              {/* Icon */}
              <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center mx-auto mb-6">
                <ClockIcon className="w-8 h-8 text-white animate-pulse" />
              </div>

              {/* Title */}
              <h3 className="text-2xl font-bold text-white mb-2">
                Generating Video
              </h3>

              {/* Job ID */}
              <p className="text-gray-400 text-sm mb-6">
                Job ID: {jobId?.slice(0, 8)}...
              </p>

              {/* Progress bar */}
              <div className="mb-6">
                <div className="flex items-center justify-between text-sm text-gray-400 mb-2">
                  <span>Progress</span>
                  <span>{progress}%</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-3 overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${progress}%` }}
                    transition={{ duration: 0.5, ease: 'easeOut' }}
                    className={`h-full bg-gradient-to-r ${getProgressColor(progress)} rounded-full relative`}
                  >
                    <div className="absolute inset-0 bg-white/20 animate-pulse rounded-full"></div>
                  </motion.div>
                </div>
              </div>

              {/* Status message */}
              <motion.p
                key={getProgressMessage(progress)}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-gray-300 mb-6"
              >
                {getProgressMessage(progress)}
              </motion.p>

              {/* Estimated time */}
              <div className="bg-white/5 backdrop-blur-sm rounded-lg p-4 border border-white/10">
                <p className="text-sm text-gray-400">Estimated time remaining</p>
                <p className="text-white font-semibold">
                  {progress < 50 ? '2-3 minutes' : progress < 80 ? '1-2 minutes' : 'Less than 1 minute'}
                </p>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

export default ProgressModal;
