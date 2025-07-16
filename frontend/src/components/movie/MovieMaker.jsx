import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  Card,
  CardContent,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Alert,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineConnector,
  TimelineContent,
  TimelineDot
} from '@mui/material';
import {
  Movie,
  PlayArrow,
  Stop,
  Edit,
  Download,
  Share,
  Add,
  Remove,
  ExpandMore,
  VideoCall,
  Script,
  Timeline as TimelineIcon,
  Preview,
  Settings,
  Check,
  Error,
  Warning
} from '@mui/icons-material';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:4700';

// Movie presets
const MOVIE_PRESETS = [
  { id: 'short_film', name: 'Short Film', description: '3-5 minute artistic story', scenes: 8 },
  { id: 'commercial', name: 'Commercial', description: '30-60 second advertisement', scenes: 4 },
  { id: 'music_video', name: 'Music Video', description: '2-4 minute music visual', scenes: 12 },
  { id: 'feature', name: 'Feature Trailer', description: '2 minute movie trailer', scenes: 10 },
  { id: 'story', name: 'Story Video', description: 'Narrative-driven content', scenes: 6 }
];

// Visual styles
const VISUAL_STYLES = [
  'cinematic', 'anime', 'pixar', 'realistic', 'wes_anderson', 
  'claymation', 'advertisement', 'music_video', 'documentary'
];

// Scene status component
const SceneStatus = ({ status }) => {
  const statusConfig = {
    pending: { icon: <TimelineIcon />, color: 'default' },
    generating: { icon: <VideoCall />, color: 'primary' },
    completed: { icon: <Check />, color: 'success' },
    failed: { icon: <Error />, color: 'error' }
  };

  const config = statusConfig[status] || statusConfig.pending;

  return (
    <Chip
      icon={config.icon}
      label={status.charAt(0).toUpperCase() + status.slice(1)}
      color={config.color}
      size="small"
    />
  );
};

// Scene editor component
const SceneEditor = ({ scene, onUpdate, onDelete, index }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <Accordion expanded={expanded} onChange={() => setExpanded(!expanded)}>
      <AccordionSummary expandIcon={<ExpandMore />}>
        <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Scene {index + 1}: {scene.title || 'Untitled Scene'}
          </Typography>
          <SceneStatus status={scene.status || 'pending'} />
        </Box>
      </AccordionSummary>
      <AccordionDetails>
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Scene Title"
              value={scene.title || ''}
              onChange={(e) => onUpdate({ ...scene, title: e.target.value })}
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              fullWidth
              multiline
              rows={3}
              label="Scene Description"
              value={scene.prompt || ''}
              onChange={(e) => onUpdate({ ...scene, prompt: e.target.value })}
            />
          </Grid>
          <Grid item xs={6}>
            <TextField
              fullWidth
              type="number"
              label="Duration (seconds)"
              value={scene.duration || 8}
              onChange={(e) => onUpdate({ ...scene, duration: parseInt(e.target.value) })}
              inputProps={{ min: 5, max: 60 }}
            />
          </Grid>
          <Grid item xs={6}>
            <FormControl fullWidth>
              <InputLabel>Camera Movement</InputLabel>
              <Select
                value={scene.camera_movement || 'static'}
                onChange={(e) => onUpdate({ ...scene, camera_movement: e.target.value })}
              >
                <MenuItem value="static">Static</MenuItem>
                <MenuItem value="pan_left">Pan Left</MenuItem>
                <MenuItem value="pan_right">Pan Right</MenuItem>
                <MenuItem value="zoom_in">Zoom In</MenuItem>
                <MenuItem value="zoom_out">Zoom Out</MenuItem>
                <MenuItem value="dolly">Dolly</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12}>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button variant="outlined" onClick={() => onDelete(index)} color="error">
                Delete Scene
              </Button>
            </Box>
          </Grid>
        </Grid>
      </AccordionDetails>
    </Accordion>
  );
};

