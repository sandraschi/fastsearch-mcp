import React, { useState, useRef, useEffect } from 'react';
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
  Slider,
  Chip,
  Alert,
  IconButton,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  ListItemAvatar,
  Avatar,
  Tabs,
  Tab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  LinearProgress,
  Tooltip
} from '@mui/material';
import {
  MusicNote,
  PlayArrow,
  Pause,
  Stop,
  Download,
  Share,
  Refresh,
  VolumeUp,
  Favorite,
  FavoriteBorder,
  Delete,
  Loop,
  Shuffle,
  QueueMusic,
  Album,
  AudioFile,
  Settings,
  History,
  Equalizer
} from '@mui/icons-material';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:4700';

// Music genres and styles
const MUSIC_GENRES = [
  { id: 'electronic', name: 'Electronic', description: 'Synthesized and digital sounds' },
  { id: 'classical', name: 'Classical', description: 'Orchestral and traditional instruments' },
  { id: 'rock', name: 'Rock', description: 'Guitar-driven energetic music' },
  { id: 'jazz', name: 'Jazz', description: 'Improvised and swing rhythms' },
  { id: 'ambient', name: 'Ambient', description: 'Atmospheric and ethereal' },
  { id: 'pop', name: 'Pop', description: 'Catchy and mainstream' },
  { id: 'hip_hop', name: 'Hip Hop', description: 'Rhythmic and beat-focused' },
  { id: 'folk', name: 'Folk', description: 'Acoustic and traditional' },
  { id: 'cinematic', name: 'Cinematic', description: 'Movie soundtrack style' },
  { id: 'world', name: 'World', description: 'International and cultural' }
];

const MOODS = [
  { id: 'uplifting', name: 'Uplifting', emoji: '😊' },
  { id: 'relaxing', name: 'Relaxing', emoji: '😌' },
  { id: 'energetic', name: 'Energetic', emoji: '⚡' },
  { id: 'melancholic', name: 'Melancholic', emoji: '😔' },
  { id: 'mysterious', name: 'Mysterious', emoji: '🔮' },
  { id: 'romantic', name: 'Romantic', emoji: '💕' },
  { id: 'dramatic', name: 'Dramatic', emoji: '🎭' },
  { id: 'peaceful', name: 'Peaceful', emoji: '☮️' }
];

const DURATIONS = [
  { value: 15, label: '15 seconds' },
  { value: 30, label: '30 seconds' },
  { value: 60, label: '1 minute' },
  { value: 120, label: '2 minutes' },
  { value: 180, label: '3 minutes' }
];

// Audio player component
const AudioPlayer = ({ track, onPlay, onPause, isPlaying }) => {
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(0.8);
  const [isLooping, setIsLooping] = useState(false);
  const audioRef = useRef(null);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const updateTime = () => setCurrentTime(audio.currentTime);
    const updateDuration = () => setDuration(audio.duration);

    audio.addEventListener('timeupdate', updateTime);
    audio.addEventListener('loadedmetadata', updateDuration);
    audio.addEventListener('ended', () => onPause());

    return () => {
      audio.removeEventListener('timeupdate', updateTime);
      audio.removeEventListener('loadedmetadata', updateDuration);
      audio.removeEventListener('ended', () => onPause());
    };
  }, [track, onPause]);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    if (isPlaying) {
      audio.play();
    } else {
      audio.pause();
    }
  }, [isPlaying]);

  useEffect(() => {
    const audio = audioRef.current;
    if (audio) {
      audio.volume = volume;
    }
  }, [volume]);

  useEffect(() => {
    const audio = audioRef.current;
    if (audio) {
      audio.loop = isLooping;
    }
  }, [isLooping]);

  const handleSeek = (event, newValue) => {
    const audio = audioRef.current;
    if (audio) {
      audio.currentTime = newValue;
      setCurrentTime(newValue);
    }
  };

  const formatTime = (time) => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  if (!track) return null;

  return (
    <Box>
      <audio ref={audioRef} src={track.url} preload="metadata" />
      
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <IconButton onClick={isPlaying ? onPause : onPlay} size="large">
          {isPlaying ? <Pause /> : <PlayArrow />}
        </IconButton>
        
        <Box sx={{ flex: 1, mx: 2 }}>
          <Slider
            value={currentTime}
            max={duration || 100}
            onChange={handleSeek}
            size="small"
          />
          <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
            <Typography variant="caption">{formatTime(currentTime)}</Typography>
            <Typography variant="caption">{formatTime(duration)}</Typography>
          </Box>
        </Box>
        
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <IconButton onClick={() => setIsLooping(!isLooping)} color={isLooping ? 'primary' : 'default'}>
            <Loop />
          </IconButton>
          <VolumeUp />
          <Slider
            value={volume}
            onChange={(e, newValue) => setVolume(newValue)}
            min={0}
            max={1}
            step={0.1}
            sx={{ width: 100, ml: 1 }}
          />
        </Box>
      </Box>
    </Box>
  );
};

