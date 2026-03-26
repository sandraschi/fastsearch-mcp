import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { toast } from 'sonner';
import {
  FilmIcon,
  SparklesIcon,
  PlayIcon,
  DocumentTextIcon,
  CogIcon,
  ClockIcon,
  CurrencyDollarIcon,
  PencilIcon,
  CheckIcon,
} from '@heroicons/react/24/outline';

// Form validation schema
const movieSchema = z.object({
  title: z.string().min(3, 'Title must be at least 3 characters').max(100, 'Title too long'),
  concept: z.string().min(20, 'Concept must be at least 20 characters').max(1000, 'Concept too long'),
  style: z.string(),
  preset: z.string(),
  maxClips: z.number().min(3).max(50),
  budget: z.number().min(1).max(100),
});

const MovieMakerPage = () => {
  const [currentStep, setCurrentStep] = useState('setup'); // setup, script, review, production
  const [generatedScript, setGeneratedScript] = useState('');
  const [isGeneratingScript, setIsGeneratingScript] = useState(false);
  const [scenes, setScenes] = useState([]);
  const [productionProgress, setProductionProgress] = useState(0);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(movieSchema),
    defaultValues: {
      title: '',
      concept: '',
      style: 'cinematic',
      preset: 'short-film',
      maxClips: 10,
      budget: 5.0,
    },
  });

  const watchedValues = watch();

  const movieStyles = [
    { id: 'anime', name: '🎨 Anime', description: 'Japanese animation style with vibrant colors' },
    { id: 'pixar', name: '🎭 Pixar', description: '3D animated movie style with character focus' },
    { id: 'wes-anderson', name: '🎪 Wes Anderson', description: 'Symmetrical, pastel-colored cinematography' },
    { id: 'claymation', name: '🏺 Claymation', description: 'Stop-motion clay animation texture' },
    { id: 'svankmajer', name: '🎪 Švankmajer', description: 'Surreal, dark stop-motion style' },
    { id: 'advertisement', name: '📺 Advertisement', description: 'Clean, commercial-style presentation' },
    { id: 'music-video', name: '🎵 Music Video', description: 'Dynamic, rhythm-focused cinematography' },
    { id: 'cinematic', name: '🎬 Cinematic', description: 'Hollywood blockbuster production value' },
    { id: 'documentary', name: '📰 Documentary', description: 'Realistic, informational presentation' },
  ];

  const moviePresets = [
    { id: 'commercial', name: '📺 Commercial', clips: '3-5', duration: '24-40s', cost: '$0.30-1.25' },
    { id: 'short-film', name: '🎬 Short Film', clips: '5-10', duration: '40-80s', cost: '$0.50-2.50' },
    { id: 'music-video', name: '🎵 Music Video', clips: '8-15', duration: '64-120s', cost: '$0.80-3.75' },
    { id: 'story', name: '📖 Story', clips: '10-20', duration: '80-160s', cost: '$1.00-5.00' },
    { id: 'feature', name: '🎭 Feature', clips: '20-50', duration: '160-400s', cost: '$2.00-12.50' },
  ];

  const selectedStyle = movieStyles.find(style => style.id === watchedValues.style);
  const selectedPreset = moviePresets.find(preset => preset.id === watchedValues.preset);

  const onSubmit = async (data) => {
    try {
      setIsGeneratingScript(true);
      
      const projectData = {
        ...data,
        id: Date.now().toString(),
        createdAt: new Date().toISOString(),
        status: 'script-generation'
      };
      
      await generateScript(projectData);
      setCurrentStep('script');
      toast.success('Movie project created! Script generation started.');
      
    } catch (error) {
      console.error('Project creation error:', error);
      toast.error('Failed to create movie project');
      setIsGeneratingScript(false);
    }
  };

  const generateScript = async (project) => {
    try {
      const mockScript = generateMockScript(project);
      setGeneratedScript(mockScript.script);
      setScenes(mockScript.scenes);
    } finally {
      setIsGeneratingScript(false);
    }
  };

  const generateMockScript = (project) => {
    const sceneCount = Math.floor(Math.random() * (project.maxClips - 3)) + 3;
    const mockScenes = Array.from({ length: sceneCount }, (_, i) => ({
      id: i + 1,
      title: `Scene ${i + 1}`,
      description: `A compelling scene showing ${project.concept.slice(0, 50)}...`,
      duration: 8,
      prompt: `${selectedStyle?.description || 'Cinematic style'} scene showing ${project.concept}`,
      continuityFrame: i > 0 ? `frame_${i}.jpg` : null,
    }));

    const script = `# ${project.title}

## Synopsis
${project.concept}

## Style: ${selectedStyle?.name || 'Cinematic'}
${selectedStyle?.description || 'Professional cinematography'}

## Scenes

${mockScenes.map(scene => `
### ${scene.title}
**Duration**: ${scene.duration} seconds
**Description**: ${scene.description}
**Visual Prompt**: ${scene.prompt}
${scene.continuityFrame ? `**Continuity**: Starts from ${scene.continuityFrame}` : ''}
`).join('\n')}

## Production Notes
- Total scenes: ${sceneCount}
- Estimated duration: ${sceneCount * 8} seconds
- Style: ${project.style}
- Budget: $${project.budget}
`;

    return { script, scenes: mockScenes };
  };

  const startProduction = async () => {
    setCurrentStep('production');
    
    // Simulate production process
    for (let i = 0; i <= 100; i += 10) {
      await new Promise(resolve => setTimeout(resolve, 500));
      setProductionProgress(i);
    }
    
    toast.success('Movie production completed!');
  };

  const renderSetupStep = () => (
    <div className="max-w-4xl mx-auto space-y-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <div className="w-20 h-20 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center mx-auto mb-6">
          <FilmIcon className="w-10 h-10 text-white" />
        </div>
        <h1 className="text-3xl md:text-4xl font-bold text-white mb-4">
          Create Your Movie
        </h1>
        <p className="text-gray-400 max-w-2xl mx-auto">
          Transform your creative vision into a complete movie using AI. From script to screen in minutes.
        </p>
      </motion.div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
        {/* Project Details */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-white/10"
        >
          <h2 className="text-xl font-semibold text-white mb-4 flex items-center">
            <DocumentTextIcon className="w-6 h-6 mr-2" />
            Project Details
          </h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                Movie Title
              </label>
              <input
                {...register('title')}
                type="text"
                className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                placeholder="Enter your movie title..."
              />
              {errors.title && (
                <p className="text-red-400 text-sm mt-1">{errors.title.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-white mb-2">
                Movie Concept
              </label>
              <textarea
                {...register('concept')}
                rows={4}
                className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                placeholder="Describe your movie concept, plot, or idea..."
              />
              {errors.concept && (
                <p className="text-red-400 text-sm mt-1">{errors.concept.message}</p>
              )}
            </div>
          </div>
        </motion.div>

        {/* Style Selection */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-white/10"
        >
          <h2 className="text-xl font-semibold text-white mb-4 flex items-center">
            <SparklesIcon className="w-6 h-6 mr-2" />
            Visual Style
          </h2>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {movieStyles.map((style) => (
              <label
                key={style.id}
                className={`cursor-pointer p-4 rounded-lg border-2 transition-all duration-200 ${
                  watchedValues.style === style.id
                    ? 'border-purple-500 bg-purple-500/10'
                    : 'border-white/10 hover:border-white/20'
                }`}
              >
                <input
                  {...register('style')}
                  type="radio"
                  value={style.id}
                  className="sr-only"
                />
                <div className="text-lg font-medium text-white mb-1">{style.name}</div>
                <div className="text-sm text-gray-400">{style.description}</div>
              </label>
            ))}
          </div>
        </motion.div>

        {/* Movie Preset */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-white/10"
        >
          <h2 className="text-xl font-semibold text-white mb-4 flex items-center">
            <ClockIcon className="w-6 h-6 mr-2" />
            Movie Length
          </h2>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {moviePresets.map((preset) => (
              <label
                key={preset.id}
                className={`cursor-pointer p-4 rounded-lg border-2 transition-all duration-200 ${
                  watchedValues.preset === preset.id
                    ? 'border-purple-500 bg-purple-500/10'
                    : 'border-white/10 hover:border-white/20'
                }`}
              >
                <input
                  {...register('preset')}
                  type="radio"
                  value={preset.id}
                  className="sr-only"
                />
                <div className="text-lg font-medium text-white mb-1">{preset.name}</div>
                <div className="text-sm text-gray-400 space-y-1">
                  <div>Clips: {preset.clips}</div>
                  <div>Duration: {preset.duration}</div>
                  <div className="text-green-400">Cost: {preset.cost}</div>
                </div>
              </label>
            ))}
          </div>
        </motion.div>

        {/* Advanced Settings */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-white/10"
        >
          <h2 className="text-xl font-semibold text-white mb-4 flex items-center">
            <CogIcon className="w-6 h-6 mr-2" />
            Advanced Settings
          </h2>
          
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                Maximum Clips: {watchedValues.maxClips}
              </label>
              <input
                {...register('maxClips', { valueAsNumber: true })}
                type="range"
                min="3"
                max="50"
                className="w-full accent-purple-500"
              />
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>3</span>
                <span>50</span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-white mb-2">
                Budget Limit: ${watchedValues.budget}
              </label>
              <input
                {...register('budget', { valueAsNumber: true })}
                type="range"
                min="1"
                max="100"
                step="0.5"
                className="w-full accent-purple-500"
              />
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>$1</span>
                <span>$100</span>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Summary & Create */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-white/10"
        >
          <h2 className="text-xl font-semibold text-white mb-4 flex items-center">
            <CurrencyDollarIcon className="w-6 h-6 mr-2" />
            Project Summary
          </h2>
          
          <div className="grid md:grid-cols-3 gap-4 mb-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-white">{selectedStyle?.name || 'Style'}</div>
              <div className="text-gray-400 text-sm">Visual Style</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-white">{selectedPreset?.clips || '5-10'}</div>
              <div className="text-gray-400 text-sm">Clips</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-400">{selectedPreset?.cost || '$0.50-2.50'}</div>
              <div className="text-gray-400 text-sm">Estimated Cost</div>
            </div>
          </div>

          <motion.button
            type="submit"
            disabled={isGeneratingScript}
            whileHover={{ scale: isGeneratingScript ? 1 : 1.02 }}
            whileTap={{ scale: isGeneratingScript ? 1 : 0.98 }}
            className={`w-full py-4 px-6 rounded-xl font-semibold transition-all duration-300 ${
              isGeneratingScript
                ? 'bg-gray-600 cursor-not-allowed'
                : 'bg-gradient-to-r from-purple-500 to-pink-500 hover:shadow-lg hover:shadow-purple-500/25'
            } text-white`}
          >
            {isGeneratingScript ? (
              <div className="flex items-center justify-center">
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                Generating Script...
              </div>
            ) : (
              <div className="flex items-center justify-center">
                <FilmIcon className="w-5 h-5 mr-2" />
                Create Movie Project
              </div>
            )}
          </motion.button>
        </motion.div>
      </form>
    </div>
  );

  const renderScriptStep = () => (
    <div className="max-w-6xl mx-auto space-y-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <h1 className="text-3xl md:text-4xl font-bold text-white mb-4">
          Review Your Script
        </h1>
        <p className="text-gray-400 max-w-2xl mx-auto">
          Review and edit the generated script before starting production
        </p>
      </motion.div>

      <div className="grid lg:grid-cols-2 gap-8">
        {/* Script Editor */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-white/10"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-white">Script</h2>
            <button className="flex items-center space-x-2 px-3 py-1 bg-white/10 hover:bg-white/20 text-gray-400 hover:text-white rounded-lg transition-colors">
              <PencilIcon className="w-4 h-4" />
              <span className="text-sm">Edit</span>
            </button>
          </div>
          
          <textarea
            value={generatedScript}
            onChange={(e) => setGeneratedScript(e.target.value)}
            className="w-full h-96 px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 font-mono text-sm resize-none"
            placeholder="Generated script will appear here..."
          />
        </motion.div>

        {/* Scene Breakdown */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.4 }}
          className="space-y-4"
        >
          <h2 className="text-xl font-semibold text-white">Scene Breakdown</h2>
          
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {scenes.map((scene, index) => (
              <div
                key={scene.id}
                className="bg-white/5 backdrop-blur-sm rounded-lg p-4 border border-white/10"
              >
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold text-white">{scene.title}</h3>
                  <span className="text-xs text-gray-400">{scene.duration}s</span>
                </div>
                <p className="text-gray-300 text-sm mb-2">{scene.description}</p>
                <p className="text-gray-400 text-xs">{scene.prompt}</p>
                {scene.continuityFrame && (
                  <div className="mt-2 text-xs text-purple-400">
                    Continues from previous scene
                  </div>
                )}
              </div>
            ))}
          </div>

          <div className="bg-white/5 backdrop-blur-sm rounded-lg p-4 border border-white/10">
            <h3 className="font-semibold text-white mb-2">Production Summary</h3>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">Total Scenes:</span>
                <span className="text-white">{scenes.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Duration:</span>
                <span className="text-white">{scenes.length * 8}s</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Estimated Cost:</span>
                <span className="text-green-400">${(scenes.length * 0.25).toFixed(2)}</span>
              </div>
            </div>
          </div>

          <motion.button
            onClick={startProduction}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="w-full py-4 px-6 bg-gradient-to-r from-purple-500 to-pink-500 text-white font-semibold rounded-xl hover:shadow-lg hover:shadow-purple-500/25 transition-all duration-300"
          >
            <div className="flex items-center justify-center">
              <PlayIcon className="w-5 h-5 mr-2" />
              Start Production
            </div>
          </motion.button>
        </motion.div>
      </div>
    </div>
  );

  const renderProductionStep = () => (
    <div className="max-w-4xl mx-auto space-y-8 text-center">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <div className="w-20 h-20 bg-gradient-to-br from-green-500 to-blue-500 rounded-full flex items-center justify-center mx-auto mb-6">
          <FilmIcon className="w-10 h-10 text-white" />
        </div>
        <h1 className="text-3xl md:text-4xl font-bold text-white mb-4">
          Producing Your Movie
        </h1>
        <p className="text-gray-400 max-w-2xl mx-auto">
          AI is generating your movie scenes with frame-to-frame continuity
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.2 }}
        className="bg-white/5 backdrop-blur-sm rounded-xl p-8 border border-white/10"
      >
        <div className="mb-6">
          <div className="flex items-center justify-between text-sm text-gray-400 mb-2">
            <span>Progress</span>
            <span>{productionProgress}%</span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-4 overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${productionProgress}%` }}
              transition={{ duration: 0.5, ease: 'easeOut' }}
              className="h-full bg-gradient-to-r from-green-500 to-blue-500 rounded-full relative"
            >
              <div className="absolute inset-0 bg-white/20 animate-pulse rounded-full"></div>
            </motion.div>
          </div>
        </div>

        <div className="space-y-4">
          {scenes.map((scene, index) => (
            <div
              key={scene.id}
              className={`flex items-center justify-between p-4 rounded-lg transition-all duration-300 ${
                index < (productionProgress / 100) * scenes.length
                  ? 'bg-green-500/10 border border-green-500/20'
                  : 'bg-white/5 border border-white/10'
              }`}
            >
              <div className="flex items-center space-x-3">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  index < (productionProgress / 100) * scenes.length
                    ? 'bg-green-500'
                    : 'bg-gray-600'
                }`}>
                  {index < (productionProgress / 100) * scenes.length ? (
                    <CheckIcon className="w-5 h-5 text-white" />
                  ) : (
                    <span className="text-white text-sm">{index + 1}</span>
                  )}
                </div>
                <span className="text-white font-medium">{scene.title}</span>
              </div>
              <span className="text-gray-400 text-sm">{scene.duration}s</span>
            </div>
          ))}
        </div>

        {productionProgress === 100 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-8"
          >
            <div className="text-green-400 text-lg font-semibold mb-4">
              🎉 Movie Production Complete!
            </div>
            <button className="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white font-semibold rounded-lg hover:shadow-lg transition-all duration-300">
              Download Movie
            </button>
          </motion.div>
        )}
      </motion.div>
    </div>
  );

  return (
    <div className="space-y-8">
      {/* Step Indicator */}
      <div className="flex items-center justify-center space-x-4 mb-8">
        {['setup', 'script', 'production'].map((step, index) => (
          <div
            key={step}
            className={`flex items-center space-x-2 ${
              currentStep === step ? 'text-purple-400' : 'text-gray-500'
            }`}
          >
            <div className={`w-8 h-8 rounded-full flex items-center justify-center border-2 ${
              currentStep === step
                ? 'border-purple-400 bg-purple-400/20'
                : 'border-gray-600'
            }`}>
              {index + 1}
            </div>
            <span className="font-medium capitalize">{step}</span>
            {index < 2 && (
              <div className="w-8 h-px bg-gray-600 ml-2"></div>
            )}
          </div>
        ))}
      </div>

      {/* Step Content */}
      {currentStep === 'setup' && renderSetupStep()}
      {currentStep === 'script' && renderScriptStep()}
      {currentStep === 'production' && renderProductionStep()}
    </div>
  );
};

export default MovieMakerPage;
