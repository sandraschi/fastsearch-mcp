import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  PhotoIcon,
  PlayIcon,
  HeartIcon,
  ShareIcon,
  FunnelIcon,
  ArrowDownTrayIcon,
  MusicalNoteIcon,
  FilmIcon,
  CameraIcon,
  SpeakerWaveIcon,
} from '@heroicons/react/24/outline';
import { imageService } from '../services/imageService';
import { musicService } from '../services/musicService';

const GalleryPage = () => {
  const [selectedFilter, setSelectedFilter] = useState('all');
  const [contentType, setContentType] = useState('all'); // all, videos, images, music
  const [videos, setVideos] = useState([]);
  const [images, setImages] = useState([]);
  const [music, setMusic] = useState([]);
  const [loading, setLoading] = useState(true);

  // Load content from APIs
  useEffect(() => {
    loadContent();
  }, []);

  const loadContent = async () => {
    setLoading(true);
    try {
      // Load images
      const imageList = await imageService.listImageGenerations({ limit: 50 });
      setImages(imageList || []);

      // Load music
      const musicList = await musicService.listMusicGenerations({ limit: 50 });
      setMusic(musicList || []);

      // Mock videos data (replace with actual video service when ready)
      setVideos([
        {
          id: 'video-1',
          title: 'Sunset Mountain Vista',
          thumbnail: '/api/placeholder/400/300',
          duration: '5s',
          style: 'cinematic',
          type: 'video',
          aspectRatio: '16:9',
          createdAt: '2024-01-15',
          likes: 24,
        },
        {
          id: 'video-2',
          title: 'Urban Night Scene',
          thumbnail: '/api/placeholder/400/300',
          duration: '8s',
          style: 'realistic',
          type: 'video',
          aspectRatio: '16:9',
          createdAt: '2024-01-14',
          likes: 18,
        }
      ]);

    } catch (error) {
      console.error('Failed to load content:', error);
    } finally {
      setLoading(false);
    }
  };

  // Get filtered content based on type and filter
  const getFilteredContent = () => {
    let allContent = [];
    
    if (contentType === 'all' || contentType === 'videos') {
      allContent = [...allContent, ...videos.map(v => ({ ...v, type: 'video' }))];
    }
    
    if (contentType === 'all' || contentType === 'images') {
      allContent = [...allContent, ...images.map(i => ({ 
        ...i, 
        type: 'image',
        title: i.prompt?.substring(0, 50) + '...' || 'Generated Image',
        thumbnail: i.thumbnail_url || i.image_url,
        style: i.style,
        createdAt: i.created_at,
        likes: 0,
        duration: null
      }))];
    }
    
    if (contentType === 'all' || contentType === 'music') {
      allContent = [...allContent, ...music.map(m => ({ 
        ...m, 
        type: 'music',
        title: m.prompt?.substring(0, 50) + '...' || 'Generated Music',
        thumbnail: '/api/placeholder/400/300', // Music waveform placeholder
        style: m.style,
        duration: `${m.duration}s`,
        createdAt: m.created_at,
        likes: 0
      }))];
    }

    // Apply style filter
    if (selectedFilter !== 'all') {
      allContent = allContent.filter(item => item.style === selectedFilter);
    }

    // Sort by creation date (newest first)
    return allContent.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
  };

  const filteredContent = getFilteredContent();

  const contentTypeFilters = [
    { id: 'all', name: 'All Content', icon: PhotoIcon, count: videos.length + images.length + music.length },
    { id: 'videos', name: 'Videos', icon: FilmIcon, count: videos.length },
    { id: 'images', name: 'Images', icon: CameraIcon, count: images.length },
    { id: 'music', name: 'Music', icon: MusicalNoteIcon, count: music.length },
  ];

  const styleFilters = [
    { id: 'all', name: 'All Styles' },
    { id: 'cinematic', name: 'Cinematic' },
    { id: 'realistic', name: 'Realistic' },
    { id: 'artistic', name: 'Artistic' },
    { id: 'photorealistic', name: 'Photorealistic' },
    { id: 'pop', name: 'Pop' },
    { id: 'rock', name: 'Rock' },
    { id: 'electronic', name: 'Electronic' },
  ];

  const getContentIcon = (type) => {
    switch (type) {
      case 'video': return FilmIcon;
      case 'image': return CameraIcon;
      case 'music': return MusicalNoteIcon;
      default: return PhotoIcon;
    }
  };

  const getContentTypeColor = (type) => {
    switch (type) {
      case 'video': return 'text-blue-400';
      case 'image': return 'text-green-400';
      case 'music': return 'text-purple-400';
      default: return 'text-gray-400';
    }
  };

  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <h1 className="text-3xl md:text-4xl font-bold text-white mb-4">
          Media Gallery
        </h1>
        <p className="text-gray-400">
          Explore your AI-generated videos, images, and music
        </p>
      </motion.div>

      {/* Content Type Filters */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="flex items-center justify-center"
      >
        <div className="flex items-center space-x-1 bg-white/5 backdrop-blur-sm rounded-lg p-1 border border-white/10">
          {contentTypeFilters.map((filter) => {
            const IconComponent = filter.icon;
            return (
              <button
                key={filter.id}
                onClick={() => setContentType(filter.id)}
                className={`flex items-center px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                  contentType === filter.id
                    ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white'
                    : 'text-gray-400 hover:text-white hover:bg-white/10'
                }`}
              >
                <IconComponent className="w-4 h-4 mr-2" />
                {filter.name}
                <span className="ml-2 text-xs opacity-60">({filter.count})</span>
              </button>
            );
          })}
        </div>
      </motion.div>

      {/* Style Filters */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="flex items-center justify-between"
      >
        <div className="flex items-center space-x-1 bg-white/5 backdrop-blur-sm rounded-lg p-1 border border-white/10">
          {styleFilters.slice(0, 6).map((filter) => (
            <button
              key={filter.id}
              onClick={() => setSelectedFilter(filter.id)}
              className={`px-3 py-1 rounded-md text-sm font-medium transition-all duration-200 ${
                selectedFilter === filter.id
                  ? 'bg-white/20 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-white/10'
              }`}
            >
              {filter.name}
            </button>
          ))}
        </div>

        <div className="flex items-center space-x-2">
          <button className="flex items-center px-4 py-2 bg-white/5 backdrop-blur-sm border border-white/10 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-colors">
            <FunnelIcon className="w-4 h-4 mr-2" />
            More Filters
          </button>
        </div>
      </motion.div>

      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading your content...</p>
        </div>
      ) : (
        <>
          {/* Content Grid */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
          >
            {filteredContent.map((item, index) => {
              const IconComponent = getContentIcon(item.type);
              return (
                <motion.div
                  key={`${item.type}-${item.id}`}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="group cursor-pointer"
                  onClick={() => {}}
                >
                  <div className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 overflow-hidden hover:border-white/20 transition-all duration-300 group-hover:scale-105">
                    {/* Thumbnail */}
                    <div className="relative aspect-video bg-gray-800">
                      {item.thumbnail && (
                        <img 
                          src={item.thumbnail} 
                          alt={item.title}
                          className="w-full h-full object-cover"
                        />
                      )}
                      <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
                      
                      {/* Play/View Button */}
                      <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                        <div className="w-12 h-12 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center">
                          {item.type === 'video' && <PlayIcon className="w-6 h-6 text-white" />}
                          {item.type === 'image' && <PhotoIcon className="w-6 h-6 text-white" />}
                          {item.type === 'music' && <SpeakerWaveIcon className="w-6 h-6 text-white" />}
                        </div>
                      </div>

                      {/* Type Badge */}
                      <div className="absolute top-3 left-3 flex items-center bg-black/50 backdrop-blur-sm px-2 py-1 rounded text-white text-xs">
                        <IconComponent className={`w-3 h-3 mr-1 ${getContentTypeColor(item.type)}`} />
                        {item.type}
                      </div>
                      
                      {/* Duration Badge */}
                      {item.duration && (
                        <div className="absolute top-3 right-3 bg-black/50 backdrop-blur-sm px-2 py-1 rounded text-white text-xs">
                          {item.duration}
                        </div>
                      )}

                      {/* Title */}
                      <div className="absolute bottom-3 left-3 right-3 text-white">
                        <p className="font-medium text-sm truncate">{item.title}</p>
                      </div>
                    </div>

                    {/* Info */}
                    <div className="p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs text-gray-400 capitalize">
                          {item.style} {item.aspectRatio && `• ${item.aspectRatio}`}
                        </span>
                        <span className="text-xs text-gray-400">
                          {new Date(item.createdAt).toLocaleDateString()}
                        </span>
                      </div>

                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <button className="flex items-center text-gray-400 hover:text-red-400 transition-colors">
                            <HeartIcon className="w-4 h-4 mr-1" />
                            <span className="text-xs">{item.likes}</span>
                          </button>
                          <button className="text-gray-400 hover:text-white transition-colors">
                            <ShareIcon className="w-4 h-4" />
                          </button>
                        </div>
                        <button className="text-gray-400 hover:text-white transition-colors">
                          <ArrowDownTrayIcon className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </motion.div>

          {filteredContent.length === 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center py-12"
            >
              <PhotoIcon className="w-16 h-16 text-gray-600 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-white mb-2">No content found</h3>
              <p className="text-gray-400 mb-6">
                Try adjusting your filters or create your first {contentType === 'all' ? 'content' : contentType}
              </p>
              <div className="flex items-center justify-center space-x-4">
                <a
                  href="/generate"
                  className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-blue-500 to-blue-600 text-white font-semibold rounded-lg hover:shadow-lg transition-all duration-300"
                >
                  <FilmIcon className="w-5 h-5 mr-2" />
                  Create Video
                </a>
                <a
                  href="/images"
                  className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-green-500 to-green-600 text-white font-semibold rounded-lg hover:shadow-lg transition-all duration-300"
                >
                  <CameraIcon className="w-5 h-5 mr-2" />
                  Create Image
                </a>
                <a
                  href="/music"
                  className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-purple-500 to-purple-600 text-white font-semibold rounded-lg hover:shadow-lg transition-all duration-300"
                >
                  <MusicalNoteIcon className="w-5 h-5 mr-2" />
                  Create Music
                </a>
              </div>
            </motion.div>
          )}
        </>
      )}
    </div>
  );
};

export default GalleryPage;