// Main Movie Maker component
const MovieMaker = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [concept, setConcept] = useState('');
  const [preset, setPreset] = useState('short_film');
  const [style, setStyle] = useState('cinematic');
  const [title, setTitle] = useState('');
  const [genre, setGenre] = useState('');
  
  const [script, setScript] = useState('');
  const [scenes, setScenes] = useState([]);
  const [generating, setGenerating] = useState(false);
  const [currentScene, setCurrentScene] = useState(0);
  const [progress, setProgress] = useState(0);
  
  const [movieProject, setMovieProject] = useState(null);
  const [projects, setProjects] = useState([]);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return { Authorization: `Bearer ${token}` };
  };

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/movie/projects`,
        { headers: getAuthHeaders() }
      );
      setProjects(response.data);
    } catch (error) {
      console.error('Failed to load projects:', error);
    }
  };

  const generateScript = async () => {
    if (!concept.trim()) {
      setError('Please provide a movie concept');
      return;
    }

    setGenerating(true);
    setError('');

    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/movie/generate-script`,
        {
          concept,
          preset,
          style,
          title,
          genre
        },
        { headers: getAuthHeaders() }
      );

      setScript(response.data.script);
      setScenes(response.data.scenes);
      setActiveStep(1);
      setSuccess('Script generated successfully!');

    } catch (error) {
      console.error('Script generation error:', error);
      setError(error.response?.data?.detail || 'Failed to generate script');
    } finally {
      setGenerating(false);
    }
  };

  const addScene = () => {
    const newScene = {
      id: Date.now(),
      title: `Scene ${scenes.length + 1}`,
      prompt: '',
      duration: 8,
      camera_movement: 'static',
      status: 'pending'
    };
    setScenes([...scenes, newScene]);
  };

  const updateScene = (index, updatedScene) => {
    const newScenes = [...scenes];
    newScenes[index] = updatedScene;
    setScenes(newScenes);
  };

  const deleteScene = (index) => {
    const newScenes = scenes.filter((_, i) => i !== index);
    setScenes(newScenes);
  };

  const generateMovie = async () => {
    if (scenes.length === 0) {
      setError('Please add at least one scene');
      return;
    }

    setGenerating(true);
    setCurrentScene(0);
    setProgress(0);
    setError('');

    try {
      const movieData = {
        title: title || 'Untitled Movie',
        concept,
        style,
        scenes: scenes.map(scene => ({
          title: scene.title,
          prompt: scene.prompt,
          duration: scene.duration,
          camera_movement: scene.camera_movement
        }))
      };

      const response = await axios.post(
        `${API_BASE_URL}/api/v1/movie/create`,
        movieData,
        { headers: getAuthHeaders() }
      );

      const projectId = response.data.project_id;
      setMovieProject({
        id: projectId,
        ...movieData,
        status: 'generating',
        created_at: new Date().toISOString()
      });

      // Poll for progress
      pollMovieProgress(projectId);

    } catch (error) {
      console.error('Movie generation error:', error);
      setError(error.response?.data?.detail || 'Failed to start movie generation');
      setGenerating(false);
    }
  };

  const pollMovieProgress = async (projectId) => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/movie/status/${projectId}`,
        { headers: getAuthHeaders() }
      );

      const { status, current_scene, total_scenes, scenes: sceneStatuses } = response.data;

      setCurrentScene(current_scene);
      setProgress((current_scene / total_scenes) * 100);

      // Update scene statuses
      const updatedScenes = scenes.map((scene, index) => ({
        ...scene,
        status: sceneStatuses[index]?.status || 'pending'
      }));
      setScenes(updatedScenes);

      if (status === 'completed') {
        setGenerating(false);
        setActiveStep(2);
        setSuccess('Movie generated successfully!');
        setMovieProject(prev => ({
          ...prev,
          status: 'completed',
          video_url: response.data.video_url
        }));
      } else if (status === 'failed') {
        setGenerating(false);
        setError('Movie generation failed');
      } else {
        // Continue polling
        setTimeout(() => pollMovieProgress(projectId), 2000);
      }

    } catch (error) {
      console.error('Progress polling error:', error);
      setGenerating(false);
      setError('Failed to check movie progress');
    }
  };

  const downloadMovie = async () => {
    if (!movieProject?.video_url) return;
    
    try {
      const response = await fetch(movieProject.video_url);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `${movieProject.title.replace(/\s+/g, '_')}.mp4`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      setError('Failed to download movie');
    }
  };

  const steps = [
    'Create Concept',
    'Edit Scenes',
    'Generate Movie'
  ];

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        🎬 Movie Maker
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" sx={{ mb: 3 }}>
        Create complete movies with multiple scenes, continuity, and professional storytelling.
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>{success}</Alert>}

      <Grid container spacing={3}>
        {/* Main Content */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Stepper activeStep={activeStep} orientation="vertical">
              {/* Step 1: Concept Creation */}
              <Step>
                <StepLabel>Create Movie Concept</StepLabel>
                <StepContent>
                  <Grid container spacing={3}>
                    <Grid item xs={12} sm={6}>
                      <TextField
                        fullWidth
                        label="Movie Title"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        placeholder="Enter your movie title"
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <TextField
                        fullWidth
                        label="Genre"
                        value={genre}
                        onChange={(e) => setGenre(e.target.value)}
                        placeholder="e.g., Drama, Comedy, Sci-Fi"
                      />
                    </Grid>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        multiline
                        rows={4}
                        label="Movie Concept"
                        value={concept}
                        onChange={(e) => setConcept(e.target.value)}
                        placeholder="Describe your movie concept, story, and key scenes..."
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <FormControl fullWidth>
                        <InputLabel>Movie Type</InputLabel>
                        <Select value={preset} onChange={(e) => setPreset(e.target.value)}>
                          {MOVIE_PRESETS.map((p) => (
                            <MenuItem key={p.id} value={p.id}>
                              <Box>
                                <Typography variant="body1">{p.name}</Typography>
                                <Typography variant="caption" color="text.secondary">
                                  {p.description}
                                </Typography>
                              </Box>
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <FormControl fullWidth>
                        <InputLabel>Visual Style</InputLabel>
                        <Select value={style} onChange={(e) => setStyle(e.target.value)}>
                          {VISUAL_STYLES.map((s) => (
                            <MenuItem key={s} value={s}>
                              {s.charAt(0).toUpperCase() + s.slice(1).replace('_', ' ')}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>
                    <Grid item xs={12}>
                      <Button
                        variant="contained"
                        onClick={generateScript}
                        disabled={generating || !concept.trim()}
                        startIcon={generating ? <Stop /> : <Script />}
                      >
                        {generating ? 'Generating Script...' : 'Generate Script & Scenes'}
                      </Button>
                    </Grid>
                  </Grid>
                </StepContent>
              </Step>

              {/* Step 2: Scene Editing */}
              <Step>
                <StepLabel>Edit Scenes</StepLabel>
                <StepContent>
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="h6" gutterBottom>
                      Generated Script
                    </Typography>
                    <Paper sx={{ p: 2, bgcolor: 'grey.50', maxHeight: 200, overflow: 'auto' }}>
                      <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                        {script || 'Script will appear here after generation...'}
                      </Typography>
                    </Paper>
                  </Box>

                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6">
                      Scenes ({scenes.length})
                    </Typography>
                    <Button
                      variant="outlined"
                      startIcon={<Add />}
                      onClick={addScene}
                    >
                      Add Scene
                    </Button>
                  </Box>

                  {scenes.map((scene, index) => (
                    <SceneEditor
                      key={scene.id || index}
                      scene={scene}
                      index={index}
                      onUpdate={(updatedScene) => updateScene(index, updatedScene)}
                      onDelete={deleteScene}
                    />
                  ))}

                  <Box sx={{ mt: 3 }}>
                    <Button
                      variant="contained"
                      onClick={generateMovie}
                      disabled={generating || scenes.length === 0}
                      startIcon={generating ? <Stop /> : <Movie />}
                    >
                      {generating ? 'Generating Movie...' : 'Generate Movie'}
                    </Button>
                  </Box>
                </StepContent>
              </Step>

              {/* Step 3: Movie Generation */}
              <Step>
                <StepLabel>Generate Movie</StepLabel>
                <StepContent>
                  {generating && (
                    <Box sx={{ mb: 3 }}>
                      <Typography variant="h6" gutterBottom>
                        Generating Movie...
                      </Typography>
                      <LinearProgress variant="determinate" value={progress} sx={{ mb: 1 }} />
                      <Typography variant="body2" color="text.secondary">
                        Scene {currentScene + 1} of {scenes.length}
                      </Typography>
                      
                      <Timeline sx={{ mt: 2 }}>
                        {scenes.map((scene, index) => (
                          <TimelineItem key={index}>
                            <TimelineSeparator>
                              <TimelineDot color={
                                scene.status === 'completed' ? 'success' :
                                scene.status === 'generating' ? 'primary' :
                                scene.status === 'failed' ? 'error' : 'grey'
                              }>
                                {scene.status === 'completed' ? <Check /> :
                                 scene.status === 'generating' ? <VideoCall /> :
                                 scene.status === 'failed' ? <Error /> : <TimelineIcon />}
                              </TimelineDot>
                              {index < scenes.length - 1 && <TimelineConnector />}
                            </TimelineSeparator>
                            <TimelineContent>
                              <Typography variant="h6" component="span">
                                {scene.title}
                              </Typography>
                              <Typography>{scene.status}</Typography>
                            </TimelineContent>
                          </TimelineItem>
                        ))}
                      </Timeline>
                    </Box>
                  )}

                  {movieProject && movieProject.status === 'completed' && (
                    <Box>
                      <Typography variant="h6" gutterBottom>
                        Movie Generated Successfully!
                      </Typography>
                      <video
                        width="100%"
                        controls
                        style={{ borderRadius: 8, marginBottom: 16 }}
                      >
                        <source src={movieProject.video_url} type="video/mp4" />
                        Your browser does not support the video tag.
                      </video>
                      
                      <Box sx={{ display: 'flex', gap: 2 }}>
                        <Button
                          variant="contained"
                          startIcon={<Download />}
                          onClick={downloadMovie}
                        >
                          Download Movie
                        </Button>
                        <Button
                          variant="outlined"
                          startIcon={<Share />}
                          onClick={() => {
                            if (navigator.share) {
                              navigator.share({
                                title: movieProject.title,
                                url: movieProject.video_url
                              });
                            } else {
                              navigator.clipboard.writeText(movieProject.video_url);
                              setSuccess('Movie URL copied to clipboard!');
                            }
                          }}
                        >
                          Share
                        </Button>
                      </Box>
                    </Box>
                  )}
                </StepContent>
              </Step>
            </Stepper>
          </Paper>
        </Grid>

        {/* Sidebar */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, mb: 2 }}>
            <Typography variant="h6" gutterBottom>
              🎭 Movie Types
            </Typography>
            <List dense>
              {MOVIE_PRESETS.map((preset) => (
                <ListItem key={preset.id}>
                  <ListItemText
                    primary={preset.name}
                    secondary={`${preset.description} (${preset.scenes} scenes)`}
                  />
                </ListItem>
              ))}
            </List>
          </Paper>

          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              💡 Movie Making Tips
            </Typography>
            <List dense>
              <ListItem>
                <ListItemText primary="Start with a clear story concept" />
              </ListItem>
              <ListItem>
                <ListItemText primary="Keep scenes between 5-15 seconds" />
              </ListItem>
              <ListItem>
                <ListItemText primary="Use consistent visual style" />
              </ListItem>
              <ListItem>
                <ListItemText primary="Plan scene transitions" />
              </ListItem>
              <ListItem>
                <ListItemText primary="Consider pacing and rhythm" />
              </ListItem>
            </List>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default MovieMaker;
