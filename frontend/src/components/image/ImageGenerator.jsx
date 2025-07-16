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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  ImageList,
  ImageListItem,
  ImageListItemBar,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  CircularProgress,
  Tooltip
} from '@mui/material';
import {
  Image as ImageIcon,
  Download,
  Share,
  Refresh,
  Favorite,
  FavoriteBorder,
  Delete,
  Edit,
  Fullscreen,
  Palette,
  PhotoLibrary,
  Settings,
  History,
  Upload,
  ZoomIn,
  Copy
} from '@mui/icons-material';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:4700';

// Image styles and presets
const IMAGE_STYLES = [
  { id: 'realistic', name: 'Realistic', description: 'Photorealistic images' },
  { id: 'artistic', name: 'Artistic', description: 'Artistic and creative style' },
  { id: 'digital_art', name: 'Digital Art', description: 'Digital artwork style' },
  { id: 'oil_painting', name: 'Oil Painting', description: 'Traditional oil painting' },
  { id: 'watercolor', name: 'Watercolor', description: 'Watercolor painting style' },
  { id: 'sketch', name: 'Sketch', description: 'Pencil sketch style' },
  { id: 'cartoon', name: 'Cartoon', description: 'Cartoon illustration' },
  { id: 'anime', name: 'Anime', description: 'Anime/manga style' },
  { id: 'vintage', name: 'Vintage', description: 'Vintage photograph style' },
  { id: 'minimalist', name: 'Minimalist', description: 'Clean, simple design' }
];

const ASPECT_RATIOS = [
  { id: '1:1', name: 'Square', description: '1024x1024' },
  { id: '16:9', name: 'Landscape', description: '1344x768' },
  { id: '9:16', name: 'Portrait', description: '768x1344' },
  { id: '4:3', name: 'Standard', description: '1152x896' },
  { id: '3:2', name: 'Classic', description: '1216x832' }
];

const QUALITY_LEVELS = [
  { id: 'draft', name: 'Draft', description: 'Fast generation, lower quality' },
  { id: 'standard', name: 'Standard', description: 'Balanced speed and quality' },
  { id: 'high', name: 'High', description: 'Best quality, slower generation' }
];