// Track list component
const TrackList = ({ tracks, currentTrack, onSelectTrack, onDeleteTrack, onToggleFavorite }) => {
  return (
    <List>
      {tracks.length === 0 ? (
        <ListItem>
          <ListItemText 
            primary="No tracks generated yet"
            secondary="Generate your first track to see it here"
          />
        </ListItem>
      ) : (
        tracks.map((track, index) => (
          <ListItem 
            key={index} 
            button 
            selected={currentTrack?.id === track.id}
            onClick={() => onSelectTrack(track)}
          >
            <ListItemAvatar>
              <Avatar sx={{ bgcolor: 'primary.main' }}>
                <MusicNote />
              </Avatar>
            </ListItemAvatar>
            <ListItemText
              primary={track.title || `Track ${index + 1}`}
              secondary={`${track.genre} • ${track.mood} • ${track.duration}s`}
            />
            <ListItemSecondaryAction>
              <IconButton onClick={() => onToggleFavorite(index)} color={track.favorite ? 'error' : 'default'}>
                {track.favorite ? <Favorite /> : <FavoriteBorder />}
              </IconButton>
              <IconButton onClick={() => onDeleteTrack(index)}>
                <Delete />
              </IconButton>
            </ListItemSecondaryAction>
          </ListItem>
        ))
      )}
    </List>
  );
};

