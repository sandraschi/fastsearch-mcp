import React from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  SparklesIcon,
  PlayIcon,
  CameraIcon,
  FilmIcon,
  ChartBarIcon,
  UserGroupIcon,
  DocumentTextIcon,
  LightBulbIcon,
  ClockIcon,
  CurrencyDollarIcon,
  StarIcon,
  BoltIcon,
} from '@heroicons/react/24/outline';

const HomePage = () => {
  const features = [
    {
      name: 'AI Video Generation',
      description: 'Create stunning videos from text descriptions using Google Veo',
      icon: SparklesIcon,
      color: 'from-purple-500 to-pink-500',
    },
    {
      name: 'Movie Maker',
      description: 'Generate complete movies with multiple scenes and continuity',
      icon: FilmIcon,
      color: 'from-blue-500 to-cyan-500',
    },
    {
      name: 'Multiple Styles',
      description: 'Choose from cinematic, anime, Pixar, Wes Anderson, and more',
      icon: CameraIcon,
      color: 'from-green-500 to-teal-500',
    },
    {
      name: 'Real-time Progress',
      description: 'Track your video generation progress in real-time',
      icon: ChartBarIcon,
      color: 'from-orange-500 to-red-500',
    },
  ];

  const movieMakerFeatures = [
    {
      icon: DocumentTextIcon,
      title: 'AI Script Generation',
      description: 'Transform simple ideas into detailed movie scripts'
    },
    {
      icon: LightBulbIcon,
      title: 'Scene Continuity',
      description: 'Frame-to-frame continuity for seamless movie flow'
    },
    {
      icon: ClockIcon,
      title: 'Quick Production',
      description: 'Complete movies in minutes, not months'
    },
    {
      icon: CurrencyDollarIcon,
      title: 'Cost Control',
      description: 'Built-in budget limits and cost estimation'
    },
  ];

  const movieStyles = [
    { name: 'Anime', emoji: '🎨', description: 'Japanese animation style' },
    { name: 'Pixar', emoji: '🎭', description: '3D animated movies' },
    { name: 'Wes Anderson', emoji: '🎪', description: 'Quirky cinematography' },
    { name: 'Claymation', emoji: '🏺', description: 'Stop-motion clay animation' },
    { name: 'Švankmajer', emoji: '🎪', description: 'Surreal stop-motion' },
    { name: 'Advertisement', emoji: '📺', description: 'Commercial style' },
    { name: 'Music Video', emoji: '🎵', description: 'Dynamic visuals' },
    { name: 'Cinematic', emoji: '🎬', description: 'Hollywood blockbuster' },
  ];

  const stats = [
    { name: 'Videos Generated', value: '50,000+' },
    { name: 'Movies Created', value: '5,000+' },
    { name: 'Hours Saved', value: '100,000+' },
    { name: 'Styles Available', value: '9+' },
  ];

  return (
    <div className="space-y-16">
      {/* Hero Section */}
      <motion.section
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="text-center py-12"
      >
        <motion.div
          initial={{ scale: 0.5, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.2, duration: 0.6 }}
          className="mb-8"
        >
          <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full mb-6">
            <SparklesIcon className="w-10 h-10 text-white" />
          </div>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.6 }}
          className="text-4xl md:text-6xl font-bold text-white mb-6"
        >
          Create Amazing Videos & Movies with{' '}
          <span className="bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
            AI Magic
          </span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.6 }}
          className="text-xl text-gray-300 mb-8 max-w-3xl mx-auto"
        >
          From single videos to complete movies - transform your ideas into stunning visual content using Google's cutting-edge Veo AI model. 
          Professional quality in minutes, not months.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, duration: 0.6 }}
          className="flex flex-col sm:flex-row gap-4 justify-center"
        >
          <Link
            to="/generate"
            className="inline-flex items-center px-8 py-4 bg-gradient-to-r from-purple-500 to-pink-500 text-white font-semibold rounded-xl hover:shadow-lg hover:shadow-purple-500/25 transition-all duration-300 transform hover:scale-105"
          >
            <PlayIcon className="w-5 h-5 mr-2" />
            Create Video
          </Link>
          <Link
            to="/moviemaker"
            className="inline-flex items-center px-8 py-4 bg-gradient-to-r from-blue-500 to-cyan-500 text-white font-semibold rounded-xl hover:shadow-lg hover:shadow-blue-500/25 transition-all duration-300 transform hover:scale-105"
          >
            <FilmIcon className="w-5 h-5 mr-2" />
            Make a Movie
          </Link>
        </motion.div>
      </motion.section>

      {/* Movie Maker Spotlight */}
      <motion.section
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6, duration: 0.6 }}
        className="py-16 bg-gradient-to-r from-blue-500/10 to-purple-500/10 backdrop-blur-sm rounded-2xl border border-white/10"
      >
        <div className="text-center mb-12">
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.7, duration: 0.6 }}
            className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-full mb-6"
          >
            <FilmIcon className="w-8 h-8 text-white" />
          </motion.div>
          
          <h2 className="text-4xl font-bold text-white mb-4">
            Introducing{' '}
            <span className="bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
              Movie Maker
            </span>
          </h2>
          <p className="text-xl text-gray-300 max-w-3xl mx-auto mb-8">
            The world's first AI-powered movie creation platform with frame-to-frame continuity. 
            Turn your ideas into complete movies with multiple scenes and seamless transitions.
          </p>

          <div className="flex items-center justify-center space-x-2 mb-8">
            <StarIcon className="w-5 h-5 text-yellow-400 fill-current" />
            <StarIcon className="w-5 h-5 text-yellow-400 fill-current" />
            <StarIcon className="w-5 h-5 text-yellow-400 fill-current" />
            <StarIcon className="w-5 h-5 text-yellow-400 fill-current" />
            <StarIcon className="w-5 h-5 text-yellow-400 fill-current" />
            <span className="text-white font-semibold ml-2">Revolutionary Technology</span>
          </div>
        </div>

        {/* Movie Maker Features */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          {movieMakerFeatures.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.8 + index * 0.1, duration: 0.6 }}
              className="text-center"
            >
              <div className="inline-flex items-center justify-center w-12 h-12 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-lg mb-4">
                <feature.icon className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">{feature.title}</h3>
              <p className="text-gray-400">{feature.description}</p>
            </motion.div>
          ))}
        </div>

        {/* Movie Styles Showcase */}
        <div className="mb-12">
          <h3 className="text-2xl font-bold text-white text-center mb-8">
            Choose Your Movie Style
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4">
            {movieStyles.map((style, index) => (
              <motion.div
                key={style.name}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 1.0 + index * 0.05, duration: 0.4 }}
                className="text-center p-4 bg-white/5 backdrop-blur-sm rounded-lg border border-white/10 hover:border-white/20 transition-all duration-300 group"
              >
                <div className="text-3xl mb-2 group-hover:scale-110 transition-transform duration-300">
                  {style.emoji}
                </div>
                <div className="text-white font-medium text-sm">{style.name}</div>
                <div className="text-gray-400 text-xs">{style.description}</div>
              </motion.div>
            ))}
          </div>
        </div>

        <div className="text-center">
          <Link
            to="/moviemaker"
            className="inline-flex items-center px-8 py-4 bg-gradient-to-r from-blue-500 to-cyan-500 text-white font-semibold rounded-xl hover:shadow-lg hover:shadow-blue-500/25 transition-all duration-300 transform hover:scale-105"
          >
            <BoltIcon className="w-5 h-5 mr-2" />
            Start Making Movies
          </Link>
        </div>
      </motion.section>

      {/* Stats Section */}
      <motion.section
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1.2, duration: 0.6 }}
        className="py-8"
      >
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {stats.map((stat, index) => (
            <motion.div
              key={stat.name}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1.3 + index * 0.1, duration: 0.6 }}
              className="text-center"
            >
              <div className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-white/10">
                <div className="text-3xl font-bold text-white mb-2">{stat.value}</div>
                <div className="text-gray-400">{stat.name}</div>
              </div>
            </motion.div>
          ))}
        </div>
      </motion.section>

      {/* Features Section */}
      <motion.section
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1.4, duration: 0.6 }}
        className="py-12"
      >
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-white mb-4">
            Powerful Features
          </h2>
          <p className="text-gray-400 max-w-2xl mx-auto">
            Everything you need to create professional videos and movies with AI
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature, index) => (
            <motion.div
              key={feature.name}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1.5 + index * 0.1, duration: 0.6 }}
              className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-white/10 hover:border-white/20 transition-all duration-300 group"
            >
              <div className={`inline-flex items-center justify-center w-12 h-12 bg-gradient-to-br ${feature.color} rounded-lg mb-4 group-hover:scale-110 transition-transform duration-300`}>
                <feature.icon className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">
                {feature.name}
              </h3>
              <p className="text-gray-400">
                {feature.description}
              </p>
            </motion.div>
          ))}
        </div>
      </motion.section>

      {/* Use Cases Section */}
      <motion.section
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1.8, duration: 0.6 }}
        className="py-12"
      >
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-white mb-4">
            Perfect For Every Creator
          </h2>
          <p className="text-gray-400 max-w-2xl mx-auto">
            From content creators to filmmakers, VeoGen empowers everyone to create amazing visual content
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          <div className="text-center">
            <div className="w-16 h-16 bg-gradient-to-br from-pink-500 to-rose-500 rounded-full flex items-center justify-center mx-auto mb-4">
              <UserGroupIcon className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-xl font-semibold text-white mb-3">Content Creators</h3>
            <p className="text-gray-400">
              Create engaging social media content, YouTube videos, and viral clips in minutes
            </p>
          </div>

          <div className="text-center">
            <div className="w-16 h-16 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-full flex items-center justify-center mx-auto mb-4">
              <CameraIcon className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-xl font-semibold text-white mb-3">Businesses</h3>
            <p className="text-gray-400">
              Professional marketing videos, product demos, and advertisements without expensive production
            </p>
          </div>

          <div className="text-center">
            <div className="w-16 h-16 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-full flex items-center justify-center mx-auto mb-4">
              <FilmIcon className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-xl font-semibold text-white mb-3">Filmmakers</h3>
            <p className="text-gray-400">
              Rapid prototyping, concept visualization, and complete indie film production
            </p>
          </div>
        </div>
      </motion.section>

      {/* CTA Section */}
      <motion.section
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 2.0, duration: 0.6 }}
        className="text-center py-12"
      >
        <div className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 backdrop-blur-sm rounded-2xl p-8 border border-white/10">
          <h3 className="text-3xl font-bold text-white mb-4">
            Ready to Create Your Masterpiece?
          </h3>
          <p className="text-gray-300 mb-8 max-w-2xl mx-auto">
            Join thousands of creators who are already using VeoGen to bring their ideas to life. 
            Start with a single video or create your first movie today.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/generate"
              className="inline-flex items-center px-8 py-4 bg-gradient-to-r from-purple-500 to-pink-500 text-white font-semibold rounded-xl hover:shadow-lg hover:shadow-purple-500/25 transition-all duration-300 transform hover:scale-105"
            >
              <SparklesIcon className="w-5 h-5 mr-2" />
              Start Creating Videos
            </Link>
            <Link
              to="/moviemaker"
              className="inline-flex items-center px-8 py-4 bg-gradient-to-r from-blue-500 to-cyan-500 text-white font-semibold rounded-xl hover:shadow-lg hover:shadow-blue-500/25 transition-all duration-300 transform hover:scale-105"
            >
              <FilmIcon className="w-5 h-5 mr-2" />
              Make Your First Movie
            </Link>
          </div>
        </div>
      </motion.section>
    </div>
  );
};

export default HomePage;
