import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { toast } from 'sonner';
import {
  SparklesIcon,
  PhotoIcon,
  PlayIcon,
  ClockIcon,

  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import VideoPreview from '../components/VideoPreview';
import ProgressModal from '../components/ProgressModal';

// Form validation schema
const generateSchema = z.object({
  prompt: z.string().min(10, 'Prompt must be at least 10 characters').max(2000, 'Prompt too long'),
  style: z.string(),
  aspectRatio: z.string(),
  duration: z.number().min(1).max(60),
  fps: z.number().min(12).max(60),
  resolution: z.string(),
  motionIntensity: z.string(),
  cameraMovement: z.string(),
  temperature: z.number().min(0).max(1),
  negativePrompt: z.string().optional(),
  seed: z.number().optional(),
});

const GeneratePage = () => {
  const [referenceImage, setReferenceImage] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationProgress, setGenerationProgress] = useState(0);
  const [currentJobId, setCurrentJobId] = useState(null);
  const [generatedVideo, setGeneratedVideo] = useState(null);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(generateSchema),
    defaultValues: {
      prompt: '',
      style: 'cinematic',
      aspectRatio: '16:9',
      duration: 5,
      fps: 24,
      resolution: '1080p',
      motionIntensity: 'medium',
      cameraMovement: 'static',
      temperature: 0.7,
      negativePrompt: '',
      seed: undefined,
    },
  });

  const watchedValues = watch();

  const onSubmit = async (data) => {
    try {
      setIsGenerating(true);
      setGenerationProgress(0);
      
      const requestData = {
        ...data,
        reference_image: referenceImage,
      };

      const response = await fetch('/api/v1/video/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        throw new Error('Failed to start video generation');
      }

      const result = await response.json();
      setCurrentJobId(result.job_id);
      
      pollProgress(result.job_id);
      toast.success('Video generation started!');
    } catch (error) {
      console.error('Generation error:', error);
      toast.error('Failed to generate video');
      setIsGenerating(false);
    }
  };

  const pollProgress = async (jobId) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`/api/v1/video/status/${jobId}`);
        const status = await response.json();
        
        setGenerationProgress(status.progress);
        
        if (status.status === 'completed') {
          clearInterval(pollInterval);
          setIsGenerating(false);
          setGeneratedVideo(`/api/v1/video/download/${jobId}`);
          toast.success('Video generated successfully!');
        } else if (status.status === 'failed') {
          clearInterval(pollInterval);
          setIsGenerating(false);
          toast.error(status.error_message || 'Video generation failed');
        }
      } catch (error) {
        console.error('Polling error:', error);
      }
    }, 2000);
  };

  const handleImageUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/v1/video/upload-reference', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to upload image');
      }

      const result = await response.json();
      setReferenceImage(result.image_base64);
      toast.success('Reference image uploaded!');
    } catch (error) {
      console.error('Upload error:', error);
      toast.error('Failed to upload image');
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <h1 className="text-3xl md:text-4xl font-bold text-white mb-4">
          Generate Your Video
        </h1>
        <p className="text-gray-400 max-w-2xl mx-auto">
          Describe your vision and watch AI bring it to life with stunning visuals
        </p>
      </motion.div>

      <div className="grid lg:grid-cols-2 gap-8">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="space-y-6"
        >
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <div className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-white/10">
              <label className="block text-sm font-medium text-white mb-3">
                <SparklesIcon className="w-5 h-5 inline mr-2" />
                Video Description
              </label>
              <textarea
                {...register('prompt')}
                rows={4}
                className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="Describe the video you want to create..."
              />
              {errors.prompt && (
                <p className="text-red-400 text-sm mt-2 flex items-center">
                  <ExclamationTriangleIcon className="w-4 h-4 mr-1" />
                  {errors.prompt.message}
                </p>
              )}
            </div>

            <div className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-white/10">
              <label className="block text-sm font-medium text-white mb-3">
                <PhotoIcon className="w-5 h-5 inline mr-2" />
                Reference Image (Optional)
              </label>
              <div className="flex items-center space-x-4">
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleImageUpload}
                  className="hidden"
                  id="reference-image"
                />
                <label
                  htmlFor="reference-image"
                  className="cursor-pointer px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white hover:bg-white/20 transition-colors"
                >
                  Choose Image
                </label>
                {referenceImage && (
                  <div className="w-16 h-16 rounded-lg overflow-hidden">
                    <img
                      src={`data:image/png;base64,${referenceImage}`}
                      alt="Reference"
                      className="w-full h-full object-cover"
                    />
                  </div>
                )}
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-4">
              <div className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-white/10">
                <label className="block text-sm font-medium text-white mb-3">
                  Visual Style
                </label>
                <select
                  {...register('style')}
                  className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="cinematic">Cinematic</option>
                  <option value="realistic">Realistic</option>
                  <option value="animated">Animated</option>
                  <option value="artistic">Artistic</option>
                </select>
              </div>

              <div className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-white/10">
                <label className="block text-sm font-medium text-white mb-3">
                  Aspect Ratio
                </label>
                <select
                  {...register('aspectRatio')}
                  className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="16:9">16:9 (Landscape)</option>
                  <option value="9:16">9:16 (Portrait)</option>
                  <option value="1:1">1:1 (Square)</option>
                </select>
              </div>
            </div>

            <div className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-white/10">
              <label className="block text-sm font-medium text-white mb-3">
                <ClockIcon className="w-5 h-5 inline mr-2" />
                Duration: {watchedValues.duration} seconds
              </label>
              <input
                type="range"
                {...register('duration', { valueAsNumber: true })}
                min="1"
                max="60"
                className="w-full accent-purple-500"
              />
            </div>

            <motion.button
              type="submit"
              disabled={isGenerating}
              whileHover={{ scale: isGenerating ? 1 : 1.02 }}
              whileTap={{ scale: isGenerating ? 1 : 0.98 }}
              className={`w-full py-4 px-6 rounded-xl font-semibold transition-all duration-300 ${
                isGenerating
                  ? 'bg-gray-600 cursor-not-allowed'
                  : 'bg-gradient-to-r from-purple-500 to-pink-500 hover:shadow-lg hover:shadow-purple-500/25'
              } text-white`}
            >
              {isGenerating ? (
                <div className="flex items-center justify-center">
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                  Generating...
                </div>
              ) : (
                <div className="flex items-center justify-center">
                  <PlayIcon className="w-5 h-5 mr-2" />
                  Generate Video
                </div>
              )}
            </motion.button>
          </form>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.4 }}
          className="space-y-6"
        >
          <div className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-white/10">
            <h3 className="text-lg font-semibold text-white mb-4">Preview</h3>
            {generatedVideo ? (
              <VideoPreview src={generatedVideo} />
            ) : (
              <div className="aspect-video bg-gray-800 rounded-lg flex items-center justify-center">
                <div className="text-center">
                  <PlayIcon className="w-12 h-12 text-gray-600 mx-auto mb-2" />
                  <p className="text-gray-400">Your video will appear here</p>
                </div>
              </div>
            )}
          </div>

          {watchedValues.prompt && (
            <div className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-white/10">
              <h3 className="text-lg font-semibold text-white mb-3">Settings Summary</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Style:</span>
                  <span className="text-white capitalize">{watchedValues.style}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Aspect Ratio:</span>
                  <span className="text-white">{watchedValues.aspectRatio}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Duration:</span>
                  <span className="text-white">{watchedValues.duration}s</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">FPS:</span>
                  <span className="text-white">{watchedValues.fps}</span>
                </div>
              </div>
            </div>
          )}
        </motion.div>
      </div>

      {/* Progress Modal */}
      {isGenerating && (
        <ProgressModal
          isOpen={isGenerating}
          progress={generationProgress}
          jobId={currentJobId}
          onClose={() => setIsGenerating(false)}
        />
      )}
    </div>
  );
};

export default GeneratePage;
