import React, { useState, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  Card,
  CardContent,
  CardMedia,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Slider,
  Chip,
  Alert,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Tooltip,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  Download,
  Share,
  Refresh,
  Info,
  VideoCall,
  Image as ImageIcon,
  Settings,
  History,
  Favorite,
  FavoriteBorder,
  Delete,
  Edit
} from '@mui/icons-material';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:4700';

// Video style presets
const VIDEO_STYLES = [
  { id: 'cinematic', name: 'Cinematic', description: 'Professional movie-like quality' },
  { id: 'anime', name: 'Anime', description: 'Japanese animation style' },
  { id: 'pixar', name: 'Pixar', description: '3D animated cartoon style' },
  { id: 'realistic', name: 'Realistic', description: 'Photorealistic footage' },
  { id: 'wes_anderson', name: 'Wes Anderson', description: 'Symmetrical, vintage aesthetic' },
  { id: 'claymation', name: 'Claymation', description: 'Stop-motion clay animation' },
  { id: 'advertisement', name: 'Advertisement', description: 'Commercial/marketing style' },
  { id: 'music_video', name: 'Music Video', description: 'Dynamic, rhythmic visuals' },
  { id: 'documentary', name: 'Documentary', description: 'Natural, observational style' }
];

// Duration presets
const DURATION_PRESETS = [
  { value: 5, label: '5 seconds' },
  { value: 10, label: '10 seconds' },
  { value: 15, label: '15 seconds' },
  { value: 30, label: '30 seconds' },
  { value: 60, label: '1 minute' }
];

// Video generation history component
const VideoHistory = ({ videos, onSelectVideo, onDeleteVideo }) => {
  return (
    <List>
      {videos.length === 0 ? (
        <ListItem>
          <ListItemText 
            primary="No videos generated yet"
            secondary="Generate your first video to see it here"
          />
        </ListItem>
      ) : (
        videos.map((video, index) => (
          <ListItem key={index} button onClick={() => onSelectVideo(video)}>
            <ListItemText
              primary={video.prompt}
              secondary={`${video.duration}s • ${video.style} • ${new Date(video.created_at).toLocaleDateString()}`}
            />
            <ListItemSecondaryAction>
              <IconButton edge="end" onClick={() => onDeleteVideo(index)}>
                <Delete />
              </IconButton>
            </ListItemSecondaryAction>
          </ListItem>
        ))
      )}
    </List>
  );
};

