import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  MusicalNoteIcon, 
  PlayIcon, 
 
  SparklesIcon,
  ArrowDownTrayIcon,
  ClockIcon,
  SpeakerWaveIcon
} from '@heroicons/react/24/outline';
import { musicService } from '../services/musicService';

const MusicPage = () => {
  const [prompt, setPrompt] = useState('');
  const [style, setStyle] = useState('pop');
  const [mood, setMood] = useState('happy');
  const [duration, setDuration] = useState(30);
  const [tempo, setTempo] = useState(120);
  const [musicalKey, setMusicalKey] = useState('C major');
  const [vocals, setVocals] = useState('none');
  const [isGenerating, setIsGenerating] = useState(false);

  const musicStyles = [
    { id: 'pop', name: 'Pop', description: 'Modern popular music' },
    { id: 'rock', name: 'Rock', description: 'Classic rock style' },
    { id: 'electronic', name: 'Electronic', description: 'Synthesized electronic music' },
    { id: 'classical', name: 'Classical', description: 'Orchestral classical music' },
    { id: 'jazz', name: 'Jazz', description: 'Smooth jazz rhythms' },
    { id: 'ambient', name: 'Ambient', description: 'Atmospheric background music' },
    { id: 'cinematic', name: 'Cinematic', description: 'Epic movie soundtrack style' },
    { id: 'folk', name: 'Folk', description: 'Acoustic folk music' },
    { id: 'blues', name: 'Blues', description: 'Traditional blues style' },
    { id: 'country', name: 'Country', description: 'Country music style' },
    { id: 'hip_hop', name: 'Hip Hop', description: 'Modern hip hop beats' },
    { id: 'reggae', name: 'Reggae', description: 'Laid-back reggae rhythms' },
  ];

  const musicMoods = [
    { id: 'happy', name: 'Happy', description: 'Upbeat and cheerful' },
    { id: 'sad', name: 'Sad', description: 'Melancholic and emotional' },
    { id: 'energetic', name: 'Energetic', description: 'High energy and dynamic' },
    { id: 'calm', name: 'Calm', description: 'Peaceful and relaxing' },
    { id: 'mysterious', name: 'Mysterious', description: 'Dark and intriguing' },
    { id: 'romantic', name: 'Romantic', description: 'Love and passion' },
    { id: 'epic', name: 'Epic', description: 'Grand and powerful' },
    { id: 'nostalgic', name: 'Nostalgic', description: 'Wistful and reminiscent' },
  ];

  const vocalStyles = [
    { id: 'none', name: 'Instrumental', description: 'No vocals' },
    { id: 'male', name: 'Male Vocals', description: 'Male singer' },
    { id: 'female', name: 'Female Vocals', description: 'Female singer' },
    { id: 'choir', name: 'Choir', description: 'Multiple voices' },
    { id: 'humming', name: 'Humming', description: 'Wordless humming' },
  ];

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      alert('Please enter a description for your music');
      return;
    }

    setIsGenerating(true);
    
    try {
      const musicData = {
        prompt: prompt.trim(),
        style,
        mood,
        duration,
        tempo,
        musical_key: musicalKey,
        vocal_style: vocals
      };

      const response = await musicService.generateMusic(musicData);
      
      console.log('Music generation started:', response);
      alert(`Music generation started! Job ID: ${response.job_id}. Check the Gallery tab to hear your music when it's ready.`);
      
      // Optionally redirect to Gallery or Jobs tab
      // window.location.href = '/gallery';
      
    } catch (error) {
      console.error('Music generation failed:', error);
      alert('Music generation failed. Please try again.');
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
            <MusicalNoteIcon className="w-12 h-12 text-purple-400 mr-4" />
            <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
              AI Music Generation
            </h1>
          </div>
          <p className="text-xl text-gray-300 max-w-2xl mx-auto">
            Create original music compositions using Google's Lyria AI
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
                Describe Your Music
              </label>
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="A gentle piano melody with soft strings, perfect for a romantic evening, building to an emotional crescendo..."
                className="w-full h-32 bg-gray-700/50 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
                maxLength={500}
              />
              <div className="flex justify-between items-center mt-2">
                <span className="text-sm text-gray-400">
                  {prompt.length}/500 characters
                </span>
                <span className="text-sm text-purple-400">
                  Describe mood, instruments, and style
                </span>
              </div>
            </div>

            {/* Style and Mood */}
            <div className="grid md:grid-cols-2 gap-6">
              {/* Music Style */}
              <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10">
                <label className="block text-lg font-semibold mb-3">
                  Music Style
                </label>
                <select
                  value={style}
                  onChange={(e) => setStyle(e.target.value)}
                  className="w-full bg-gray-700/50 border border-gray-600 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                >
                  {musicStyles.map((styleOption) => (
                    <option key={styleOption.id} value={styleOption.id}>
                      {styleOption.name} - {styleOption.description}
                    </option>
                  ))}
                </select>
              </div>

              {/* Music Mood */}
              <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10">
                <label className="block text-lg font-semibold mb-3">
                  Music Mood
                </label>
                <select
                  value={mood}
                  onChange={(e) => setMood(e.target.value)}
                  className="w-full bg-gray-700/50 border border-gray-600 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                >
                  {musicMoods.map((moodOption) => (
                    <option key={moodOption.id} value={moodOption.id}>
                      {moodOption.name} - {moodOption.description}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Duration and Tempo */}
            <div className="grid md:grid-cols-2 gap-6">
              {/* Duration */}
              <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10">
                <label className="block text-lg font-semibold mb-3">
                  Duration: {duration} seconds
                </label>
                <input
                  type="range"
                  min="10"
                  max="300"
                  value={duration}
                  onChange={(e) => setDuration(parseInt(e.target.value))}
                  className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
                />
                <div className="flex justify-between text-sm text-gray-400 mt-2">
                  <span>10s</span>
                  <span>5 min</span>
                </div>
              </div>

              {/* Tempo */}
              <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10">
                <label className="block text-lg font-semibold mb-3">
                  Tempo: {tempo} BPM
                </label>
                <input
                  type="range"
                  min="60"
                  max="200"
                  value={tempo}
                  onChange={(e) => setTempo(parseInt(e.target.value))}
                  className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
                />
                <div className="flex justify-between text-sm text-gray-400 mt-2">
                  <span>Slow</span>
                  <span>Fast</span>
                </div>
              </div>
            </div>

            {/* Musical Key and Vocals */}
            <div className="grid md:grid-cols-2 gap-6">
              {/* Musical Key */}
              <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10">
                <label className="block text-lg font-semibold mb-3">
                  Musical Key
                </label>
                <select
                  value={musicalKey}
                  onChange={(e) => setMusicalKey(e.target.value)}
                  className="w-full bg-gray-700/50 border border-gray-600 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                >
                  <option value="C major">C Major</option>
                  <option value="G major">G Major</option>
                  <option value="D major">D Major</option>
                  <option value="A major">A Major</option>
                  <option value="E major">E Major</option>
                  <option value="F major">F Major</option>
                  <option value="A minor">A Minor</option>
                  <option value="E minor">E Minor</option>
                  <option value="B minor">B Minor</option>
                  <option value="D minor">D Minor</option>
                  <option value="G minor">G Minor</option>
                </select>
              </div>

              {/* Vocal Style */}
              <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10">
                <label className="block text-lg font-semibold mb-3">
                  Vocal Style
                </label>
                <select
                  value={vocals}
                  onChange={(e) => setVocals(e.target.value)}
                  className="w-full bg-gray-700/50 border border-gray-600 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                >
                  {vocalStyles.map((vocal) => (
                    <option key={vocal.id} value={vocal.id}>
                      {vocal.name} - {vocal.description}
                    </option>
                  ))}
                </select>
              </div>
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
                  <span>Generating Music...</span>
                </>
              ) : (
                <>
                  <SparklesIcon className="w-6 h-6" />
                  <span>Generate Music</span>
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
            {/* Music Player Preview */}
            <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10">
              <h3 className="text-lg font-semibold mb-4">Music Preview</h3>
              <div className="aspect-video bg-gray-700/30 rounded-lg border-2 border-dashed border-gray-600 flex items-center justify-center">
                <div className="text-center">
                  <SpeakerWaveIcon className="w-16 h-16 text-gray-500 mx-auto mb-4" />
                  <p className="text-gray-400">Your generated music will play here</p>
                  <div className="flex items-center justify-center space-x-4 mt-4">
                    <button className="p-2 bg-gray-600 rounded-full hover:bg-gray-500 transition-colors">
                      <PlayIcon className="w-6 h-6" />
                    </button>
                    <button className="p-2 bg-gray-600 rounded-full hover:bg-gray-500 transition-colors">
                      <ArrowDownTrayIcon className="w-6 h-6" />
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Music Composition Details */}
            <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10">
              <h3 className="text-lg font-semibold mb-4">Composition Details</h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Style:</span>
                  <span className="text-white">{musicStyles.find(s => s.id === style)?.name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Mood:</span>
                  <span className="text-white">{musicMoods.find(m => m.id === mood)?.name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Duration:</span>
                  <span className="text-white">{duration}s</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Tempo:</span>
                  <span className="text-white">{tempo} BPM</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Key:</span>
                  <span className="text-white">{musicalKey}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Vocals:</span>
                  <span className="text-white">{vocalStyles.find(v => v.id === vocals)?.name}</span>
                </div>
              </div>
            </div>

            {/* Tips & Guidelines */}
            <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10">
              <h3 className="text-lg font-semibold mb-4">🎵 Composition Tips</h3>
              <div className="space-y-3 text-sm text-gray-300">
                <div className="flex items-start space-x-2">
                  <span className="text-purple-400">•</span>
                  <span>Describe the emotional journey you want the music to take</span>
                </div>
                <div className="flex items-start space-x-2">
                  <span className="text-purple-400">•</span>
                  <span>Mention specific instruments for richer compositions</span>
                </div>
                <div className="flex items-start space-x-2">
                  <span className="text-purple-400">•</span>
                  <span>Include dynamics like "building", "soft", "explosive"</span>
                </div>
                <div className="flex items-start space-x-2">
                  <span className="text-purple-400">•</span>
                  <span>Reference musical terms like "staccato", "legato", "crescendo"</span>
                </div>
              </div>
            </div>

            {/* Recent Music */}
            <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10">
              <h3 className="text-lg font-semibold mb-4">Recent Compositions</h3>
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="flex items-center space-x-3 p-3 bg-gray-700/30 rounded-lg">
                    <div className="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center">
                      <MusicalNoteIcon className="w-5 h-5 text-purple-400" />
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium">Composition {i}</p>
                      <p className="text-xs text-gray-400">Pop • Happy • 30s</p>
                    </div>
                    <button className="p-1 hover:bg-gray-600 rounded">
                      <PlayIcon className="w-4 h-4" />
                    </button>
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

export default MusicPage;