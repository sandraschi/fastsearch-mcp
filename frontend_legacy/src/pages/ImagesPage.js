import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  CameraIcon, 
  PhotoIcon, 
  SparklesIcon,

  ClockIcon
} from '@heroicons/react/24/outline';
import { imageService } from '../services/imageService';

const ImagesPage = () => {
  const [prompt, setPrompt] = useState('');
  const [style, setStyle] = useState('photorealistic');
  const [aspectRatio, setAspectRatio] = useState('16:9');
  const [quality, setQuality] = useState('standard');
  const [isGenerating, setIsGenerating] = useState(false);

  const imageStyles = [
    { id: 'photorealistic', name: 'Photorealistic', description: 'Realistic photography style' },
    { id: 'artistic', name: 'Artistic', description: 'Creative and artistic rendering' },
    { id: 'illustration', name: 'Illustration', description: 'Digital illustration style' },
    { id: 'painting', name: 'Painting', description: 'Traditional painting style' },
    { id: 'sketch', name: 'Sketch', description: 'Pencil sketch style' },
    { id: 'anime', name: 'Anime', description: 'Japanese anime style' },
    { id: 'cartoon', name: 'Cartoon', description: 'Cartoon illustration style' },
    { id: 'abstract', name: 'Abstract', description: 'Abstract art style' },
  ];

  const aspectRatios = [
    { id: '1:1', name: 'Square (1:1)', description: 'Perfect for social media' },
    { id: '16:9', name: 'Landscape (16:9)', description: 'Widescreen format' },
    { id: '9:16', name: 'Portrait (9:16)', description: 'Mobile-friendly vertical' },
    { id: '4:3', name: 'Classic (4:3)', description: 'Traditional photo format' },
  ];

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      alert('Please enter a description for your image');
      return;
    }

    setIsGenerating(true);
    
    try {
      const imageData = {
        prompt: prompt.trim(),
        style,
        aspect_ratio: aspectRatio,
        quality
      };

      const response = await imageService.generateImage(imageData);
      
      console.log('Image generation started:', response);
      alert(`Image generation started! Job ID: ${response.job_id}. Check the Gallery tab to see your image when it's ready.`);
      
      // Optionally redirect to Gallery or Jobs tab
      // window.location.href = '/gallery';
      
    } catch (error) {
      console.error('Image generation failed:', error);
      alert('Image generation failed. Please try again.');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-violet-800 text-white">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <div className="flex items-center justify-center mb-4">
            <CameraIcon className="w-12 h-12 text-purple-400 mr-4" />
            <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
              AI Image Generation
            </h1>
          </div>
          <p className="text-xl text-gray-300 max-w-2xl mx-auto">
            Create stunning images from text descriptions using Google's Imagen AI
          </p>
        </motion.div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Generation Panel */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="space-y-6"
          >
            {/* Prompt Input */}
            <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10">
              <label className="block text-lg font-semibold mb-3">
                Describe Your Image
              </label>
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="A serene mountain landscape at sunset with a crystal clear lake reflecting the golden sky..."
                className="w-full h-32 bg-gray-700/50 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
                maxLength={500}
              />
              <div className="flex justify-between items-center mt-2">
                <span className="text-sm text-gray-400">
                  {prompt.length}/500 characters
                </span>
                <span className="text-sm text-purple-400">
                  Be descriptive for best results
                </span>
              </div>
            </div>

            {/* Style Selection */}
            <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10">
              <label className="block text-lg font-semibold mb-3">
                Image Style
              </label>
              <div className="grid grid-cols-2 gap-3">
                {imageStyles.map((styleOption) => (
                  <button
                    key={styleOption.id}
                    onClick={() => setStyle(styleOption.id)}
                    className={`p-3 rounded-lg border-2 transition-all ${
                      style === styleOption.id
                        ? 'border-purple-500 bg-purple-500/20'
                        : 'border-gray-600 bg-gray-700/30 hover:border-gray-500'
                    }`}
                  >
                    <div className="text-left">
                      <div className="font-medium">{styleOption.name}</div>
                      <div className="text-sm text-gray-400">{styleOption.description}</div>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Aspect Ratio */}
            <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10">
              <label className="block text-lg font-semibold mb-3">
                Aspect Ratio
              </label>
              <div className="grid grid-cols-2 gap-3">
                {aspectRatios.map((ratio) => (
                  <button
                    key={ratio.id}
                    onClick={() => setAspectRatio(ratio.id)}
                    className={`p-3 rounded-lg border-2 transition-all ${
                      aspectRatio === ratio.id
                        ? 'border-purple-500 bg-purple-500/20'
                        : 'border-gray-600 bg-gray-700/30 hover:border-gray-500'
                    }`}
                  >
                    <div className="text-left">
                      <div className="font-medium">{ratio.name}</div>
                      <div className="text-sm text-gray-400">{ratio.description}</div>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Quality Settings */}
            <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10">
              <label className="block text-lg font-semibold mb-3">
                Quality Settings
              </label>
              <select
                value={quality}
                onChange={(e) => setQuality(e.target.value)}
                className="w-full bg-gray-700/50 border border-gray-600 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              >
                <option value="standard">Standard Quality</option>
                <option value="high">High Quality</option>
                <option value="ultra">Ultra Quality (Pro Plan)</option>
              </select>
            </div>

            {/* Generate Button */}
            <motion.button
              onClick={handleGenerate}
              disabled={isGenerating || !prompt.trim()}
              className={`w-full py-4 rounded-xl font-semibold text-lg flex items-center justify-center space-x-3 transition-all ${
                isGenerating || !prompt.trim()
                  ? 'bg-gray-600 cursor-not-allowed'
                  : 'bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 transform hover:scale-105'
              }`}
              whileHover={!isGenerating && prompt.trim() ? { scale: 1.02 } : {}}
              whileTap={!isGenerating && prompt.trim() ? { scale: 0.98 } : {}}
            >
              {isGenerating ? (
                <>
                  <ClockIcon className="w-6 h-6 animate-spin" />
                  <span>Generating Image...</span>
                </>
              ) : (
                <>
                  <SparklesIcon className="w-6 h-6" />
                  <span>Generate Image</span>
                </>
              )}
            </motion.button>
          </motion.div>

          {/* Preview/Info Panel */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="space-y-6"
          >
            {/* Preview Area */}
            <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10">
              <h3 className="text-lg font-semibold mb-4">Image Preview</h3>
              <div className="aspect-video bg-gray-700/30 rounded-lg border-2 border-dashed border-gray-600 flex items-center justify-center">
                <div className="text-center">
                  <PhotoIcon className="w-16 h-16 text-gray-500 mx-auto mb-4" />
                  <p className="text-gray-400">Your generated image will appear here</p>
                </div>
              </div>
            </div>

            {/* Tips & Guidelines */}
            <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10">
              <h3 className="text-lg font-semibold mb-4">💡 Pro Tips</h3>
              <div className="space-y-3 text-sm text-gray-300">
                <div className="flex items-start space-x-2">
                  <span className="text-purple-400">•</span>
                  <span>Be specific about lighting, colors, and composition</span>
                </div>
                <div className="flex items-start space-x-2">
                  <span className="text-purple-400">•</span>
                  <span>Include style keywords like "cinematic", "detailed", "artistic"</span>
                </div>
                <div className="flex items-start space-x-2">
                  <span className="text-purple-400">•</span>
                  <span>Mention camera angles and perspectives for better results</span>
                </div>
                <div className="flex items-start space-x-2">
                  <span className="text-purple-400">•</span>
                  <span>Avoid negative descriptions; focus on what you want to see</span>
                </div>
              </div>
            </div>

            {/* Recent Images */}
            <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10">
              <h3 className="text-lg font-semibold mb-4">Recent Images</h3>
              <div className="grid grid-cols-2 gap-3">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="aspect-square bg-gray-700/30 rounded-lg border border-gray-600 flex items-center justify-center">
                    <PhotoIcon className="w-8 h-8 text-gray-500" />
                  </div>
                ))}
              </div>
              <button className="w-full mt-4 py-2 text-purple-400 hover:text-purple-300 transition-colors">
                View All in Gallery →
              </button>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default ImagesPage;