import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { MicrophoneIcon, PlayIcon, PauseIcon } from '@heroicons/react/24/outline';

const AudioStudioPage = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-indigo-800 text-white">
      <div className="container mx-auto px-4 py-8">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <MicrophoneIcon className="w-12 h-12 text-purple-400 mr-4" />
            <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
              AI Audio Studio
            </h1>
          </div>
          <p className="text-xl text-gray-300">Record, enhance, and generate professional audio with AI</p>
        </motion.div>
        
        <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-8 border border-white/10 text-center">
          <div className="mb-8">
            <div className={`w-32 h-32 mx-auto rounded-full border-4 transition-all duration-300 ${
              isRecording 
                ? 'border-red-500 bg-red-500/20 animate-pulse' 
                : 'border-purple-500 bg-purple-500/20'
            } flex items-center justify-center`}>
              <MicrophoneIcon className={`w-16 h-16 ${isRecording ? 'text-red-400' : 'text-purple-400'}`} />
            </div>
          </div>

          <div className="flex items-center justify-center space-x-4">
            <button
              onClick={() => setIsRecording(!isRecording)}
              className={`px-8 py-4 rounded-full transition-all text-lg font-semibold ${
                isRecording 
                  ? 'bg-gradient-to-r from-gray-600 to-gray-700 hover:from-gray-700 hover:to-gray-800'
                  : 'bg-gradient-to-r from-red-600 to-pink-600 hover:from-red-700 hover:to-pink-700'
              }`}
            >
              <MicrophoneIcon className="w-6 h-6 inline mr-2" />
              {isRecording ? 'Stop Recording' : 'Start Recording'}
            </button>
            
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className="px-8 py-4 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 rounded-full transition-all text-lg font-semibold"
            >
              {isPlaying ? <PauseIcon className="w-6 h-6 inline mr-2" /> : <PlayIcon className="w-6 h-6 inline mr-2" />}
              {isPlaying ? 'Pause' : 'Play'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AudioStudioPage;