// Main Music Generator component
const MusicGenerator = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [prompt, setPrompt] = useState('');
  const [genre, setGenre] = useState('electronic');
  const [mood, setMood] = useState('uplifting');
  const [duration, setDuration] = useState(60);
  const [tempo, setTempo] = useState(120);
  const [creativity, setCreativity] = useState(0.7);
  const [instruments, setInstruments] = useState('');
  
  const [generating, setGenerating] = useState(false);
  const [currentTrack, setCurrentTrack] = useState(null);
  const [trackHistory, setTrackHistory] = useState([]);
  const [isPlaying, setIsPlaying] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return { Authorization: `Bearer ${token}` };
  };

  const generateMusic = async () => {
    if (!prompt.trim()) {
      setError('Please describe the music you want to generate');
      return;
    }

    setGenerating(true);
    setError('');

    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/music/generate`,
        {
          prompt,
          genre,
          mood,
          duration,
          tempo,
          creativity,
          instruments: instruments || undefined
        },
        { headers: getAuthHeaders() }
      );

      const newTrack = {
        id: Date.now(),
        title: prompt.substring(0, 50),
        url: response.data.music_url,
        prompt,
        genre,
        mood,
        duration,
        tempo,
        created_at: new Date().toISOString(),
        favorite: false
      };

      setCurrentTrack(newTrack);
      setTrackHistory(prev => [newTrack, ...prev]);
      setSuccess('Music generated successfully!');

    } catch (error) {
      console.error('Music generation error:', error);
      setError(error.response?.data?.detail || 'Failed to generate music. Please try again.');
    } finally {
      setGenerating(false);
    }
  };

  const downloadTrack = async (track) => {
    if (!track?.url) return;
    
    try {
      const response = await fetch(track.url);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `${track.title.replace(/\s+/g, '_')}.mp3`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      setError('Failed to download track');
    }
  };

  const shareTrack = async (track) => {
    if (!track?.url) return;
    
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'VeoGen AI Music',
          text: `Check out this AI-generated music: "${track.title}"`,
          url: track.url
        });
      } catch (error) {
        // User cancelled sharing
      }
    } else {
      navigator.clipboard.writeText(track.url);
      setSuccess('Track URL copied to clipboard!');
    }
  };

  const toggleFavorite = (index) => {
    setTrackHistory(prev => prev.map((track, i) => 
      i === index ? { ...track, favorite: !track.favorite } : track
    ));
  };

  const deleteTrack = (index) => {
    const trackToDelete = trackHistory[index];
    if (currentTrack?.id === trackToDelete.id) {
      setCurrentTrack(null);
      setIsPlaying(false);
    }
    setTrackHistory(prev => prev.filter((_, i) => i !== index));
  };

  const TabPanel = ({ children, value, index, ...other }) => (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`music-tabpanel-${index}`}
      aria-labelledby={`music-tab-${index}`}
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
        🎵 Music Generator
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" sx={{ mb: 3 }}>
        Create original music with AI using Lyria. From ambient soundscapes to energetic beats.
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>{success}</Alert>}

      <Grid container spacing={3}>
        {/* Main Generation Panel */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)} sx={{ mb: 3 }}>
              <Tab label="Generate" icon={<MusicNote />} />
              <Tab label="Advanced" icon={<Settings />} />
              <Tab label="Library" icon={<QueueMusic />} />
            </Tabs>

            <TabPanel value={activeTab} index={0}>
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Music Description"
                    placeholder="Describe the music you want... (e.g., 'Relaxing piano melody for meditation')"
                    multiline
                    rows={4}
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    disabled={generating}
                  />
                </Grid>

                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Genre</InputLabel>
                    <Select value={genre} onChange={(e) => setGenre(e.target.value)} disabled={generating}>
                      {MUSIC_GENRES.map((g) => (
                        <MenuItem key={g.id} value={g.id}>
                          <Box>
                            <Typography variant="body1">{g.name}</Typography>
                            <Typography variant="caption" color="text.secondary">
                              {g.description}
                            </Typography>
                          </Box>
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>

                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Mood</InputLabel>
                    <Select value={mood} onChange={(e) => setMood(e.target.value)} disabled={generating}>
                      {MOODS.map((m) => (
                        <MenuItem key={m.id} value={m.id}>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <Typography sx={{ mr: 1 }}>{m.emoji}</Typography>
                            <Typography>{m.name}</Typography>
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
                      {DURATIONS.map((d) => (
                        <MenuItem key={d.value} value={d.value}>
                          {d.label}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>

                <Grid item xs={12} sm={6}>
                  <Typography gutterBottom>Tempo (BPM)</Typography>
                  <Slider
                    value={tempo}
                    onChange={(e, newValue) => setTempo(newValue)}
                    min={60}
                    max={180}
                    step={10}
                    marks={[
                      { value: 60, label: 'Slow' },
                      { value: 120, label: 'Medium' },
                      { value: 180, label: 'Fast' }
                    ]}
                    disabled={generating}
                  />
                </Grid>

                <Grid item xs={12}>
                  <Typography gutterBottom>Creativity Level</Typography>
                  <Slider
                    value={creativity}
                    onChange={(e, newValue) => setCreativity(newValue)}
                    min={0}
                    max={1}
                    step={0.1}
                    marks={[
                      { value: 0, label: 'Structured' },
                      { value: 0.5, label: 'Balanced' },
                      { value: 1, label: 'Experimental' }
                    ]}
                    disabled={generating}
                  />
                </Grid>

                <Grid item xs={12}>
                  <Button
                    variant="contained"
                    size="large"
                    onClick={generateMusic}
                    disabled={generating || !prompt.trim()}
                    startIcon={generating ? <Equalizer /> : <MusicNote />}
                    fullWidth
                  >
                    {generating ? 'Generating Music...' : 'Generate Music'}
                  </Button>
                  
                  {generating && (
                    <Box sx={{ mt: 2 }}>
                      <LinearProgress />
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 1, textAlign: 'center' }}>
                        Composing your music with AI...
                      </Typography>
                    </Box>
                  )}
                </Grid>
              </Grid>
            </TabPanel>

            <TabPanel value={activeTab} index={1}>
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Specific Instruments (Optional)"
                    placeholder="e.g., piano, guitar, violin, drums..."
                    value={instruments}
                    onChange={(e) => setInstruments(e.target.value)}
                    disabled={generating}
                  />
                </Grid>

                <Grid item xs={12}>
                  <Typography variant="h6" gutterBottom>Genre Templates</Typography>
                  <Grid container spacing={2}>
                    {MUSIC_GENRES.slice(0, 6).map((g) => (
                      <Grid item xs={6} sm={4} key={g.id}>
                        <Card 
                          sx={{ 
                            cursor: 'pointer',
                            '&:hover': { elevation: 4 }
                          }}
                          onClick={() => {
                            setGenre(g.id);
                            setPrompt(`${g.description} style music`);
                          }}
                        >
                          <CardContent sx={{ textAlign: 'center', py: 2 }}>
                            <Typography variant="h6">{g.name}</Typography>
                            <Typography variant="caption" color="text.secondary">
                              {g.description}
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                    ))}
                  </Grid>
                </Grid>
              </Grid>
            </TabPanel>

            <TabPanel value={activeTab} index={2}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">Music Library ({trackHistory.length})</Typography>
                {trackHistory.length > 0 && (
                  <Chip
                    icon={<AudioFile />}
                    label={`${trackHistory.filter(t => t.favorite).length} favorites`}
                    color="primary"
                    variant="outlined"
                  />
                )}
              </Box>
              
              <TrackList
                tracks={trackHistory}
                currentTrack={currentTrack}
                onSelectTrack={setCurrentTrack}
                onDeleteTrack={deleteTrack}
                onToggleFavorite={toggleFavorite}
              />
            </TabPanel>
          </Paper>
        </Grid>

        {/* Audio Player Panel */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Now Playing
            </Typography>
            
            {currentTrack ? (
              <Box>
                <Card sx={{ mb: 2 }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                        <Album />
                      </Avatar>
                      <Box>
                        <Typography variant="h6" noWrap>
                          {currentTrack.title}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {currentTrack.genre} • {currentTrack.mood}
                        </Typography>
                      </Box>
                    </Box>
                    
                    <AudioPlayer
                      track={currentTrack}
                      isPlaying={isPlaying}
                      onPlay={() => setIsPlaying(true)}
                      onPause={() => setIsPlaying(false)}
                    />
                    
                    <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
                      <Button
                        variant="outlined"
                        startIcon={<Download />}
                        onClick={() => downloadTrack(currentTrack)}
                        size="small"
                      >
                        Download
                      </Button>
                      <Button
                        variant="outlined"
                        startIcon={<Share />}
                        onClick={() => shareTrack(currentTrack)}
                        size="small"
                      >
                        Share
                      </Button>
                      <Button
                        variant="outlined"
                        startIcon={<Refresh />}
                        onClick={() => {
                          setPrompt(currentTrack.prompt);
                          generateMusic();
                        }}
                        size="small"
                      >
                        Remix
                      </Button>
                    </Box>
                  </CardContent>
                </Card>
              </Box>
            ) : (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <MusicNote sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                <Typography variant="body1" color="text.secondary">
                  Generate music to start playing
                </Typography>
              </Box>
            )}
          </Paper>

          {/* Music Tips */}
          <Paper sx={{ p: 2, mt: 2 }}>
            <Typography variant="h6" gutterBottom>
              🎼 Music Creation Tips
            </Typography>
            <List dense>
              <ListItem>
                <ListItemText primary="Be specific about the mood and style" />
              </ListItem>
              <ListItem>
                <ListItemText primary="Mention specific instruments for better control" />
              </ListItem>
              <ListItem>
                <ListItemText primary="Try different creativity levels for variety" />
              </ListItem>
              <ListItem>
                <ListItemText primary="Combine genres for unique sounds" />
              </ListItem>
            </List>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default MusicGenerator;
