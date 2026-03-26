import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  BookOpenIcon,
  PencilIcon,
  SparklesIcon,
  GlobeAltIcon,
  UserGroupIcon,
  DocumentTextIcon,
  ArrowPathIcon,
  ShoppingCartIcon,
  LightBulbIcon,
} from '@heroicons/react/24/outline';

const BookMakerPage = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const [bookProject, setBookProject] = useState({
    title: '',
    genre: '',
    length: 'novel',
    mainCharacter: '',
    loveInterest: '',
    antagonist: '',
    contentIdeas: '',
    selectedTropes: []
  });
  
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedContent, setGeneratedContent] = useState({
    outline: '',
    firstChapter: ''
  });

  const steps = [
    { id: 1, name: 'Basic Info', icon: BookOpenIcon },
    { id: 2, name: 'World Building', icon: GlobeAltIcon },
    { id: 3, name: 'Characters', icon: UserGroupIcon },
    { id: 4, name: 'Plot Elements', icon: SparklesIcon },
    { id: 5, name: 'Generate', icon: LightBulbIcon }
  ];

  const genres = [
    'Fantasy', 'Science Fiction', 'Romance', 'Mystery', 'Thriller', 'Horror',
    'Historical Fiction', 'Contemporary Fiction', 'Young Adult'
  ];

  const popularTropes = [
    'Enemies to Lovers', 'Chosen One', 'Found Family', 'Redemption Arc',
    'Love Triangle', 'Fish Out of Water', 'Coming of Age', 'Forbidden Love'
  ];

  const generateBook = async () => {
    setIsGenerating(true);
    
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    setGeneratedContent({
      outline: `**${bookProject.title}**\n\nGenre: ${bookProject.genre}\nMain Character: ${bookProject.mainCharacter}\n\nThis AI-generated outline provides a complete story structure with character development, plot progression, and thematic elements tailored to your specifications.`,
      firstChapter: `**Chapter 1**\n\n${bookProject.mainCharacter} stood at the threshold of adventure, unaware that their life was about to change forever.\n\n[This is a sample opening that would be expanded into a full chapter with dialogue, descriptions, and character development.]`
    });
    
    setIsGenerating(false);
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Book Title</label>
              <input
                type="text"
                value={bookProject.title}
                onChange={(e) => setBookProject(prev => ({ ...prev, title: e.target.value }))}
                placeholder="Enter your book title..."
                className="w-full bg-gray-700/50 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:ring-2 focus:ring-purple-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Genre</label>
              <select
                value={bookProject.genre}
                onChange={(e) => setBookProject(prev => ({ ...prev, genre: e.target.value }))}
                className="w-full bg-gray-700/50 border border-gray-600 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-purple-500"
              >
                <option value="">Select a genre...</option>
                {genres.map((genre) => (
                  <option key={genre} value={genre}>{genre}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Content Ideas</label>
              <textarea
                value={bookProject.contentIdeas}
                onChange={(e) => setBookProject(prev => ({ ...prev, contentIdeas: e.target.value }))}
                placeholder="Describe your book concept and main themes..."
                className="w-full h-32 bg-gray-700/50 border border-gray-600 rounded-lg p-4 text-white placeholder-gray-400 focus:ring-2 focus:ring-purple-500 resize-none"
              />
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Setting & Location</label>
              <input
                type="text"
                placeholder="e.g., Victorian London, Space Station, Fantasy Kingdom..."
                className="w-full bg-gray-700/50 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:ring-2 focus:ring-purple-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Time Period</label>
              <input
                type="text"
                placeholder="e.g., Modern Day, Medieval, Future, 1920s..."
                className="w-full bg-gray-700/50 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:ring-2 focus:ring-purple-500"
              />
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Main Character</label>
              <input
                type="text"
                value={bookProject.mainCharacter}
                onChange={(e) => setBookProject(prev => ({ ...prev, mainCharacter: e.target.value }))}
                placeholder="Protagonist name and description..."
                className="w-full bg-gray-700/50 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:ring-2 focus:ring-purple-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Love Interest</label>
              <input
                type="text"
                value={bookProject.loveInterest}
                onChange={(e) => setBookProject(prev => ({ ...prev, loveInterest: e.target.value }))}
                placeholder="Romantic interest (if applicable)..."
                className="w-full bg-gray-700/50 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:ring-2 focus:ring-purple-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Antagonist</label>
              <input
                type="text"
                value={bookProject.antagonist}
                onChange={(e) => setBookProject(prev => ({ ...prev, antagonist: e.target.value }))}
                placeholder="Main villain or opposing force..."
                className="w-full bg-gray-700/50 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:ring-2 focus:ring-purple-500"
              />
            </div>
          </div>
        );

      case 4:
        return (
          <div className="space-y-6">
            <div>
              <h4 className="text-lg font-semibold mb-4">Select Story Tropes</h4>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {popularTropes.map((trope) => (
                  <button
                    key={trope}
                    onClick={() => {
                      setBookProject(prev => ({
                        ...prev,
                        selectedTropes: prev.selectedTropes.includes(trope)
                          ? prev.selectedTropes.filter(t => t !== trope)
                          : [...prev.selectedTropes, trope]
                      }));
                    }}
                    className={`p-3 rounded-lg text-sm transition-all ${
                      bookProject.selectedTropes.includes(trope)
                        ? 'bg-purple-500/30 border border-purple-500 text-purple-200'
                        : 'bg-gray-700/30 border border-gray-600 text-gray-300 hover:border-gray-500'
                    }`}
                  >
                    {trope}
                  </button>
                ))}
              </div>
            </div>
          </div>
        );

      case 5:
        return (
          <div className="space-y-6">
            <div className="text-center">
              <h4 className="text-2xl font-bold mb-4">Ready to Create Your Book!</h4>
              <p className="text-gray-300 mb-6">AI will generate your book outline and first chapter.</p>
              
              <button
                onClick={generateBook}
                disabled={isGenerating || !bookProject.title || !bookProject.genre}
                className={`px-8 py-4 rounded-lg font-semibold transition-all text-lg ${
                  isGenerating || !bookProject.title || !bookProject.genre
                    ? 'bg-gray-600 cursor-not-allowed'
                    : 'bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700'
                }`}
              >
                {isGenerating ? (
                  <>
                    <ArrowPathIcon className="w-6 h-6 inline mr-2 animate-spin" />
                    Generating Your Book...
                  </>
                ) : (
                  <>
                    <SparklesIcon className="w-6 h-6 inline mr-2" />
                    Generate Book
                  </>
                )}
              </button>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-indigo-800 text-white">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <div className="flex items-center justify-center mb-4">
            <BookOpenIcon className="w-12 h-12 text-purple-400 mr-4" />
            <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
              AI Book Maker Studio
            </h1>
          </div>
          <p className="text-xl text-gray-300">
            Create, publish, and market your book with AI-powered assistance
          </p>
        </motion.div>

        {/* Progress Steps */}
        <div className="mb-8">
          <div className="flex items-center justify-center space-x-4 max-w-2xl mx-auto">
            {steps.map((step, index) => {
              const IconComponent = step.icon;
              return (
                <div key={step.id} className="flex items-center">
                  <button
                    onClick={() => setCurrentStep(step.id)}
                    className={`flex flex-col items-center p-4 rounded-lg transition-all ${
                      currentStep === step.id
                        ? 'bg-purple-500/20 border-2 border-purple-500'
                        : 'bg-gray-700/30 border-2 border-gray-600 hover:border-gray-500'
                    }`}
                  >
                    <IconComponent className={`w-6 h-6 mb-2 ${
                      currentStep === step.id ? 'text-purple-400' : 'text-gray-400'
                    }`} />
                    <span className="text-xs font-medium">{step.name}</span>
                  </button>
                  {index < steps.length - 1 && (
                    <div className="h-0.5 w-8 bg-gray-600" />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Main Content */}
        <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-8 border border-white/10 mb-8">
          <h2 className="text-2xl font-bold mb-6">
            {steps.find(s => s.id === currentStep)?.name}
          </h2>
          {renderStepContent()}
        </div>

        {/* Navigation */}
        <div className="flex justify-between items-center mb-8">
          <button
            onClick={() => setCurrentStep(Math.max(1, currentStep - 1))}
            disabled={currentStep === 1}
            className={`px-6 py-3 rounded-lg transition-all ${
              currentStep === 1
                ? 'bg-gray-600 cursor-not-allowed'
                : 'bg-gray-700 hover:bg-gray-600'
            }`}
          >
            Previous
          </button>
          <div className="text-sm text-gray-400">
            Step {currentStep} of {steps.length}
          </div>
          <button
            onClick={() => setCurrentStep(Math.min(steps.length, currentStep + 1))}
            disabled={currentStep === steps.length}
            className={`px-6 py-3 rounded-lg transition-all ${
              currentStep === steps.length
                ? 'bg-gray-600 cursor-not-allowed'
                : 'bg-purple-600 hover:bg-purple-700'
            }`}
          >
            Next
          </button>
        </div>

        {/* Results */}
        {generatedContent.outline && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <div className="text-center mb-8">
              <h3 className="text-2xl font-bold mb-2">🎉 Your Book Has Been Created!</h3>
            </div>

            <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10">
              <div className="flex items-center space-x-3 mb-4">
                <DocumentTextIcon className="w-6 h-6 text-blue-400" />
                <h4 className="text-lg font-semibold">Book Outline</h4>
              </div>
              <div className="bg-gray-900/50 rounded-lg p-4">
                <pre className="text-sm text-gray-300 whitespace-pre-wrap">{generatedContent.outline}</pre>
              </div>
            </div>

            <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10">
              <div className="flex items-center space-x-3 mb-4">
                <PencilIcon className="w-6 h-6 text-green-400" />
                <h4 className="text-lg font-semibold">First Chapter</h4>
              </div>
              <div className="bg-gray-900/50 rounded-lg p-4">
                <div className="text-sm text-gray-300 whitespace-pre-wrap">{generatedContent.firstChapter}</div>
              </div>
            </div>

            <div className="flex flex-wrap gap-4 justify-center">
              <button className="px-6 py-3 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 rounded-lg transition-all">
                <DocumentTextIcon className="w-5 h-5 inline mr-2" />
                Download Manuscript
              </button>
              <button className="px-6 py-3 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 rounded-lg transition-all">
                <ShoppingCartIcon className="w-5 h-5 inline mr-2" />
                Publish to Amazon
              </button>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default BookMakerPage;