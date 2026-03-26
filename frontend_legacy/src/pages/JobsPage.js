import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import {
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  TrashIcon,
  EyeIcon,
  ArrowDownTrayIcon,
} from '@heroicons/react/24/outline';

const JobsPage = () => {
  const [jobs, setJobs] = useState([]);

  const { data: jobsData, isLoading, refetch } = useQuery({
    queryKey: ['jobs'],
    queryFn: async () => {
      const response = await fetch('/api/v1/video/jobs');
      if (!response.ok) throw new Error('Failed to fetch jobs');
      return response.json();
    },
    refetchInterval: 3000, // Poll every 3 seconds
  });

  useEffect(() => {
    if (jobsData) {
      setJobs(jobsData.jobs || []);
    }
  }, [jobsData]);

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
      case 'failed':
        return <XCircleIcon className="w-5 h-5 text-red-500" />;
      case 'processing':
        return <ClockIcon className="w-5 h-5 text-yellow-500 animate-pulse" />;
      default:
        return <ClockIcon className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'text-green-400 bg-green-500/10';
      case 'failed':
        return 'text-red-400 bg-red-500/10';
      case 'processing':
        return 'text-yellow-400 bg-yellow-500/10';
      default:
        return 'text-gray-400 bg-gray-500/10';
    }
  };

  const deleteJob = async (jobId) => {
    try {
      const response = await fetch(`/api/v1/video/jobs/${jobId}`, {
        method: 'DELETE',
      });
      if (response.ok) {
        refetch();
      }
    } catch (error) {
      console.error('Failed to delete job:', error);
    }
  };

  const downloadVideo = (jobId) => {
    window.open(`/api/v1/video/download/${jobId}`, '_blank');
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <h1 className="text-3xl md:text-4xl font-bold text-white mb-4">
          Video Generation Jobs
        </h1>
        <p className="text-gray-400">
          Track your video generation progress and manage completed videos
        </p>
      </motion.div>

      {jobs.length === 0 ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-12"
        >
          <ClockIcon className="w-16 h-16 text-gray-600 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-white mb-2">No jobs yet</h3>
          <p className="text-gray-400 mb-6">
            Start generating your first video to see it here
          </p>
          <a
            href="/generate"
            className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white font-semibold rounded-lg hover:shadow-lg transition-all duration-300"
          >
            Generate Video
          </a>
        </motion.div>
      ) : (
        <div className="space-y-4">
          {jobs.map((job, index) => (
            <motion.div
              key={job.job_id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-white/10"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  {getStatusIcon(job.status)}
                  <div>
                    <h3 className="text-lg font-semibold text-white">
                      Job #{job.job_id.slice(0, 8)}
                    </h3>
                    <p className="text-gray-400 text-sm">
                      Created: {new Date(job.created_at).toLocaleString()}
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-4">
                  <span
                    className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(
                      job.status
                    )}`}
                  >
                    {job.status.charAt(0).toUpperCase() + job.status.slice(1)}
                  </span>

                  <div className="flex items-center space-x-2">
                    {job.status === 'completed' && (
                      <>
                        <button
                          onClick={() => downloadVideo(job.job_id)}
                          className="p-2 text-gray-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
                          title="Download"
                        >
                          <ArrowDownTrayIcon className="w-5 h-5" />
                        </button>
                        <button
                          className="p-2 text-gray-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
                          title="Preview"
                        >
                          <EyeIcon className="w-5 h-5" />
                        </button>
                      </>
                    )}
                    <button
                      onClick={() => deleteJob(job.job_id)}
                      className="p-2 text-gray-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                      title="Delete"
                    >
                      <TrashIcon className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              </div>

              {job.status === 'processing' && (
                <div className="mt-4">
                  <div className="flex items-center justify-between text-sm text-gray-400 mb-2">
                    <span>Progress</span>
                    <span>{job.progress}%</span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${job.progress}%` }}
                      className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full"
                    />
                  </div>
                </div>
              )}

              {job.completed_at && (
                <p className="text-gray-400 text-sm mt-2">
                  Completed: {new Date(job.completed_at).toLocaleString()}
                </p>
              )}
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
};

export default JobsPage;
