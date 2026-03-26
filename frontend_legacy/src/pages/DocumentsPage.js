import React, { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { 
  DocumentTextIcon,
  CloudArrowUpIcon,
  DocumentIcon,
  PlusIcon,
  FolderIcon,
  MagnifyingGlassIcon,
  EyeIcon,
  PencilIcon,
  ShareIcon,
  DocumentArrowDownIcon,
  ChartBarIcon,
  CalendarIcon,
  UserIcon,
} from '@heroicons/react/24/outline';

const DocumentsPage = () => {
  const [documents, setDocuments] = useState([
    {
      id: 1,
      name: 'Project Proposal.pdf',
      type: 'pdf',
      size: '2.4 MB',
      modified: '2024-01-15',
      tags: ['Project', 'Proposal', 'Business'],
      author: 'John Doe',
      status: 'final'
    },
    {
      id: 2,
      name: 'Meeting Notes.docx',
      type: 'docx',
      size: '156 KB',
      modified: '2024-01-14',
      tags: ['Meeting', 'Notes'],
      author: 'Jane Smith',
      status: 'draft'
    },
    {
      id: 3,
      name: 'Research Report.pdf',
      type: 'pdf',
      size: '5.1 MB',
      modified: '2024-01-13',
      tags: ['Research', 'Analysis'],
      author: 'Alex Johnson',
      status: 'review'
    }
  ]);
  
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFolder, setSelectedFolder] = useState('all');
  const [viewMode, setViewMode] = useState('grid');
  const fileInputRef = useRef(null);

  const folders = [
    { id: 'all', name: 'All Documents', count: 15 },
    { id: 'recent', name: 'Recent', count: 5 },
    { id: 'projects', name: 'Projects', count: 8 },
    { id: 'reports', name: 'Reports', count: 3 },
    { id: 'drafts', name: 'Drafts', count: 2 },
    { id: 'shared', name: 'Shared', count: 6 }
  ];

  const handleFileUpload = (event) => {
    const files = Array.from(event.target.files);
    files.forEach(file => {
      const newDoc = {
        id: Date.now() + Math.random(),
        name: file.name,
        type: file.name.split('.').pop().toLowerCase(),
        size: `${(file.size / 1024 / 1024).toFixed(1)} MB`,
        modified: new Date().toISOString().split('T')[0],
        tags: ['New'],
        author: 'You',
        status: 'draft'
      };
      setDocuments(prev => [newDoc, ...prev]);
    });
  };

  const generateSummary = async (doc) => {
    // Simulate AI document analysis
    alert(`Analyzing "${doc.name}" with AI...\n\nSummary: This document contains important information about ${doc.tags.join(', ').toLowerCase()}. Key insights and recommendations have been identified.`);
  };

  const analyzeContent = async (doc) => {
    // Simulate AI content analysis
    alert(`Deep content analysis for "${doc.name}":\n\n• Document type: ${doc.type.toUpperCase()}\n• Key themes: ${doc.tags.join(', ')}\n• Sentiment: Professional\n• Readability: High\n• Action items: 3 identified`);
  };

  const filteredDocuments = documents.filter(doc => {
    const matchesSearch = doc.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         doc.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesFolder = selectedFolder === 'all' || 
                         (selectedFolder === 'recent' && new Date(doc.modified) > new Date(Date.now() - 7*24*60*60*1000)) ||
                         (selectedFolder === 'drafts' && doc.status === 'draft') ||
                         doc.tags.some(tag => tag.toLowerCase().includes(selectedFolder));
    return matchesSearch && matchesFolder;
  });

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-indigo-900 to-purple-800 text-white">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <div className="flex items-center justify-center mb-4">
            <DocumentTextIcon className="w-12 h-12 text-indigo-400 mr-4" />
            <h1 className="text-4xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
              AI Document Manager
            </h1>
          </div>
          <p className="text-xl text-gray-300">
            Intelligent document organization, analysis, and insights
          </p>
        </motion.div>

        <div className="grid lg:grid-cols-4 gap-6">
          {/* Sidebar */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="lg:col-span-1 space-y-6"
          >
            {/* Upload Area */}
            <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10">
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".pdf,.doc,.docx,.txt,.ppt,.pptx,.xls,.xlsx"
                onChange={handleFileUpload}
                className="hidden"
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                className="w-full p-4 border-2 border-dashed border-gray-600 rounded-lg hover:border-indigo-500 transition-colors text-center"
              >
                <CloudArrowUpIcon className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                <span className="text-sm text-gray-400">Upload Documents</span>
              </button>
            </div>

            {/* Folders */}
            <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10">
              <h3 className="text-lg font-semibold mb-4">Folders</h3>
              <div className="space-y-2">
                {folders.map((folder) => (
                  <button
                    key={folder.id}
                    onClick={() => setSelectedFolder(folder.id)}
                    className={`w-full flex items-center justify-between p-3 rounded-lg transition-colors ${
                      selectedFolder === folder.id
                        ? 'bg-indigo-500/20 text-indigo-300'
                        : 'hover:bg-gray-700/50 text-gray-300'
                    }`}
                  >
                    <div className="flex items-center space-x-2">
                      <FolderIcon className="w-4 h-4" />
                      <span className="text-sm">{folder.name}</span>
                    </div>
                    <span className="text-xs bg-gray-600 px-2 py-1 rounded">{folder.count}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10">
              <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
              <div className="space-y-2">
                <button className="w-full p-3 bg-gradient-to-r from-blue-600 to-cyan-600 rounded-lg hover:from-blue-700 hover:to-cyan-700 transition-all text-sm">
                  <PlusIcon className="w-4 h-4 inline mr-2" />
                  New Document
                </button>
                <button className="w-full p-3 bg-gradient-to-r from-purple-600 to-pink-600 rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all text-sm">
                  <ChartBarIcon className="w-4 h-4 inline mr-2" />
                  Analytics Report
                </button>
                <button className="w-full p-3 bg-gradient-to-r from-green-600 to-emerald-600 rounded-lg hover:from-green-700 hover:to-emerald-700 transition-all text-sm">
                  <DocumentArrowDownIcon className="w-4 h-4 inline mr-2" />
                  Batch Export
                </button>
              </div>
            </div>
          </motion.div>

          {/* Main Content */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="lg:col-span-3 space-y-6"
          >
            {/* Search and Controls */}
            <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10">
              <div className="flex items-center space-x-4 mb-4">
                <div className="flex-1 relative">
                  <MagnifyingGlassIcon className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search documents, tags, or content..."
                    className="w-full pl-10 pr-4 py-2 bg-gray-700/50 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setViewMode('grid')}
                    className={`p-2 rounded ${viewMode === 'grid' ? 'bg-indigo-500' : 'bg-gray-600'}`}
                  >
                    <DocumentIcon className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setViewMode('list')}
                    className={`p-2 rounded ${viewMode === 'list' ? 'bg-indigo-500' : 'bg-gray-600'}`}
                  >
                    <DocumentTextIcon className="w-4 h-4" />
                  </button>
                </div>
              </div>
              
              <div className="flex items-center justify-between text-sm text-gray-400">
                <span>{filteredDocuments.length} documents found</span>
                <div className="flex items-center space-x-4">
                  <span>Sort by:</span>
                  <select className="bg-gray-700 border border-gray-600 rounded px-2 py-1 text-white">
                    <option>Recent</option>
                    <option>Name</option>
                    <option>Size</option>
                    <option>Type</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Documents Grid/List */}
            <div className={`grid gap-4 ${viewMode === 'grid' ? 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3' : 'grid-cols-1'}`}>
              {filteredDocuments.map((doc) => (
                <motion.div
                  key={doc.id}
                  layout
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10 hover:border-indigo-500/50 transition-all group"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <div className={`p-2 rounded-lg ${
                        doc.type === 'pdf' ? 'bg-red-500/20 text-red-400' :
                        doc.type === 'docx' ? 'bg-blue-500/20 text-blue-400' :
                        doc.type === 'txt' ? 'bg-gray-500/20 text-gray-400' :
                        'bg-green-500/20 text-green-400'
                      }`}>
                        <DocumentIcon className="w-5 h-5" />
                      </div>
                      <div>
                        <h4 className="font-medium text-white group-hover:text-indigo-300 transition-colors">
                          {doc.name}
                        </h4>
                        <div className="flex items-center space-x-2 text-xs text-gray-400">
                          <span>{doc.size}</span>
                          <span>•</span>
                          <span>{doc.modified}</span>
                        </div>
                      </div>
                    </div>
                    <div className={`px-2 py-1 rounded text-xs ${
                      doc.status === 'final' ? 'bg-green-500/20 text-green-400' :
                      doc.status === 'draft' ? 'bg-yellow-500/20 text-yellow-400' :
                      'bg-blue-500/20 text-blue-400'
                    }`}>
                      {doc.status}
                    </div>
                  </div>

                  <div className="flex items-center space-x-1 mb-4">
                    {doc.tags.map((tag, index) => (
                      <span key={index} className="px-2 py-1 bg-gray-700/50 rounded text-xs text-gray-300">
                        {tag}
                      </span>
                    ))}
                  </div>

                  <div className="flex items-center justify-between text-xs text-gray-400 mb-4">
                    <div className="flex items-center space-x-1">
                      <UserIcon className="w-3 h-3" />
                      <span>{doc.author}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <CalendarIcon className="w-3 h-3" />
                      <span>{doc.modified}</span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <button className="p-1 bg-gray-700 rounded hover:bg-gray-600 transition-colors">
                        <EyeIcon className="w-4 h-4" />
                      </button>
                      <button className="p-1 bg-gray-700 rounded hover:bg-gray-600 transition-colors">
                        <PencilIcon className="w-4 h-4" />
                      </button>
                      <button className="p-1 bg-gray-700 rounded hover:bg-gray-600 transition-colors">
                        <ShareIcon className="w-4 h-4" />
                      </button>
                    </div>
                    <div className="flex items-center space-x-1">
                      <button
                        onClick={() => generateSummary(doc)}
                        className="px-2 py-1 bg-indigo-600 hover:bg-indigo-700 rounded text-xs transition-colors"
                      >
                        AI Summary
                      </button>
                      <button
                        onClick={() => analyzeContent(doc)}
                        className="px-2 py-1 bg-purple-600 hover:bg-purple-700 rounded text-xs transition-colors"
                      >
                        Analyze
                      </button>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>

            {filteredDocuments.length === 0 && (
              <div className="text-center py-12">
                <DocumentIcon className="w-16 h-16 text-gray-500 mx-auto mb-4" />
                <h3 className="text-xl font-medium text-gray-400 mb-2">No documents found</h3>
                <p className="text-gray-500">Try adjusting your search or upload some documents to get started.</p>
              </div>
            )}
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default DocumentsPage;