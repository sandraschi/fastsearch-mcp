import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  ChartBarIcon,
  GlobeAltIcon,
  BoltIcon,
  CpuChipIcon,
  BuildingOfficeIcon,
  CurrencyDollarIcon,
  ClockIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';

const FuturePredictorPage = () => {
  const [selectedCategory, setSelectedCategory] = useState('technology');
  const [predictions, setPredictions] = useState([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const categories = [
    { id: 'technology', name: 'Technology', icon: CpuChipIcon, color: 'from-blue-500 to-cyan-500' },
    { id: 'business', name: 'Business', icon: BuildingOfficeIcon, color: 'from-green-500 to-emerald-500' },
    { id: 'economy', name: 'Economy', icon: CurrencyDollarIcon, color: 'from-yellow-500 to-orange-500' },
    { id: 'society', name: 'Society', icon: GlobeAltIcon, color: 'from-purple-500 to-pink-500' },
    { id: 'environment', name: 'Environment', icon: BoltIcon, color: 'from-green-600 to-teal-500' },
    { id: 'markets', name: 'Markets', icon: ChartBarIcon, color: 'from-red-500 to-rose-500' }
  ];



  const generatePredictions = async () => {
    setIsAnalyzing(true);
    await new Promise(resolve => setTimeout(resolve, 3000));
    setPredictions([
      {
        id: 1,
        title: 'AI Video Generation Mainstream Adoption',
        probability: 92,
        timeframe: '6-12 months',
        impact: 'High',
        description: 'AI video generation tools will become widely adopted by content creators and businesses.',
        factors: ['Improving quality', 'Decreasing costs', 'User-friendly interfaces'],
        confidence: 'Very High'
      }
    ]);
    setIsAnalyzing(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-indigo-900 to-purple-800 text-white">
      <div className="container mx-auto px-4 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <div className="flex items-center justify-center mb-4">
            <SparklesIcon className="w-12 h-12 text-indigo-400 mr-4" />
            <h1 className="text-4xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
              AI Future Predictor
            </h1>
          </div>
          <p className="text-xl text-gray-300">
            Harness AI to predict trends, analyze patterns, and forecast the future
          </p>
        </motion.div>

        <div className="grid lg:grid-cols-4 gap-6">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="lg:col-span-1 space-y-6"
          >
            <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10">
              <h3 className="text-lg font-semibold mb-4">Prediction Category</h3>
              <div className="space-y-2">
                {categories.map((category) => {
                  const IconComponent = category.icon;
                  return (
                    <button
                      key={category.id}
                      onClick={() => setSelectedCategory(category.id)}
                      className={`w-full flex items-center space-x-3 p-3 rounded-lg transition-all ${
                        selectedCategory === category.id
                          ? 'bg-indigo-500/20 border border-indigo-500'
                          : 'bg-gray-700/30 border border-gray-600 hover:border-gray-500'
                      }`}
                    >
                      <div className={`p-2 rounded bg-gradient-to-r ${category.color}`}>
                        <IconComponent className="w-4 h-4 text-white" />
                      </div>
                      <span className="text-sm font-medium">{category.name}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            <button
              onClick={generatePredictions}
              disabled={isAnalyzing}
              className={`w-full py-4 rounded-lg font-semibold transition-all ${
                isAnalyzing
                  ? 'bg-gray-600 cursor-not-allowed'
                  : 'bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700'
              }`}
            >
              {isAnalyzing ? (
                <>
                  <ClockIcon className="w-5 h-5 inline mr-2 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <SparklesIcon className="w-5 h-5 inline mr-2" />
                  Generate Predictions
                </>
              )}
            </button>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="lg:col-span-3 space-y-6"
          >
            <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-white/10">
              {predictions.length === 0 ? (
                <div className="text-center py-12">
                  <SparklesIcon className="w-16 h-16 text-gray-500 mx-auto mb-4" />
                  <h3 className="text-xl font-medium text-gray-400 mb-2">Ready for Future Analysis</h3>
                  <p className="text-gray-500">Select a category and generate predictions to see AI-powered forecasts.</p>
                </div>
              ) : (
                <div className="space-y-6">
                  {predictions.map((prediction) => (
                    <div key={prediction.id} className="bg-gray-700/30 rounded-xl p-6 border border-gray-600">
                      <h4 className="text-lg font-semibold text-white mb-2">{prediction.title}</h4>
                      <p className="text-gray-300 mb-4">{prediction.description}</p>
                      <div className="text-2xl font-bold text-green-400">{prediction.probability}%</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default FuturePredictorPage;