// Image gallery component
const ImageGallery = ({ images, onSelectImage, onDeleteImage, onToggleFavorite }) => {
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewImage, setPreviewImage] = useState(null);

  const handlePreview = (image) => {
    setPreviewImage(image);
    setPreviewOpen(true);
  };

  return (
    <>
      <ImageList cols={2} gap={8}>
        {images.map((image, index) => (
          <ImageListItem key={index}>
            <img
              src={image.url}
              alt={image.prompt}
              loading="lazy"
              style={{ cursor: 'pointer', aspectRatio: '1/1', objectFit: 'cover' }}
              onClick={() => handlePreview(image)}
            />
            <ImageListItemBar
              title={image.prompt.substring(0, 50) + '...'}
              subtitle={`${image.style} • ${image.resolution}`}
              actionIcon={
                <Box>
                  <IconButton
                    sx={{ color: 'rgba(255, 255, 255, 0.54)' }}
                    onClick={() => onToggleFavorite(index)}
                  >
                    {image.favorite ? <Favorite /> : <FavoriteBorder />}
                  </IconButton>
                  <IconButton
                    sx={{ color: 'rgba(255, 255, 255, 0.54)' }}
                    onClick={() => onDeleteImage(index)}
                  >
                    <Delete />
                  </IconButton>
                </Box>
              }
            />
          </ImageListItem>
        ))}
      </ImageList>

      {/* Preview Dialog */}
      <Dialog
        open={previewOpen}
        onClose={() => setPreviewOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">Image Preview</Typography>
            <IconButton onClick={() => setPreviewOpen(false)}>
              <Fullscreen />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          {previewImage && (
            <Box>
              <img
                src={previewImage.url}
                alt={previewImage.prompt}
                style={{ width: '100%', maxHeight: '70vh', objectFit: 'contain' }}
              />
              <Typography variant="body1" sx={{ mt: 2 }}>
                <strong>Prompt:</strong> {previewImage.prompt}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Style: {previewImage.style} • Resolution: {previewImage.resolution}
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPreviewOpen(false)}>Close</Button>
          {previewImage && (
            <>
              <Button
                startIcon={<Download />}
                onClick={() => {
                  const a = document.createElement('a');
                  a.href = previewImage.url;
                  a.download = `veogen-image-${Date.now()}.png`;
                  a.click();
                }}
              >
                Download
              </Button>
              <Button
                startIcon={<Share />}
                onClick={() => {
                  if (navigator.share) {
                    navigator.share({
                      title: 'VeoGen AI Image',
                      text: previewImage.prompt,
                      url: previewImage.url
                    });
                  } else {
                    navigator.clipboard.writeText(previewImage.url);
                  }
                }}
              >
                Share
              </Button>
            </>
          )}
        </DialogActions>
      </Dialog>
    </>
  );
};

// Main Image Generator component
const ImageGenerator = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [prompt, setPrompt] = useState('');
  const [style, setStyle] = useState('realistic');
  const [aspectRatio, setAspectRatio] = useState('1:1');
  const [quality, setQuality] = useState('standard');
  const [creativity, setCreativity] = useState(0.7);
  const [seed, setSeed] = useState('');
  const [negativePrompt, setNegativePrompt] = useState('');
  const [referenceImage, setReferenceImage] = useState(null);
  
  const [generating, setGenerating] = useState(false);
  const [generatedImages, setGeneratedImages] = useState([]);
  const [imageHistory, setImageHistory] = useState([]);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [batchCount, setBatchCount] = useState(1);
  
  const fileInputRef = useRef(null);

  const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return { Authorization: `Bearer ${token}` };
  };

  const handleImageUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      if (file.size > 10 * 1024 * 1024) {
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

  const generateImages = async () => {
    if (!prompt.trim()) {
      setError('Please enter an image description');
      return;
    }

    setGenerating(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('prompt', prompt);
      formData.append('style', style);
      formData.append('aspect_ratio', aspectRatio);
      formData.append('quality', quality);
      formData.append('creativity', creativity);
      formData.append('batch_count', batchCount);
      
      if (seed) formData.append('seed', seed);
      if (negativePrompt) formData.append('negative_prompt', negativePrompt);
      if (referenceImage) formData.append('reference_image', referenceImage.file);

      const response = await axios.post(
        `${API_BASE_URL}/api/v1/image/generate`,
        formData,
        {
          headers: {
            ...getAuthHeaders(),
            'Content-Type': 'multipart/form-data'
          }
        }
      );

      const newImages = response.data.images.map(imageData => ({
        id: Date.now() + Math.random(),
        url: imageData.url,
        prompt,
        style,
        resolution: aspectRatio,
        quality,
        created_at: new Date().toISOString(),
        favorite: false
      }));

      setGeneratedImages(newImages);
      setImageHistory(prev => [...newImages, ...prev]);
      setSuccess(`Generated ${newImages.length} image(s) successfully!`);

    } catch (error) {
      console.error('Image generation error:', error);
      setError(error.response?.data?.detail || 'Failed to generate images. Please try again.');
    } finally {
      setGenerating(false);
    }
  };

  const toggleFavorite = (index) => {
    setImageHistory(prev => prev.map((img, i) => 
      i === index ? { ...img, favorite: !img.favorite } : img
    ));
  };

  const deleteImage = (index) => {
    setImageHistory(prev => prev.filter((_, i) => i !== index));
  };

  const downloadAllImages = () => {
    generatedImages.forEach((image, index) => {
      setTimeout(() => {
        const a = document.createElement('a');
        a.href = image.url;
        a.download = `veogen-image-${index + 1}.png`;
        a.click();
      }, index * 500);
    });
  };

  const TabPanel = ({ children, value, index, ...other }) => (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`image-tabpanel-${index}`}
      aria-labelledby={`image-tab-${index}`}
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
        🎨 Image Generator
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" sx={{ mb: 3 }}>
        Create stunning AI-generated images with Imagen 3. From photorealistic to artistic styles.
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>{success}</Alert>}

      <Grid container spacing={3}>
        {/* Main Generation Panel */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)} sx={{ mb: 3 }}>
              <Tab label="Generate" icon={<ImageIcon />} />
              <Tab label="Advanced" icon={<Settings />} />
              <Tab label="Gallery" icon={<PhotoLibrary />} />
            </Tabs>

            <TabPanel value={activeTab} index={0}>
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Image Description"
                    placeholder="Describe the image you want to generate... (e.g., 'A beautiful sunset over mountains')"
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
                      {IMAGE_STYLES.map((styleOption) => (
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
                    <InputLabel>Aspect Ratio</InputLabel>
                    <Select value={aspectRatio} onChange={(e) => setAspectRatio(e.target.value)} disabled={generating}>
                      {ASPECT_RATIOS.map((ratio) => (
                        <MenuItem key={ratio.id} value={ratio.id}>
                          <Box>
                            <Typography variant="body1">{ratio.name}</Typography>
                            <Typography variant="caption" color="text.secondary">
                              {ratio.description}
                            </Typography>
                          </Box>
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>

                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Quality</InputLabel>
                    <Select value={quality} onChange={(e) => setQuality(e.target.value)} disabled={generating}>
                      {QUALITY_LEVELS.map((level) => (
                        <MenuItem key={level.id} value={level.id}>
                          <Box>
                            <Typography variant="body1">{level.name}</Typography>
                            <Typography variant="caption" color="text.secondary">
                              {level.description}
                            </Typography>
                          </Box>
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>

                <Grid item xs={12} sm={6}>
                  <Typography gutterBottom>Number of Images</Typography>
                  <Slider
                    value={batchCount}
                    onChange={(e, newValue) => setBatchCount(newValue)}
                    min={1}
                    max={4}
                    step={1}
                    marks={[
                      { value: 1, label: '1' },
                      { value: 2, label: '2' },
                      { value: 3, label: '3' },
                      { value: 4, label: '4' }
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
                      { value: 0, label: 'Precise' },
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
                    onClick={generateImages}
                    disabled={generating || !prompt.trim()}
                    startIcon={generating ? <CircularProgress size={20} /> : <Palette />}
                    fullWidth
                  >
                    {generating ? 'Generating Images...' : `Generate ${batchCount} Image${batchCount > 1 ? 's' : ''}`}
                  </Button>
                </Grid>
              </Grid>
            </TabPanel>

            <TabPanel value={activeTab} index={1}>
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Negative Prompt (Optional)"
                    placeholder="What you don't want to see in the image..."
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
                    startIcon={<Upload />}
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
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">Generated Images ({imageHistory.length})</Typography>
                {generatedImages.length > 0 && (
                  <Button
                    variant="outlined"
                    startIcon={<Download />}
                    onClick={downloadAllImages}
                  >
                    Download All
                  </Button>
                )}
              </Box>
              
              {imageHistory.length === 0 ? (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <ImageIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="body1" color="text.secondary">
                    No images generated yet. Create your first image to see it here.
                  </Typography>
                </Box>
              ) : (
                <ImageGallery
                  images={imageHistory}
                  onSelectImage={(image) => setGeneratedImages([image])}
                  onDeleteImage={deleteImage}
                  onToggleFavorite={toggleFavorite}
                />
              )}
            </TabPanel>
          </Paper>
        </Grid>

        {/* Preview Panel */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Latest Generated Images
            </Typography>
            
            {generatedImages.length > 0 ? (
              <Box>
                <ImageList cols={1} gap={8}>
                  {generatedImages.map((image, index) => (
                    <ImageListItem key={index}>
                      <img
                        src={image.url}
                        alt={image.prompt}
                        loading="lazy"
                        style={{ aspectRatio: '1/1', objectFit: 'cover' }}
                      />
                      <ImageListItemBar
                        title={`Image ${index + 1}`}
                        subtitle={image.style}
                        actionIcon={
                          <Box>
                            <IconButton
                              sx={{ color: 'rgba(255, 255, 255, 0.54)' }}
                              onClick={() => {
                                const a = document.createElement('a');
                                a.href = image.url;
                                a.download = `veogen-image-${index + 1}.png`;
                                a.click();
                              }}
                            >
                              <Download />
                            </IconButton>
                            <IconButton
                              sx={{ color: 'rgba(255, 255, 255, 0.54)' }}
                              onClick={() => {
                                navigator.clipboard.writeText(image.url);
                                setSuccess('Image URL copied to clipboard!');
                              }}
                            >
                              <Copy />
                            </IconButton>
                          </Box>
                        }
                      />
                    </ImageListItem>
                  ))}
                </ImageList>
                
                <Box sx={{ mt: 2 }}>
                  <Button
                    variant="contained"
                    startIcon={<Refresh />}
                    onClick={generateImages}
                    fullWidth
                    disabled={generating}
                  >
                    Generate More
                  </Button>
                </Box>
              </Box>
            ) : (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <ImageIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                <Typography variant="body1" color="text.secondary">
                  Generate images to see preview here
                </Typography>
              </Box>
            )}
          </Paper>

          {/* Style Examples */}
          <Paper sx={{ p: 2, mt: 2 }}>
            <Typography variant="h6" gutterBottom>
              💡 Style Examples
            </Typography>
            <List dense>
              <ListItem>
                <ListItemText
                  primary="Realistic"
                  secondary="Perfect for portraits and landscapes"
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="Digital Art"
                  secondary="Modern digital illustrations"
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="Oil Painting"
                  secondary="Classical artistic style"
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="Anime"
                  secondary="Japanese manga/anime style"
                />
              </ListItem>
            </List>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ImageGenerator;
