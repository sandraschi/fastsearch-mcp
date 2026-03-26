import React from 'react';
import ReactPlayer from 'react-player';
import { motion } from 'framer-motion';

const VideoPreview = ({ src, thumbnail, title, className = '' }) => {
  if (!src) {
    return (
      <div className={`aspect-video bg-gray-800 rounded-lg flex items-center justify-center ${className}`}>
        <div className="text-center">
          <div className="w-16 h-16 bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-gray-500" fill="currentColor" viewBox="0 0 24 24">
              <path d="M8 5v14l11-7z"/>
            </svg>
          </div>
          <p className="text-gray-400">No video to preview</p>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`relative aspect-video rounded-lg overflow-hidden bg-black ${className}`}
    >
      <ReactPlayer
        url={src}
        width="100%"
        height="100%"
        controls
        light={thumbnail}
        playing={false}
        config={{
          file: {
            attributes: {
              controlsList: 'nodownload',
            }
          }
        }}
      />
      {title && (
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4">
          <h3 className="text-white font-medium">{title}</h3>
        </div>
      )}
    </motion.div>
  );
};

export default VideoPreview;
