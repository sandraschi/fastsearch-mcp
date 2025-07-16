import React, { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { 
  MagnifyingGlassIcon,
  GlobeAltIcon,
  DocumentIcon,
  PhotoIcon,
  VideoCameraIcon,
  AcademicCapIcon,
  LinkIcon,
  ClockIcon,
  BookmarkIcon,
  ShareIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';

const AISearchPage = () => {
  const [query, setQuery] = useState('');
  const [searchType, setSearchType] = useState('general');
  const [results, setResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [factCheck, setFactCheck] = useState(null);
  const [researchMode, setResearchMode] = useState(false);
  const inputRef = useRef(null);

  const searchTypes = [
    { id: 'general', name: 'General Search', icon: MagnifyingGlassIcon, description: 'Comprehensive web search' },
    { id: 'academic', name: 'Academic Research', icon: AcademicCapIcon, description: 'Scholarly articles and papers' },
    { id: 'news', name: 'Latest News', icon: GlobeAltIcon, description: 'Current news and trends' },
    { id: 'images', name: 'Visual Search', icon: PhotoIcon, description: 'Images and visual content' },
    { id: 'videos', name: 'Video Content', icon: VideoCameraIcon, description: 'Video tutorials and content' },
    { id: 'documents', name: 'Documents', icon: DocumentIcon, description: 'PDFs and documents' }
  ];

  const handleSearch = async () => {
    if (!query.trim()) return;

    setIsSearching(true);
    setResults([]);
    setFactCheck(null);

    try {
      // Simulate AI-powered search results
      await new Promise(resolve => setTimeout(resolve, 2000));

      const mockResults = [
        {
          id: 1,
          title: 'Understanding AI Video Generation with Google Veo',
          url: 'https://ai.google.dev/models/veo',
          snippet: 'Veo is our most capable video generation model to date. It can create high-quality videos in a wide range of cinematic and visual styles.',
          source: 'Google AI',
          type: 'official',
          relevanceScore: 0.95,
          timestamp: '2024-12-01',
          verified: true
        },
        {
          id: 2,
          title: 'AI Image Generation Best Practices',
          url: 'https://example.com/ai-image-best-practices',
          snippet: 'Learn the most effective techniques for generating high-quality images using AI models like Imagen and DALL-E.',
          source: 'AI Research Blog',
          type: 'article',
          relevanceScore: 0.88,
          timestamp: '2024-11-28',
          verified: false
        },
        {
          id: 3,
          title: 'The Future of AI Content Creation',
          url: 'https://example.com/future-ai-content',
          snippet: 'Exploring how artificial intelligence is revolutionizing content creation across video, image, music, and text generation.',
          source: 'Tech Review',
          type: 'analysis',
          relevanceScore: 0.82,
          timestamp: '2024-11-25',
          verified: true
        }
      ];

      setResults(mockResults);

      // Mock fact-check result
      if (query.toLowerCase().includes('fact') || query.toLowerCase().includes('true')) {
        setFactCheck({
          claim: query,
          status: 'verified',
          confidence: 0.92,
          sources: ['Reuters', 'AP News', 'BBC'],
          summary: 'This claim has been verified by multiple authoritative sources.'
        });
      }

    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setIsSearching(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const generateResearchReport = async () => {
    setResearchMode(true);
    // Simulate research report generation
    await new Promise(resolve => setTimeout(resolve, 3000));
    setResearchMode(false);
    alert('Research report generated! Check the Gallery tab for your comprehensive research document.');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-indigo-800 text-white">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <div className="flex items-center justify-center mb-4">
            <MagnifyingGlassIcon className="w-12 h-12 text-blue-400 mr-4" />
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
              AI-Powered Research
            </h1>
          </div>
          <p className="text-xl text-gray-300 max-w-2xl mx-auto">
            Intelligent search with real-time fact-checking and comprehensive research capabilities
          </p>
        </motion.div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Search Panel */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="lg:col-span-2 space-y-6"
          >
            {/* Search Input */}
            <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10">
              <div className="flex space-x-4 mb-4">
                <input
                  ref={inputRef}
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="What would you like to research today?"
                  className="flex-1 bg-gray-700/50 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={isSearching}
                />
                <button
                  onClick={handleSearch}
                  disabled={!query.trim() || isSearching}
                  className={`px-6 py-3 rounded-lg font-semibold transition-all ${
                    !query.trim() || isSearching
                      ? 'bg-gray-600 cursor-not-allowed'
                      : 'bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700'
                  }`}
                >
                  {isSearching ? (
                    <ClockIcon className="w-5 h-5 animate-spin" />
                  ) : (
                    <MagnifyingGlassIcon className="w-5 h-5" />
                  )}
                </button>
              </div>

              {/* Search Type Selector */}
              <div className="grid grid-cols-3 gap-2">
                {searchTypes.map((type) => {
                  const IconComponent = type.icon;
                  return (
                    <button
                      key={type.id}
                      onClick={() => setSearchType(type.id)}
                      className={`p-3 rounded-lg border-2 transition-all ${
                        searchType === type.id
                          ? 'border-blue-500 bg-blue-500/20'
                          : 'border-gray-600 bg-gray-700/30 hover:border-gray-500'
                      }`}
                    >
                      <div className="flex items-center space-x-2">
                        <IconComponent className="w-4 h-4" />
                        <span className="text-xs font-medium">{type.name}</span>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Fact Check Results */}
            {factCheck && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10"
              >
                <div className="flex items-center space-x-3 mb-4">
                  {factCheck.status === 'verified' ? (
                    <CheckCircleIcon className="w-6 h-6 text-green-400" />
                  ) : (
                    <ExclamationTriangleIcon className="w-6 h-6 text-yellow-400" />
                  )}
                  <h3 className="text-lg font-semibold">Fact Check Result</h3>
                  <span className={`px-2 py-1 rounded text-xs ${
                    factCheck.status === 'verified' ? 'bg-green-500/20 text-green-300' : 'bg-yellow-500/20 text-yellow-300'
                  }`}>
                    {Math.round(factCheck.confidence * 100)}% confidence
                  </span>
                </div>
                <p className="text-gray-300 mb-3">{factCheck.summary}</p>
                <div className="flex items-center space-x-2 text-sm text-gray-400">
                  <span>Sources:</span>
                  {factCheck.sources.map((source, index) => (
                    <span key={index} className="bg-gray-700 px-2 py-1 rounded">{source}</span>
                  ))}
                </div>
              </motion.div>
            )}

            {/* Search Results */}
            {results.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-4"
              >
                <div className="flex items-center justify-between">
                  <h3 className="text-xl font-semibold">Search Results</h3>
                  <button
                    onClick={generateResearchReport}
                    disabled={researchMode}
                    className={`px-4 py-2 rounded-lg text-sm transition-all ${
                      researchMode
                        ? 'bg-gray-600 cursor-not-allowed'
                        : 'bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700'
                    }`}
                  >
                    {researchMode ? 'Generating...' : 'Generate Research Report'}
                  </button>
                </div>

                {results.map((result) => (
                  <div key={result.id} className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <h4 className="text-lg font-medium text-blue-300 hover:text-blue-200 cursor-pointer">
                            {result.title}
                          </h4>
                          {result.verified && (
                            <CheckCircleIcon className="w-4 h-4 text-green-400" />
                          )}
                        </div>
                        <p className="text-gray-300 mb-2">{result.snippet}</p>
                        <div className="flex items-center space-x-4 text-sm text-gray-400">
                          <span className="flex items-center space-x-1">
                            <GlobeAltIcon className="w-4 h-4" />
                            <span>{result.source}</span>
                          </span>
                          <span>{result.timestamp}</span>
                          <span className="bg-blue-500/20 text-blue-300 px-2 py-1 rounded">
                            {Math.round(result.relevanceScore * 100)}% relevant
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2 ml-4">
                        <button className="p-2 bg-gray-700 rounded-lg hover:bg-gray-600 transition-colors">
                          <BookmarkIcon className="w-4 h-4" />
                        </button>
                        <button className="p-2 bg-gray-700 rounded-lg hover:bg-gray-600 transition-colors">
                          <ShareIcon className="w-4 h-4" />
                        </button>
                        <button className="p-2 bg-gray-700 rounded-lg hover:bg-gray-600 transition-colors">
                          <LinkIcon className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </motion.div>
            )}
          </motion.div>

          {/* Sidebar */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="space-y-6"
          >
            {/* Search Tips */}
            <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10">
              <h3 className="text-lg font-semibold mb-4">🔍 Search Tips</h3>
              <div className="space-y-3 text-sm text-gray-300">
                <div className="flex items-start space-x-2">
                  <span className="text-blue-400">•</span>
                  <span>Use quotes for exact phrases: "AI video generation"</span>
                </div>
                <div className="flex items-start space-x-2">
                  <span className="text-blue-400">•</span>
                  <span>Add "fact check" to verify claims</span>
                </div>
                <div className="flex items-start space-x-2">
                  <span className="text-blue-400">•</span>
                  <span>Include dates for recent information: "2024"</span>
                </div>
                <div className="flex items-start space-x-2">
                  <span className="text-blue-400">•</span>
                  <span>Use research mode for comprehensive reports</span>
                </div>
              </div>
            </div>

            {/* Recent Searches */}
            <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10">
              <h3 className="text-lg font-semibold mb-4">Recent Searches</h3>
              <div className="space-y-2">
                {['AI video trends 2024', 'Best image generation techniques', 'Music composition AI'].map((search, index) => (
                  <button
                    key={index}
                    onClick={() => setQuery(search)}
                    className="w-full text-left p-2 bg-gray-700/30 rounded-lg hover:bg-gray-600/30 transition-colors text-sm"
                  >
                    {search}
                  </button>
                ))}
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10">
              <h3 className="text-lg font-semibold mb-4">Quick Research</h3>
              <div className="space-y-2">
                <button className="w-full p-3 bg-gradient-to-r from-blue-600 to-cyan-600 rounded-lg hover:from-blue-700 hover:to-cyan-700 transition-all">
                  Content Trends Analysis
                </button>
                <button className="w-full p-3 bg-gradient-to-r from-purple-600 to-pink-600 rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all">
                  Competitor Research
                </button>
                <button className="w-full p-3 bg-gradient-to-r from-green-600 to-emerald-600 rounded-lg hover:from-green-700 hover:to-emerald-700 transition-all">
                  Market Insights
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default AISearchPage;