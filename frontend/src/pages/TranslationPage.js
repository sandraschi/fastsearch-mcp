import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { LanguageIcon, ArrowsRightLeftIcon, SpeakerWaveIcon } from '@heroicons/react/24/outline';

const TranslationPage = () => {
  const [sourceText, setSourceText] = useState('');
  const [translatedText, setTranslatedText] = useState('');
  const [sourceLanguage, setSourceLanguage] = useState('auto');
  const [targetLanguage, setTargetLanguage] = useState('es');
  const [isTranslating, setIsTranslating] = useState(false);

  const languages = [
    { code: 'auto', name: 'Auto-detect', flag: '🌐' },
    { code: 'en', name: 'English', flag: '🇺🇸' },
    { code: 'es', name: 'Spanish', flag: '🇪🇸' },
    { code: 'fr', name: 'French', flag: '🇫🇷' },
    { code: 'de', name: 'German', flag: '🇩🇪' },
    { code: 'it', name: 'Italian', flag: '🇮🇹' },
    { code: 'pt', name: 'Portuguese', flag: '🇵🇹' },
    { code: 'zh', name: 'Chinese', flag: '🇨🇳' },
    { code: 'ja', name: 'Japanese', flag: '🇯🇵' },
    { code: 'ko', name: 'Korean', flag: '🇰🇷' }
  ];

  const handleTranslate = async () => {
    if (!sourceText.trim()) return;
    setIsTranslating(true);
    await new Promise(resolve => setTimeout(resolve, 1500));
    setTranslatedText('This is a sample translation using advanced AI technology.');
    setIsTranslating(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-indigo-900 to-purple-800 text-white">
      <div className="container mx-auto px-4 py-8">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <LanguageIcon className="w-12 h-12 text-indigo-400 mr-4" />
            <h1 className="text-4xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
              AI Universal Translator
            </h1>
          </div>
          <p className="text-xl text-gray-300">Break down language barriers with intelligent translation</p>
        </motion.div>

        <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10 mb-6">
          <div className="flex items-center justify-between mb-4">
            <select
              value={sourceLanguage}
              onChange={(e) => setSourceLanguage(e.target.value)}
              className="bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white"
            >
              {languages.map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {lang.flag} {lang.name}
                </option>
              ))}
            </select>
            
            <button className="p-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 transition-colors">
              <ArrowsRightLeftIcon className="w-5 h-5" />
            </button>
            
            <select
              value={targetLanguage}
              onChange={(e) => setTargetLanguage(e.target.value)}
              className="bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white"
            >
              {languages.filter(lang => lang.code !== 'auto').map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {lang.flag} {lang.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10">
            <h3 className="text-lg font-semibold mb-4">Source Text</h3>
            <textarea
              value={sourceText}
              onChange={(e) => setSourceText(e.target.value)}
              placeholder="Enter text to translate..."
              className="w-full h-64 bg-gray-700/50 border border-gray-600 rounded-lg p-4 text-white placeholder-gray-400 focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
            />
            <button
              onClick={handleTranslate}
              disabled={!sourceText.trim() || isTranslating}
              className={`w-full mt-4 py-3 rounded-lg font-semibold transition-all ${
                !sourceText.trim() || isTranslating
                  ? 'bg-gray-600 cursor-not-allowed'
                  : 'bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700'
              }`}
            >
              {isTranslating ? 'Translating...' : 'Translate'}
            </button>
          </div>

          <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Translation</h3>
              <button className="p-2 bg-gray-700 rounded-lg hover:bg-gray-600 transition-colors">
                <SpeakerWaveIcon className="w-4 h-4" />
              </button>
            </div>
            <div className="w-full h-64 bg-gray-700/50 border border-gray-600 rounded-lg p-4 text-white overflow-y-auto">
              {translatedText || (
                <span className="text-gray-400">Translation will appear here...</span>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TranslationPage;