// Main Video Generator component
const VideoGenerator = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [prompt, setPrompt] = useState('');
  const [style, setStyle] = useState('cinematic');
  const [duration, setDuration] = useState(5);
  const [aspectRatio, setAspectRatio] = useState('16:9');
  const [temperature, setTemperature] = useState(0.7);
  const [seed, setSeed] = useState('');
  const [negativePrompt, setNegativePrompt] = useState('');
  const [referenceImage, setReferenceImage] = useState(null);
  
  const [generating, setGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  const [generatedVideo, setGeneratedVideo] = useState(null);
  const [videoHistory, setVideoHistory] = useState([]);
  const [previewDialog, setPreviewDialog] = useState(false);
  
  const fileInputRef = useRef(null);
  const videoRef = useRef(null);

  const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return { Authorization: `Bearer ${token}` };
  };

  const handleImageUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      if (file.size > 10 * 1024 * 1024) { // 10MB limit
        setError('Image file size must be less than 10MB');
        return;
      }
      
      const reader = new FileReader();
      reader.onload = (e) => {
        setReferenceImage({
          file: file,
          preview: e.target.result
        });
      };
      reader.readAsDataURL(file);
    }
  };

  const generateVideo = async () => {
    if (!prompt.trim()) {
      setError('Please enter a video description');
      return;
    }

    setGenerating(true);
    setError('');
    setProgress(0);

    // Simulate progress
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return 90;
        }
        return prev + Math.random() * 10;
      });
    }, 1000);

    try {
      const formData = new FormData();
      formData.append('prompt', prompt);
      formData.append('style', style);
      formData.append('duration', duration);
      formData.append('aspect_ratio', aspectRatio);
      formData.append('temperature', temperature);
      
      if (seed) formData.append('seed', seed);
      if (negativePrompt) formData.append('negative_prompt', negativePrompt);
      if (referenceImage) formData.append('reference_image', referenceImage.file);

      const response = await axios.post(
        `${API_BASE_URL}/api/v1/video/generate`,
        formData,
        {
          headers: {
            ...getAuthHeaders(),
            'Content-Type': 'multipart/form-data'
          }
        }
      );

      clearInterval(progressInterval);
      setProgress(100);

      const videoData = {
        id: Date.now(),
        prompt,
        style,
        duration,
        aspect_ratio: aspectRatio,
        video_url: response.data.video_url,
        created_at: new Date().toISOString(),
        status: 'completed'
      };

      setGeneratedVideo(videoData);
      setVideoHistory(prev => [videoData, ...prev]);
      setSuccess('Video generated successfully!');

    } catch (error) {
      clearInterval(progressInterval);
      console.error('Video generation error:', error);
      setError(error.response?.data?.detail || 'Failed to generate video. Please try again.');
    } finally {
      setGenerating(false);
      setTimeout(() => setProgress(0), 2000);
    }
  };

  const downloadVideo = async () => {
    if (!generatedVideo?.video_url) return;
    
    try {
      const response = await fetch(generatedVideo.video_url);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `veogen-video-${generatedVideo.id}.mp4`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      setError('Failed to download video');
    }
  };

  const shareVideo = async () => {
    if (!generatedVideo?.video_url) return;
    
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'VeoGen AI Video',
          text: `Check out this AI-generated video: "${prompt}"`,
          url: generatedVideo.video_url
        });
      } catch (error) {
        // User cancelled sharing
      }
    } else {
      // Fallback to copying URL
      navigator.clipboard.writeText(generatedVideo.video_url);
      setSuccess('Video URL copied to clipboard!');
    }
  };

  const TabPanel = ({ children, value, index, ...other }) => (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`video-tabpanel-${index}`}
      aria-labelledby={`video-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        🎬 Video Generator
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" sx={{ mb: 3 }}>
        Generate stunning videos using AI with Veo 3. Describe what you want to see and let AI bring it to life.
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>{success}</Alert>}

      <Grid container spacing={3}>
        {/* Main Generation Panel */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)} sx={{ mb: 3 }}>
              <Tab label="Generate" icon={<VideoCall />} />
              <Tab label="Advanced" icon={<Settings />} />
              <Tab label="History" icon={<History />} />
            </Tabs>

            <TabPanel value={activeTab} index={0}>
              {/* Basic Generation Controls */}
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Video Description"
                    placeholder="Describe the video you want to generate... (e.g., 'A serene sunset over a mountain lake with birds flying')"
                    multiline
                    rows={4}
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    disabled={generating}
                  />
                </Grid>

                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Style</InputLabel>
                    <Select value={style} onChange={(e) => setStyle(e.target.value)} disabled={generating}>
                      {VIDEO_STYLES.map((styleOption) => (
                        <MenuItem key={styleOption.id} value={styleOption.id}>
                          <Box>
                            <Typography variant="body1">{styleOption.name}</Typography>
                            <Typography variant="caption" color="text.secondary">
                              {styleOption.description}
                            </Typography>
                          </Box>
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>

                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Duration</InputLabel>
                    <Select value={duration} onChange={(e) => setDuration(e.target.value)} disabled={generating}>
                      {DURATION_PRESETS.map((preset) => (
                        <MenuItem key={preset.value} value={preset.value}>
                          {preset.label}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>

                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Aspect Ratio</InputLabel>
                    <Select value={aspectRatio} onChange={(e) => setAspectRatio(e.target.value)} disabled={generating}>
                      <MenuItem value="16:9">16:9 (Widescreen)</MenuItem>
                      <MenuItem value="9:16">9:16 (Vertical)</MenuItem>
                      <MenuItem value="1:1">1:1 (Square)</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>

                <Grid item xs={12} sm={6}>
                  <Typography gutterBottom>Creativity Level</Typography>
                  <Slider
                    value={temperature}
                    onChange={(e, newValue) => setTemperature(newValue)}
                    min={0}
                    max={1}
                    step={0.1}
                    marks={[
                      { value: 0, label: 'Conservative' },
                      { value: 0.5, label: 'Balanced' },
                      { value: 1, label: 'Creative' }
                    ]}
                    disabled={generating}
                  />
                </Grid>

                <Grid item xs={12}>
                  <Button
                    variant="contained"
                    size="large"
                    onClick={generateVideo}
                    disabled={generating || !prompt.trim()}
                    startIcon={generating ? <Stop /> : <PlayArrow />}
                    fullWidth
                  >
                    {generating ? 'Generating Video...' : 'Generate Video'}
                  </Button>
                  
                  {generating && (
                    <Box sx={{ mt: 2 }}>
                      <LinearProgress variant="determinate" value={progress} />
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                        {progress < 30 ? 'Analyzing prompt...' :
                         progress < 60 ? 'Generating frames...' :
                         progress < 90 ? 'Rendering video...' : 'Finalizing...'}
                      </Typography>
                    </Box>
                  )}
                </Grid>
              </Grid>
            </TabPanel>

            <TabPanel value={activeTab} index={1}>
              {/* Advanced Controls */}
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Negative Prompt (Optional)"
                    placeholder="What you don't want to see in the video..."
                    multiline
                    rows={2}
                    value={negativePrompt}
                    onChange={(e) => setNegativePrompt(e.target.value)}
                    disabled={generating}
                  />
                </Grid>

                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Seed (Optional)"
                    placeholder="Random seed for reproducible results"
                    value={seed}
                    onChange={(e) => setSeed(e.target.value)}
                    disabled={generating}
                  />
                </Grid>

                <Grid item xs={12}>
                  <Typography variant="h6" gutterBottom>Reference Image (Optional)</Typography>
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleImageUpload}
                    accept="image/*"
                    style={{ display: 'none' }}
                  />
                  <Button
                    variant="outlined"
                    onClick={() => fileInputRef.current?.click()}
                    startIcon={<ImageIcon />}
                    disabled={generating}
                  >
                    Upload Reference Image
                  </Button>
                  
                  {referenceImage && (
                    <Box sx={{ mt: 2 }}>
                      <img
                        src={referenceImage.preview}
                        alt="Reference"
                        style={{ maxWidth: 200, maxHeight: 200, objectFit: 'cover' }}
                      />
                      <IconButton onClick={() => setReferenceImage(null)}>
                        <Delete />
                      </IconButton>
                    </Box>
                  )}
                </Grid>
              </Grid>
            </TabPanel>

            <TabPanel value={activeTab} index={2}>
              <VideoHistory
                videos={videoHistory}
                onSelectVideo={setGeneratedVideo}
                onDeleteVideo={(index) => {
                  setVideoHistory(prev => prev.filter((_, i) => i !== index));
                }}
              />
            </TabPanel>
          </Paper>
        </Grid>

        {/* Video Preview Panel */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Generated Video
            </Typography>
            
            {generatedVideo ? (
              <Box>
                <video
                  ref={videoRef}
                  width="100%"
                  controls
                  poster="/placeholder-video.png"
                  style={{ borderRadius: 8, marginBottom: 16 }}
                >
                  <source src={generatedVideo.video_url} type="video/mp4" />
                  Your browser does not support the video tag.
                </video>
                
                <Box sx={{ mb: 2 }}>
                  <Chip label={generatedVideo.style} size="small" sx={{ mr: 1 }} />
                  <Chip label={`${generatedVideo.duration}s`} size="small" />
                </Box>
                
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  "{generatedVideo.prompt}"
                </Typography>
                
                <Grid container spacing={1}>
                  <Grid item xs={12}>
                    <Button
                      variant="contained"
                      startIcon={<Download />}
                      onClick={downloadVideo}
                      fullWidth
                    >
                      Download
                    </Button>
                  </Grid>
                  <Grid item xs={6}>
                    <Button
                      variant="outlined"
                      startIcon={<Share />}
                      onClick={shareVideo}
                      fullWidth
                    >
                      Share
                    </Button>
                  </Grid>
                  <Grid item xs={6}>
                    <Button
                      variant="outlined"
                      startIcon={<Refresh />}
                      onClick={() => {
                        // Regenerate with same settings
                        generateVideo();
                      }}
                      fullWidth
                    >
                      Retry
                    </Button>
                  </Grid>
                </Grid>
              </Box>
            ) : (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <VideoCall sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                <Typography variant="body1" color="text.secondary">
                  Generate a video to see preview here
                </Typography>
              </Box>
            )}
          </Paper>

          {/* Quick Tips */}
          <Paper sx={{ p: 2, mt: 2 }}>
            <Typography variant="h6" gutterBottom>
              💡 Tips for Better Videos
            </Typography>
            <List dense>
              <ListItem>
                <ListItemText primary="Be specific and descriptive in your prompts" />
              </ListItem>
              <ListItem>
                <ListItemText primary="Include lighting, mood, and camera angles" />
              </ListItem>
              <ListItem>
                <ListItemText primary="Try different styles for various aesthetics" />
              </ListItem>
              <ListItem>
                <ListItemText primary="Use reference images for better control" />
              </ListItem>
            </List>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default VideoGenerator;
