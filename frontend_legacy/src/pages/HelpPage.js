import React from 'react';

const HelpPage = () => (
  <div className="max-w-3xl mx-auto py-10 px-4">
    <h1 className="text-3xl font-bold mb-6 text-center">VeoGen Help & Documentation</h1>
    <div className="mb-10">
      <h2 className="text-2xl font-semibold mb-2 border-b pb-1">User Guide</h2>
      <ul className="list-disc pl-6 space-y-2">
        <li><strong>Getting Started:</strong> Learn how to create, edit, and manage video, image, and music projects.</li>
        <li><strong>Navigation:</strong> Overview of Home, Generate, Movie Maker, Images, Music, Gallery, Jobs, and Settings tabs.</li>
        <li><strong>Video Generation:</strong> How to create videos using Google Veo 3 with text prompts and visual styles.</li>
        <li><strong>Image Generation:</strong> How to create images using Google Imagen with various artistic styles.</li>
        <li><strong>Music Generation:</strong> How to compose music using Google Lyria with different genres and moods.</li>
        <li><strong>Movie Maker:</strong> How to create multi-scene movies with frame-to-frame continuity.</li>
        <li><strong>Preview & Download:</strong> How to preview generated content and download results.</li>
        <li><strong>Troubleshooting:</strong> Common issues and how to resolve them.</li>
      </ul>
    </div>
    <div className="mb-10">
      <h2 className="text-2xl font-semibold mb-2 border-b pb-1">Technical Guide</h2>
      <ul className="list-disc pl-6 space-y-2">
        <li><strong>System Architecture:</strong> Overview of backend, frontend, and monitoring stack.</li>
        <li><strong>API Endpoints:</strong> List of main endpoints for video, image, music, and movie generation.</li>
        <li><strong>Monitoring:</strong> Using Grafana, Prometheus, and Loki for logs and metrics.</li>
        <li><strong>Deployment:</strong> Docker Compose setup and service management.</li>
        <li><strong>Configuration:</strong> Environment variables and config files.</li>
        <li><strong>AI Models:</strong> Integration with Google Veo 3, Imagen, and Lyria services.</li>
      </ul>
    </div>
    <div className="text-center text-gray-400 text-sm">
      For complete documentation, visit the <a href="http://localhost:3301" target="_blank" rel="noopener noreferrer" className="text-blue-400 underline">full documentation site</a>.
    </div>
  </div>
);

export default HelpPage; 