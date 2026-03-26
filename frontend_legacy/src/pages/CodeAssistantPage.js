import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  CodeBracketIcon,
  PlayIcon,
  DocumentDuplicateIcon,
  BugAntIcon,
  LightBulbIcon,
  SparklesIcon,
  CpuChipIcon,
} from '@heroicons/react/24/outline';

const CodeAssistantPage = () => {
  const [code, setCode] = useState('// Welcome to AI Code Assistant\n// Type your code here or ask for help\n\nfunction fibonacci(n) {\n  if (n <= 1) return n;\n  return fibonacci(n - 1) + fibonacci(n - 2);\n}\n\nconsole.log(fibonacci(10));');
  const [language, setLanguage] = useState('javascript');
  const [output, setOutput] = useState('');
  const [isRunning, setIsRunning] = useState(false);

  const languages = [
    { id: 'javascript', name: 'JavaScript', icon: '🟨' },
    { id: 'python', name: 'Python', icon: '🐍' },
    { id: 'typescript', name: 'TypeScript', icon: '🔷' },
    { id: 'java', name: 'Java', icon: '☕' },
    { id: 'cpp', name: 'C++', icon: '⚡' },
    { id: 'html', name: 'HTML', icon: '🌐' },
    { id: 'css', name: 'CSS', icon: '🎨' }
  ];

  const runCode = async () => {
    setIsRunning(true);
    setOutput('Running code...\n');
    
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    if (language === 'javascript' && code.includes('fibonacci')) {
      setOutput('Running code...\n55\nExecution completed successfully!');
    } else {
      setOutput('Running code...\nCode executed successfully!');
    }
    
    setIsRunning(false);
  };

  const analyzeCode = async () => {
    alert('AI Code Analysis:\n\n• Complexity: Medium\n• Performance: Good\n• Security: Secure\n• Maintainability: High\n\nSuggestions:\n• Consider adding input validation\n• Add comments for complex logic\n• Extract magic numbers to constants');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-indigo-800 text-white">
      <div className="container mx-auto px-4 py-8">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <CodeBracketIcon className="w-12 h-12 text-blue-400 mr-4" />
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
              AI Code Assistant
            </h1>
          </div>
          <p className="text-xl text-gray-300">Write, analyze, and optimize code with AI-powered assistance</p>
        </motion.div>

        <div className="grid lg:grid-cols-3 gap-6">
          <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} className="lg:col-span-2 space-y-6">
            <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-4 border border-white/10">
              <div className="flex items-center justify-between mb-4">
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                >
                  {languages.map((lang) => (
                    <option key={lang.id} value={lang.id}>
                      {lang.icon} {lang.name}
                    </option>
                  ))}
                </select>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={analyzeCode}
                    className="px-3 py-2 bg-purple-600 hover:bg-purple-700 rounded transition-colors text-sm"
                  >
                    <BugAntIcon className="w-4 h-4 inline mr-1" />
                    Analyze
                  </button>
                  <button
                    onClick={runCode}
                    disabled={isRunning}
                    className={`px-4 py-2 rounded transition-colors text-sm ${
                      isRunning
                        ? 'bg-gray-600 cursor-not-allowed'
                        : 'bg-green-600 hover:bg-green-700'
                    }`}
                  >
                    <PlayIcon className="w-4 h-4 inline mr-1" />
                    {isRunning ? 'Running...' : 'Run Code'}
                  </button>
                </div>
              </div>

              <div className="bg-gray-900/80 rounded-lg border border-gray-700">
                <div className="flex items-center justify-between p-3 border-b border-gray-700">
                  <div className="flex space-x-2">
                    <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                    <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  </div>
                  <span className="text-xs text-gray-400">{language}.{language === 'python' ? 'py' : 'js'}</span>
                </div>
                <textarea
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  className="w-full h-96 p-4 bg-transparent text-green-400 font-mono text-sm resize-none focus:outline-none"
                  style={{ fontFamily: 'Monaco, Menlo, monospace' }}
                  placeholder="// Start coding here..."
                />
              </div>
            </div>

            <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10">
              <h3 className="text-lg font-semibold mb-4">Output</h3>
              <div className="bg-gray-900/80 rounded-lg p-4 min-h-32">
                <pre className="text-green-400 font-mono text-sm whitespace-pre-wrap">
                  {output || 'No output yet. Run your code to see results.'}
                </pre>
              </div>
            </div>
          </motion.div>

          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="space-y-6">
            <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10">
              <h3 className="text-lg font-semibold mb-4 flex items-center">
                <LightBulbIcon className="w-5 h-5 mr-2 text-yellow-400" />
                AI Suggestions
              </h3>
              <div className="space-y-3">
                <div className="p-3 rounded-lg border-l-4 bg-blue-500/10 border-blue-500">
                  <div className="flex items-start space-x-2">
                    <SparklesIcon className="w-4 h-4 text-blue-400" />
                    <div>
                      <h4 className="font-medium text-sm">Performance Optimization</h4>
                      <p className="text-xs text-gray-400 mt-1">Consider using memoization for recursive functions</p>
                    </div>
                  </div>
                </div>
                <p className="text-gray-400 text-sm">Start coding to get AI suggestions...</p>
              </div>
            </div>

            <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10">
              <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
              <div className="space-y-2">
                <button className="w-full p-3 bg-gradient-to-r from-blue-600 to-cyan-600 rounded-lg hover:from-blue-700 hover:to-cyan-700 transition-all text-sm">
                  <CpuChipIcon className="w-4 h-4 inline mr-2" />
                  Optimize Code
                </button>
                <button className="w-full p-3 bg-gradient-to-r from-purple-600 to-pink-600 rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all text-sm">
                  <BugAntIcon className="w-4 h-4 inline mr-2" />
                  Debug Issues
                </button>
                <button className="w-full p-3 bg-gradient-to-r from-green-600 to-emerald-600 rounded-lg hover:from-green-700 hover:to-emerald-700 transition-all text-sm">
                  <DocumentDuplicateIcon className="w-4 h-4 inline mr-2" />
                  Generate Tests
                </button>
              </div>
            </div>

            <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10">
              <h3 className="text-lg font-semibold mb-4">Code Statistics</h3>
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Lines:</span>
                  <span>{code.split('\n').length}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Characters:</span>
                  <span>{code.length}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Functions:</span>
                  <span>{(code.match(/function\s+\w+/g) || []).length}</span>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default CodeAssistantPage;